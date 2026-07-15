from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util

from .const import (
    AUTO_CLEANUP_INITIAL_DELAY_SECONDS,
    CONF_MAINTENANCE_STORE_INITIALIZED,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_CLEANUP_ENABLED,
    MAINTENANCE_NOTIFICATION_ID_PREFIX,
)
from .maintenance_common import _async_save_state, _parse_utc, _utc_iso
from .maintenance_cycle import async_run_automatic_cleanup
from .models import EmbiRuntimeData
from .scheduling import normalize_utc, resolve_scheduled_run

_LOGGER = logging.getLogger(__name__)


def _notification_id(entry: ConfigEntry) -> str:
    return f"{MAINTENANCE_NOTIFICATION_ID_PREFIX}_{entry.entry_id}"


def _registration_enabled(entry: ConfigEntry, runtime: EmbiRuntimeData) -> bool:
    """Return whether this runtime may own one automatic-cleanup callback."""
    return bool(
        getattr(entry, "runtime_data", None) is runtime
        and not runtime.unloading
        and runtime.maintenance_store is not None
        and runtime.maintenance_storage_available
        and entry.options.get(CONF_SERVER_CLEANUP_ENABLED, False)
        and entry.options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)
    )


def _execution_enabled(entry: ConfigEntry, runtime: EmbiRuntimeData) -> bool:
    """Return whether the current callback may execute destructive work now."""
    return bool(entry.state is ConfigEntryState.LOADED and _registration_enabled(entry, runtime))


async def _async_refresh_persistent_state(
    hass: HomeAssistant,
    entry: ConfigEntry,
    runtime: EmbiRuntimeData,
) -> bool:
    """Refresh state after a reload may have overlapped an older cleanup task."""
    if runtime.maintenance_store is None:
        runtime.maintenance_storage_available = False
        return False
    try:
        loaded = await runtime.maintenance_store.async_load()
    except Exception:
        runtime.maintenance_storage_available = False
        _LOGGER.exception("EMBi failed to refresh persistent maintenance state")
        persistent_notification.async_create(
            hass,
            "EMBi konnte den persistenten Wartungsstatus vor dem automatischen Lauf "
            "nicht erneut laden. Der Lauf wurde aus Sicherheitsgründen ausgelassen.",
            title="EMBi-Wartung angehalten",
            notification_id=_notification_id(entry),
        )
        return False
    if loaded is None and entry.options.get(CONF_MAINTENANCE_STORE_INITIALIZED, False):
        runtime.maintenance_storage_available = False
        _LOGGER.error("EMBi expected persistent maintenance state but refresh returned no data")
        persistent_notification.async_create(
            hass,
            "Der bereits initialisierte EMBi-Wartungsspeicher ist nicht verfügbar. "
            "Automatische Läufe bleiben aus Sicherheitsgründen angehalten.",
            title="EMBi-Wartung angehalten",
            notification_id=_notification_id(entry),
        )
        return False
    if loaded is not None:
        runtime.maintenance_state = loaded
    return True


async def async_schedule_automatic_cleanup(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Schedule exactly one persistent absolute automatic cleanup callback."""
    runtime: EmbiRuntimeData = entry.runtime_data
    if runtime.cancel_auto_cleanup is not None:
        runtime.cancel_auto_cleanup()
        runtime.cancel_auto_cleanup = None
    runtime.auto_cleanup_scheduled = False

    if not _registration_enabled(entry, runtime):
        return

    now = normalize_utc(dt_util.utcnow())
    if runtime.cleanup_lock.locked():
        next_run = now + timedelta(seconds=AUTO_CLEANUP_INITIAL_DELAY_SECONDS)
        catch_up = False
    else:
        decision = resolve_scheduled_run(
            now=now,
            persisted_next_run=_parse_utc(runtime.maintenance_state.report.next_run_at),
            grace_seconds=AUTO_CLEANUP_INITIAL_DELAY_SECONDS,
        )
        next_run = decision.run_at
        catch_up = decision.catch_up

    if catch_up:
        runtime.maintenance_state.report.next_run_at = _utc_iso(next_run)
        if not await _async_save_state(hass, entry):
            return

    async def _async_scheduled_run(_now: datetime) -> None:
        runtime.cancel_auto_cleanup = None
        runtime.auto_cleanup_scheduled = False

        if not _registration_enabled(entry, runtime):
            return
        if not _execution_enabled(entry, runtime):
            await async_schedule_automatic_cleanup(hass, entry)
            return
        if runtime.cleanup_lock.locked():
            await async_schedule_automatic_cleanup(hass, entry)
            return
        if not await _async_refresh_persistent_state(hass, entry, runtime):
            return
        if not _execution_enabled(entry, runtime):
            return

        persisted = _parse_utc(runtime.maintenance_state.report.next_run_at)
        current = normalize_utc(dt_util.utcnow())
        if persisted is not None and persisted > current:
            await async_schedule_automatic_cleanup(hass, entry)
            return

        reload_needed = await async_run_automatic_cleanup(hass, entry)
        if reload_needed and _execution_enabled(entry, runtime):
            await hass.config_entries.async_reload(entry.entry_id)
            return
        if _execution_enabled(entry, runtime):
            await async_schedule_automatic_cleanup(hass, entry)

    runtime.cancel_auto_cleanup = async_track_point_in_utc_time(
        hass,
        _async_scheduled_run,
        next_run,
    )
    runtime.auto_cleanup_scheduled = True


async def async_setup_automatic_cleanup(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Restore or create the persistent absolute automatic cleanup schedule."""
    await async_schedule_automatic_cleanup(hass, entry)
