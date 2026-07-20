from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

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
    CONF_ENABLED_SENSORS,
    CONF_MAINTENANCE_STORE_INITIALIZED,
    CONF_REGISTRY_RECONCILIATION_FAILURES,
    CONF_REGISTRY_RECONCILIATION_VERSION,
    CONF_SENSOR_IDENTITY_VERSION,
    FOLLOW_UP_INTERRUPTED,
    MAINTENANCE_NOTIFICATION_ID_PREFIX,
    PLATFORMS,
    REGISTRY_RECONCILIATION_MAX_FAILURES,
    REGISTRY_RECONCILIATION_VERSION,
    RUN_MODE_AUTOMATIC,
    RUN_STATUS_INTERRUPTED,
    RUN_STATUS_RUNNING,
    RUN_STATUS_SERVER_COMPLETED,
    SENSOR_IDENTITY_VERSION,
    SENSOR_KEYS,
)
from .entry_lifecycle import async_update_listener
from .legacy_migration import legacy_cleanup_completed, migrate_options
from .maintenance import (
    async_apply_pending_registry_cleanup,
    async_setup_automatic_cleanup,
    cleanup_lock,
)
from .maintenance_store import EmbiMaintenanceStore, resolve_store_load
from .models import EmbiRuntimeData, MaintenanceState, MigrationSummary
from .player_actions import PlayerActionResult
from .player_reconciliation import async_reconcile_player_visibility
from .sensor_registry import async_prepare_sensor_registry_identities

_LOGGER = logging.getLogger(__name__)


def _notification_id(entry: ConfigEntry) -> str:
    return f"{MAINTENANCE_NOTIFICATION_ID_PREFIX}_{entry.entry_id}"


async def _async_enforce_player_visibility(
    hass: HomeAssistant,
    entry: ConfigEntry,
    migrated_options: dict[str, Any],
) -> PlayerActionResult | None:
    """Enforce saved visibility on every setup while bounding migration retries."""
    reconciliation_version = int(migrated_options.get(CONF_REGISTRY_RECONCILIATION_VERSION, 0) or 0)
    failures = int(migrated_options.get(CONF_REGISTRY_RECONCILIATION_FAILURES, 0) or 0)
    migration_pending = reconciliation_version < REGISTRY_RECONCILIATION_VERSION

    try:
        reconciliation = await async_reconcile_player_visibility(hass, entry)
    except Exception:
        if migration_pending and failures < REGISTRY_RECONCILIATION_MAX_FAILURES:
            migrated_options[CONF_REGISTRY_RECONCILIATION_FAILURES] = failures + 1
            hass.config_entries.async_update_entry(entry, options=migrated_options)
        _LOGGER.exception("EMBi visibility reconciliation failed during config-entry setup")
        return None

    if not migration_pending:
        return reconciliation

    if reconciliation.failed and failures < REGISTRY_RECONCILIATION_MAX_FAILURES:
        failures += 1
        migrated_options[CONF_REGISTRY_RECONCILIATION_FAILURES] = failures
        hass.config_entries.async_update_entry(entry, options=migrated_options)
        _LOGGER.log(
            (logging.WARNING if failures < REGISTRY_RECONCILIATION_MAX_FAILURES else logging.INFO),
            "EMBi migration reconciliation deferred: %s failed; attempt %s of %s",
            len(reconciliation.failed),
            failures,
            REGISTRY_RECONCILIATION_MAX_FAILURES,
        )
        return reconciliation

    migrated_options[CONF_REGISTRY_RECONCILIATION_VERSION] = REGISTRY_RECONCILIATION_VERSION
    migrated_options[CONF_REGISTRY_RECONCILIATION_FAILURES] = 0
    hass.config_entries.async_update_entry(entry, options=migrated_options)
    return reconciliation


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EMBi and run bounded idempotent migrations."""
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
    legacy_cleanup_was_completed = legacy_cleanup_completed(original_options)
    migrated_options, options_changed = migrate_options(original_options, devices)
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
            legacy_initial_run_completed=legacy_cleanup_was_completed,
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
            _LOGGER.exception("EMBi failed to persist the option migration result")
            persistent_notification.async_create(
                hass,
                "EMBi konnte die Migration nicht sicher speichern. Die Integration wurde "
                "nicht mit stillen Standardwerten fortgesetzt.",
                title="EMBi-Migration angehalten",
                notification_id=_notification_id(entry),
            )
            raise ConfigEntryNotReady("EMBi migration storage failed") from None
        _LOGGER.info("EMBi option migration to schema 4 completed")

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

    if int(migrated_options.get(CONF_SENSOR_IDENTITY_VERSION, 0) or 0) < SENSOR_IDENTITY_VERSION:
        enabled = migrated_options.get(CONF_ENABLED_SENSORS, list(SENSOR_KEYS))
        sensor_result = async_prepare_sensor_registry_identities(
            hass,
            entry,
            (str(value) for value in enabled),
        )
        migrated_options[CONF_SENSOR_IDENTITY_VERSION] = SENSOR_IDENTITY_VERSION
        hass.config_entries.async_update_entry(entry, options=migrated_options)
        _LOGGER.info(
            "EMBi sensor identity migration: %s prepared, %s migrated, "
            "%s duplicate remnants removed, %s collisions",
            sensor_result.prepared,
            sensor_result.migrated,
            sensor_result.duplicates_removed,
            sensor_result.collisions,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await _async_enforce_player_visibility(hass, entry, migrated_options)

    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    await async_setup_automatic_cleanup(hass, entry)
    return True
