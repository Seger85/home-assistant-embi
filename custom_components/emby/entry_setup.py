from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_SSL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .api import EmbyApiClient, EmbyApiError, EmbyAuthError
from .const import (
    AUTO_CLEANUP_INTERVAL_HOURS,
    FOLLOW_UP_INTERRUPTED,
    MAINTENANCE_NOTIFICATION_ID_PREFIX,
    MAINTENANCE_STORE_INITIALIZED,
    PLATFORMS,
    RUN_MODE_AUTOMATIC,
    RUN_STATUS_INTERRUPTED,
    RUN_STATUS_RUNNING,
    RUN_STATUS_SERVER_COMPLETED,
)
from .entry_lifecycle import async_update_listener
from .helpers import legacy_initial_run_completed, migrate_stable_options
from .maintenance import (
    async_apply_pending_registry_cleanup,
    async_setup_automatic_cleanup,
    cleanup_lock,
)
from .maintenance_store import EmbiMaintenanceStore, resolve_store_load
from .models import EmbiRuntimeData, MaintenanceState

_LOGGER = logging.getLogger(__name__)


def _notification_id(entry: ConfigEntry) -> str:
    return f"{MAINTENANCE_NOTIFICATION_ID_PREFIX}_{entry.entry_id}"


async def _async_initialize_store(
    hass: HomeAssistant,
    entry: ConfigEntry,
    store: EmbiMaintenanceStore,
) -> tuple[MaintenanceState, bool]:
    """Load or initialize the Store and fail closed on unexpected missing data."""
    try:
        loaded = resolve_store_load(
            await store.async_load_data(),
            initialized_marker=bool(entry.options.get(MAINTENANCE_STORE_INITIALIZED, False)),
        )
        if loaded.needs_initial_save:
            await store.async_save(loaded.state)
            options = dict(entry.options)
            options[MAINTENANCE_STORE_INITIALIZED] = True
            hass.config_entries.async_update_entry(entry, options=options)
        return loaded.state, True
    except Exception:  # noqa: BLE001
        _LOGGER.exception("EMBi failed to load or initialize persistent maintenance state")
        persistent_notification.async_create(
            hass,
            "EMBi konnte den persistenten Lauf- und Schedulerstatus nicht sicher laden. "
            "Automatische Läufe bleiben aus Sicherheitsgründen angehalten.",
            title="EMBi-Wartung angehalten",
            notification_id=_notification_id(entry),
        )
        return MaintenanceState(), False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EMBi from a config entry."""
    client = EmbyApiClient(
        session=async_get_clientsession(hass),
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        api_key=entry.data[CONF_API_KEY],
        use_ssl=entry.data[CONF_SSL],
    )
    try:
        await client.async_validate()
        devices = await client.async_get_devices()
    except EmbyAuthError as err:
        raise ConfigEntryAuthFailed from err
    except EmbyApiError as err:
        raise ConfigEntryNotReady(str(err)) from err

    rc3_initial_run_completed = legacy_initial_run_completed(entry.options)
    migrated_options, changed = migrate_stable_options(dict(entry.options), devices)
    if changed:
        hass.config_entries.async_update_entry(entry, options=migrated_options)

    store = EmbiMaintenanceStore.create(hass, entry.entry_id)
    maintenance_state, storage_available = await _async_initialize_store(hass, entry, store)
    if rc3_initial_run_completed:
        maintenance_state.initial_run_completed = True

    runtime = EmbiRuntimeData(
        api_client=client,
        devices=devices,
        cleanup_lock=cleanup_lock(hass, entry.entry_id),
        maintenance_store=store,
        maintenance_state=maintenance_state,
        maintenance_storage_available=storage_available,
    )
    entry.runtime_data = runtime

    report = maintenance_state.report
    if (
        report.status in {RUN_STATUS_RUNNING, RUN_STATUS_SERVER_COMPLETED}
        and not runtime.cleanup_lock.locked()
    ):
        report.status = RUN_STATUS_INTERRUPTED
        report.follow_up_status = FOLLOW_UP_INTERRUPTED
        report.last_error = "cleanup_interrupted_before_completion"
        report.result_counts_complete = False
        report.completed_at = dt_util.utcnow().isoformat()
        if report.mode == RUN_MODE_AUTOMATIC:
            report.next_run_at = (
                dt_util.utcnow() + timedelta(hours=AUTO_CLEANUP_INTERVAL_HOURS)
            ).isoformat()
        try:
            await store.async_save(maintenance_state)
        except Exception:  # noqa: BLE001
            runtime.maintenance_storage_available = False
            _LOGGER.exception("EMBi failed to persist interrupted maintenance state")

    await async_apply_pending_registry_cleanup(hass, entry, devices)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    await async_setup_automatic_cleanup(hass, entry)
    return True
