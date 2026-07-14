from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_SSL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.util import dt as dt_util

from .api import EmbyApiClient, EmbyApiError, EmbyAuthError, EmbyDeviceRecord
from .cleanup import (
    async_delete_device_records,
    plan_device_cleanup,
    removable_player_keys,
)
from .const import (
    AUTO_CLEANUP_INITIAL_DELAY_SECONDS,
    AUTO_CLEANUP_INTERVAL_HOURS,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_INITIAL_RUN_COMPLETED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_API_KEY,
    CONF_SERVER_CLEANUP_ENABLED,
    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
    DOMAIN,
)
from .helpers import ACTIVE_STATES
from .models import EmbiRuntimeData

_LOGGER = logging.getLogger(__name__)
_PENDING_REGISTRY_CLEANUP = f"{DOMAIN}_pending_registry_cleanup"


def cleanup_client(hass: HomeAssistant, entry: ConfigEntry) -> EmbyApiClient:
    """Return the server-cleanup client with least-surprise key fallback."""
    cleanup_key = str(entry.options.get(CONF_SERVER_CLEANUP_API_KEY, "")).strip()
    return EmbyApiClient(
        session=async_get_clientsession(hass),
        host=entry.data[CONF_HOST],
        port=int(entry.data[CONF_PORT]),
        api_key=cleanup_key or entry.data[CONF_API_KEY],
        use_ssl=entry.data[CONF_SSL],
    )


def active_player_keys(hass: HomeAssistant, entry: ConfigEntry) -> set[str]:
    """Return exact EMBi player keys that are currently playing or paused."""
    active: set[str] = set()
    runtime = getattr(entry, "runtime_data", None)
    pyemby = getattr(runtime, "pyemby", None)
    for device_id, device in getattr(pyemby, "devices", {}).items():
        if str(getattr(device, "state", "")).casefold() in ACTIVE_STATES:
            active.add(str(device_id))

    registry = er.async_get(hass)
    for entity in registry.entities.values():
        if (
            entity.domain != "media_player"
            or entity.platform != DOMAIN
            or entity.config_entry_id != entry.entry_id
        ):
            continue
        state = hass.states.get(entity.entity_id)
        if state is not None and str(state.state).casefold() in ACTIVE_STATES:
            active.add(str(entity.unique_id))
    return active


def queue_registry_cleanup(hass: HomeAssistant, entry_id: str, player_keys: Iterable[str]) -> int:
    """Queue exact player identities for safe removal during the next entry setup."""
    keys = {str(value) for value in player_keys if value}
    if not keys:
        return 0
    pending = hass.data.setdefault(_PENDING_REGISTRY_CLEANUP, {})
    pending.setdefault(entry_id, set()).update(keys)
    return len(keys)


async def async_apply_pending_registry_cleanup(
    hass: HomeAssistant,
    entry: ConfigEntry,
    current_devices: Iterable[EmbyDeviceRecord],
) -> int:
    """Remove queued registry entries only after unload and server revalidation."""
    pending_by_entry = hass.data.get(_PENDING_REGISTRY_CLEANUP, {})
    pending = set(pending_by_entry.pop(entry.entry_id, set()))
    if not pending:
        return 0

    remaining_player_keys = {device.player_key for device in current_devices}
    eligible = pending - remaining_player_keys
    registry = er.async_get(hass)
    removed = 0
    still_blocked: set[str] = set()

    for entity in tuple(registry.entities.values()):
        unique_id = str(entity.unique_id)
        if unique_id not in eligible:
            continue
        if (
            entity.domain != "media_player"
            or entity.platform != DOMAIN
            or entity.config_entry_id != entry.entry_id
        ):
            continue
        if hass.states.get(entity.entity_id) is not None:
            still_blocked.add(unique_id)
            continue
        registry.async_remove(entity.entity_id)
        removed += 1

    if still_blocked:
        pending_by_entry.setdefault(entry.entry_id, set()).update(still_blocked)

    if not pending_by_entry:
        hass.data.pop(_PENDING_REGISTRY_CLEANUP, None)

    _LOGGER.info(
        "EMBi registry follow-up completed: %s removed, %s deferred",
        removed,
        len(still_blocked),
    )
    return removed


async def async_run_automatic_cleanup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Run one uncapped, age-based automatic server cleanup cycle."""
    if not (
        entry.options.get(CONF_SERVER_CLEANUP_ENABLED, False)
        and entry.options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)
    ):
        return False

    runtime: EmbiRuntimeData = entry.runtime_data
    if runtime.cleanup_lock.locked():
        _LOGGER.warning("EMBi automatic cleanup skipped because another cleanup is running")
        return False

    async with runtime.cleanup_lock:
        runtime.last_auto_cleanup_at = dt_util.utcnow().isoformat()
        runtime.last_auto_cleanup_error = None
        client = cleanup_client(hass, entry)
        try:
            devices = await client.async_get_devices()
        except EmbyAuthError:
            runtime.last_auto_cleanup_error = "authentication_failed"
            _LOGGER.error("EMBi automatic cleanup failed: cleanup authentication rejected")
            return False
        except EmbyApiError:
            runtime.last_auto_cleanup_error = "device_query_failed"
            _LOGGER.error("EMBi automatic cleanup failed: device query unavailable")
            return False

        active = active_player_keys(hass, entry)
        plan = plan_device_cleanup(
            devices,
            now=dt_util.utcnow(),
            age_days=int(
                entry.options.get(
                    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
                    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
                )
            ),
            active_player_keys=active,
        )
        runtime.last_auto_cleanup_candidate_count = len(plan.candidates)
        runtime.last_auto_cleanup_skipped_active_count = len(plan.skipped_active)
        runtime.last_auto_cleanup_skipped_without_activity_count = len(
            plan.skipped_without_activity
        )
        runtime.last_auto_cleanup_success_count = 0
        runtime.last_auto_cleanup_failed_count = 0
        runtime.last_auto_cleanup_registry_queue_count = 0

        if not plan.candidates:
            _LOGGER.info(
                "EMBi automatic cleanup completed: no expired candidates, %s active and %s without activity skipped",
                len(plan.skipped_active),
                len(plan.skipped_without_activity),
            )
            return False

        result = await async_delete_device_records(client, plan.candidates)
        runtime.last_auto_cleanup_success_count = len(result.succeeded)
        runtime.last_auto_cleanup_failed_count = len(result.failed)

        removable: tuple[str, ...] = ()
        if result.succeeded and entry.options.get(
            CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
            True,
        ):
            try:
                remaining = await client.async_get_devices()
            except EmbyApiError:
                runtime.last_auto_cleanup_error = "post_delete_revalidation_failed"
                _LOGGER.error(
                    "EMBi automatic cleanup deleted server records but skipped registry follow-up because revalidation failed"
                )
            else:
                runtime.devices = remaining
                removable = removable_player_keys(
                    result.succeeded,
                    remaining,
                    active_player_keys=active_player_keys(hass, entry),
                )
                runtime.last_auto_cleanup_registry_queue_count = queue_registry_cleanup(
                    hass,
                    entry.entry_id,
                    removable,
                )

        _LOGGER.warning(
            "EMBi automatic cleanup completed: %s deleted, %s failed, %s registry removals queued; no per-run cap is applied",
            len(result.succeeded),
            len(result.failed),
            len(removable),
        )

        return bool(removable)


def async_setup_automatic_cleanup(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Schedule the first automatic run after 120 seconds, then every 24 hours."""
    if not (
        entry.options.get(CONF_SERVER_CLEANUP_ENABLED, False)
        and entry.options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)
    ):
        return

    runtime: EmbiRuntimeData = entry.runtime_data
    runtime.auto_cleanup_scheduled = True

    async def _async_interval_run(_now) -> None:
        reload_needed = await async_run_automatic_cleanup(hass, entry)
        if reload_needed and entry.state is ConfigEntryState.LOADED:
            await hass.config_entries.async_reload(entry.entry_id)

    if entry.options.get(CONF_SERVER_AUTO_CLEANUP_INITIAL_RUN_COMPLETED, False):
        cancel_interval = async_track_time_interval(
            hass,
            _async_interval_run,
            timedelta(hours=AUTO_CLEANUP_INTERVAL_HOURS),
        )
        entry.async_on_unload(cancel_interval)
        return

    async def _async_first_run() -> None:
        await async_run_automatic_cleanup(hass, entry)
        if not (
            entry.state is ConfigEntryState.LOADED
            and entry.options.get(CONF_SERVER_CLEANUP_ENABLED, False)
            and entry.options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)
        ):
            return
        updated = dict(entry.options)
        updated[CONF_SERVER_AUTO_CLEANUP_INITIAL_RUN_COMPLETED] = True
        hass.config_entries.async_update_entry(entry, options=updated)

    @callback
    def _start_first_run(_now) -> None:
        hass.async_create_task(
            _async_first_run(),
            "Run initial EMBi automatic device cleanup",
        )

    cancel_initial = async_call_later(
        hass,
        AUTO_CLEANUP_INITIAL_DELAY_SECONDS,
        _start_first_run,
    )
    entry.async_on_unload(cancel_initial)
