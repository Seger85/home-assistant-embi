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
    CONF_MAINTENANCE_STORE_INITIALIZED,
    CONF_REGISTRY_RECONCILIATION_VERSION,
    FOLLOW_UP_INTERRUPTED,
    MAINTENANCE_NOTIFICATION_ID_PREFIX,
    PLATFORMS,
    REGISTRY_RECONCILIATION_VERSION,
    RUN_MODE_AUTOMATIC,
    RUN_STATUS_INTERRUPTED,
    RUN_STATUS_RUNNING,
    RUN_STATUS_SERVER_COMPLETED,
)
from .entry_lifecycle import async_update_listener
from .maintenance import (
    async_apply_pending_registry_cleanup,
    async_setup_automatic_cleanup,
    cleanup_lock,
)
from .maintenance_store import EmbiMaintenanceStore, resolve_store_load
from .models import EmbiRuntimeData, MaintenanceState, MigrationSummary
from .options_model import legacy_initial_run_completed, migrate_options_090
from .player_actions import async_reconcile_invisible_player_entities

_LOGGER = logging.getLogger(__name__)


def _notification_id(entry: ConfigEntry) -> str:
    return f"{MAINTENANCE_NOTIFICATION_ID_PREFIX}_{entry.entry_id}"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EMBi from a config entry and migrate options non-destructively."""
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

    original_options = dict(entry.options)
    rc3_initial_run_completed = legacy_initial_run_completed(original_options)
    migrated_options, options_changed = migrate_options_090(original_options, devices)
    store_expected = bool(migrated_options.get(CONF_MAINTENANCE_STORE_INITIALIZED, False))

    store = EmbiMaintenanceStore.create(hass, entry.entry_id)
    storage_available = True
    try:
        loaded_state = await store.async_load()
    except Exception:
        storage_available = False
        maintenance_state = MaintenanceState()
        _LOGGER.exception("EMBi failed to load persistent maintenance state")
        persistent_notification.async_create(
            hass,
            "EMBi konnte den persistenten Lauf- und Schedulerstatus nicht laden. "
            "Automatische Läufe bleiben aus Sicherheitsgründen angehalten.",
            title="EMBi-Wartung angehalten",
            notification_id=_notification_id(entry),
        )
    else:
        decision = resolve_store_load(
            loaded_state,
            store_expected=store_expected,
            legacy_initial_run_completed=rc3_initial_run_completed,
        )
        maintenance_state = decision.state
        storage_available = decision.storage_available
        if not storage_available:
            _LOGGER.error("EMBi maintenance Store was expected but could not be loaded")
            persistent_notification.async_create(
                hass,
                "Der bereits initialisierte EMBi-Wartungsspeicher fehlt oder wurde von "
                "Home Assistant als beschädigt verworfen. Automatische Läufe bleiben "
                "aus Sicherheitsgründen angehalten.",
                title="EMBi-Wartung angehalten",
                notification_id=_notification_id(entry),
            )
        elif decision.initialize_store:
            try:
                await store.async_save(maintenance_state)
            except Exception:
                storage_available = False
                _LOGGER.exception("EMBi failed to initialize persistent maintenance state")
                persistent_notification.async_create(
                    hass,
                    "EMBi konnte den Wartungsspeicher nicht initialisieren. "
                    "Automatische Läufe bleiben aus Sicherheitsgründen angehalten.",
                    title="EMBi-Wartung angehalten",
                    notification_id=_notification_id(entry),
                )
            else:
                migrated_options[CONF_MAINTENANCE_STORE_INITIALIZED] = True
        elif not store_expected:
            migrated_options[CONF_MAINTENANCE_STORE_INITIALIZED] = True

    if storage_available and options_changed:
        maintenance_state.migration = MigrationSummary(
            status="completed",
            from_schema=original_options.get("options_schema_version"),
            to_schema=int(migrated_options["options_schema_version"]),
            completed_at=dt_util.utcnow().isoformat(),
            changed=True,
            unresolved_rules=len(migrated_options.get("unresolved_legacy_rules", [])),
        )
        try:
            await store.async_save(maintenance_state)
        except Exception:
            storage_available = False
            _LOGGER.exception("EMBi failed to persist the 0.9 migration result")
            persistent_notification.async_create(
                hass,
                "EMBi konnte die Migration nicht sicher speichern. Die Integration wurde "
                "nicht mit stillen Standardwerten fortgesetzt.",
                title="EMBi-Migration angehalten",
                notification_id=_notification_id(entry),
            )
            raise ConfigEntryNotReady("EMBi migration storage failed") from None
        _LOGGER.info("EMBi option migration to schema 2 completed")

    if migrated_options != original_options:
        hass.config_entries.async_update_entry(entry, options=migrated_options)

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
        except Exception:
            runtime.maintenance_storage_available = False
            _LOGGER.exception("EMBi failed to persist interrupted maintenance state")

    await async_apply_pending_registry_cleanup(hass, entry, devices)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    reconciliation_version = int(migrated_options.get(CONF_REGISTRY_RECONCILIATION_VERSION, 0) or 0)
    if reconciliation_version < REGISTRY_RECONCILIATION_VERSION:
        try:
            reconciliation = await async_reconcile_invisible_player_entities(hass, entry)
        except Exception:
            _LOGGER.exception("EMBi startup registry reconciliation failed")
        else:
            if not reconciliation.protected and not reconciliation.failed:
                migrated_options[CONF_REGISTRY_RECONCILIATION_VERSION] = (
                    REGISTRY_RECONCILIATION_VERSION
                )
                hass.config_entries.async_update_entry(entry, options=migrated_options)
            else:
                _LOGGER.warning(
                    "EMBi startup registry reconciliation deferred: %s protected, %s failed",
                    len(reconciliation.protected),
                    len(reconciliation.failed),
                )

    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    await async_setup_automatic_cleanup(hass, entry)
    return True
