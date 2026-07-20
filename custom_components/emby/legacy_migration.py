from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .api import EmbyDeviceRecord
from .const import (
    CONF_ALLOWED_DEVICE_IDS,
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_ENABLED_SENSORS,
    CONF_GLOBAL_PLAYER_MODE,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_HIDDEN_WHOLE_DEVICES,
    CONF_MAINTENANCE_STORE_INITIALIZED,
    CONF_OPTIONS_SCHEMA_VERSION,
    CONF_REGISTRY_RECONCILIATION_FAILURES,
    CONF_REGISTRY_RECONCILIATION_VERSION,
    CONF_SENSOR_IDENTITY_VERSION,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_AGE_DAYS,
    CONF_SERVER_CLEANUP_ENABLED,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_UNRESOLVED_LEGACY_RULES,
    CONF_USER_MASTER_VISIBILITY,
    DEFAULT_AUTO_SHOW_NEW_PLAYERS,
    DEFAULT_TECHNICAL_ACCESS_VISIBILITY,
    OPTIONS_SCHEMA_VERSION,
    PLAYER_MODE_ACTIVE_ONLY,
    PLAYER_MODE_PERSISTENT,
    SENSOR_KEYS,
)
from .options_model import default_options

# Historical keys are intentionally isolated here so current runtime modules and
# public documentation remain version-neutral while published upgrade paths stay supported.
_LEGACY_CLIENT_MODE = "client_mode"
_LEGACY_IGNORED_PLAYER_KEYS = "ignored_player_keys"
_LEGACY_IGNORED_REPORTED_DEVICE_IDS = "ignored_reported_device_ids"
_LEGACY_UNRESOLVED_IGNORED_IDS = "unresolved_ignored_ids"
_LEGACY_IGNORED_DEVICE_IDS = "ignored_device_ids"
_LEGACY_CLEANUP_API_KEY = "server_cleanup_api_key"
_LEGACY_AUTO_CONFIRMATION_TEXT = "auto_cleanup_confirmation_text"
_LEGACY_ADD_DELETED_TO_IGNORED = "add_deleted_to_ignored"
_LEGACY_INITIAL_RUN_COMPLETED = "server_auto_cleanup_initial_run_completed"
_LEGACY_MODE_ACTIVE_ONLY = "active_only"
_LEGACY_MODE_ALLOWLIST = "allowlist"


def legacy_cleanup_completed(options: Mapping[str, Any]) -> bool:
    """Return the historical first-run marker without exposing it elsewhere."""
    return bool(options.get(_LEGACY_INITIAL_RUN_COMPLETED, False))


def _strings(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    return sorted({str(item) for item in value if str(item)})


def _user_visibility(value: Any) -> dict[str, bool]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): bool(enabled)
        for key, enabled in sorted(value.items(), key=lambda item: str(item[0]).casefold())
        if str(key)
    }


def migrate_options(
    options: Mapping[str, Any],
    devices: Iterable[EmbyDeviceRecord],
    *,
    new_install: bool = False,
) -> tuple[dict[str, Any], bool]:
    """Idempotently preserve published upgrades while normalizing current options."""
    source = dict(options)
    defaults = default_options()
    migrated = dict(defaults)
    migrated.update(source)
    records = list(devices)

    by_record_id: dict[str, list[EmbyDeviceRecord]] = {}
    for device in records:
        by_record_id.setdefault(device.record_id, []).append(device)
    known_player_keys = {device.player_key for device in records}
    known_reported_ids = {device.reported_device_id for device in records}

    canonical_user_visibility = _user_visibility(source.get(CONF_USER_MASTER_VISIBILITY, {}))

    allowed: set[str] = set()
    for configured_id in source.get(CONF_ALLOWED_DEVICE_IDS, []):
        value = str(configured_id)
        matches = by_record_id.get(value, [])
        allowed.add(matches[0].player_key if len(matches) == 1 else value)

    hidden_players = {
        *source.get(CONF_HIDDEN_EXACT_PLAYERS, []),
        *source.get(_LEGACY_IGNORED_PLAYER_KEYS, []),
    }
    hidden_devices = {
        *source.get(CONF_HIDDEN_WHOLE_DEVICES, []),
        *source.get(_LEGACY_IGNORED_REPORTED_DEVICE_IDS, []),
    }
    unresolved = {
        *source.get(CONF_UNRESOLVED_LEGACY_RULES, []),
        *source.get(_LEGACY_UNRESOLVED_IGNORED_IDS, []),
    }

    for configured_id in source.get(_LEGACY_IGNORED_DEVICE_IDS, []):
        value = str(configured_id)
        if value in known_player_keys:
            hidden_players.add(value)
        elif value in known_reported_ids:
            hidden_devices.add(value)
        elif len(by_record_id.get(value, [])) == 1:
            hidden_devices.add(by_record_id[value][0].reported_device_id)
        else:
            unresolved.add(value)

    legacy_mode = str(source.get(_LEGACY_CLIENT_MODE, "all"))
    if CONF_GLOBAL_PLAYER_MODE not in source:
        migrated[CONF_GLOBAL_PLAYER_MODE] = (
            PLAYER_MODE_ACTIVE_ONLY
            if legacy_mode == _LEGACY_MODE_ACTIVE_ONLY
            else PLAYER_MODE_PERSISTENT
        )
    if CONF_AUTO_SHOW_NEW_PLAYERS not in source:
        migrated[CONF_AUTO_SHOW_NEW_PLAYERS] = (
            False if legacy_mode == _LEGACY_MODE_ALLOWLIST else DEFAULT_AUTO_SHOW_NEW_PLAYERS
        )
    if CONF_TECHNICAL_ACCESS_VISIBILITY not in source:
        migrated[CONF_TECHNICAL_ACCESS_VISIBILITY] = (
            DEFAULT_TECHNICAL_ACCESS_VISIBILITY if new_install else True
        )

    migrated[CONF_OPTIONS_SCHEMA_VERSION] = OPTIONS_SCHEMA_VERSION
    migrated[CONF_ALLOWED_DEVICE_IDS] = sorted(allowed)
    migrated[CONF_HIDDEN_EXACT_PLAYERS] = _strings(hidden_players)
    migrated[CONF_HIDDEN_WHOLE_DEVICES] = _strings(hidden_devices)
    migrated[CONF_UNRESOLVED_LEGACY_RULES] = _strings(unresolved)
    for user_name in tuple(canonical_user_visibility):
        migrated.pop(user_name, None)
    migrated[CONF_USER_MASTER_VISIBILITY] = canonical_user_visibility

    migrated[CONF_SERVER_CLEANUP_ENABLED] = bool(
        source.get(CONF_SERVER_CLEANUP_ENABLED, defaults[CONF_SERVER_CLEANUP_ENABLED])
    )
    migrated[CONF_SERVER_CLEANUP_AGE_DAYS] = int(
        source.get(CONF_SERVER_CLEANUP_AGE_DAYS, defaults[CONF_SERVER_CLEANUP_AGE_DAYS])
    )
    migrated[CONF_SERVER_AUTO_CLEANUP_ENABLED] = bool(
        source.get(
            CONF_SERVER_AUTO_CLEANUP_ENABLED,
            defaults[CONF_SERVER_AUTO_CLEANUP_ENABLED],
        )
    )
    migrated[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS] = int(
        source.get(
            CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
            defaults[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS],
        )
    )
    migrated[CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES] = bool(
        source.get(
            CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
            defaults[CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES],
        )
    )

    configured_sensors = source.get(CONF_ENABLED_SENSORS, defaults[CONF_ENABLED_SENSORS])
    if not isinstance(configured_sensors, (list, tuple, set)):
        configured_sensors = defaults[CONF_ENABLED_SENSORS]
    enabled_sensors = {str(value) for value in configured_sensors}
    migrated[CONF_ENABLED_SENSORS] = [key for key in SENSOR_KEYS if key in enabled_sensors]

    for key in (
        CONF_REGISTRY_RECONCILIATION_VERSION,
        CONF_REGISTRY_RECONCILIATION_FAILURES,
        CONF_SENSOR_IDENTITY_VERSION,
    ):
        try:
            migrated[key] = max(0, int(source.get(key, defaults[key]) or 0))
        except (TypeError, ValueError):
            migrated[key] = 0

    if source.get(CONF_MAINTENANCE_STORE_INITIALIZED):
        migrated[CONF_MAINTENANCE_STORE_INITIALIZED] = True

    for legacy_key in (
        _LEGACY_CLIENT_MODE,
        _LEGACY_IGNORED_PLAYER_KEYS,
        _LEGACY_IGNORED_REPORTED_DEVICE_IDS,
        _LEGACY_UNRESOLVED_IGNORED_IDS,
        _LEGACY_IGNORED_DEVICE_IDS,
        _LEGACY_CLEANUP_API_KEY,
        _LEGACY_AUTO_CONFIRMATION_TEXT,
        _LEGACY_ADD_DELETED_TO_IGNORED,
        _LEGACY_INITIAL_RUN_COMPLETED,
    ):
        migrated.pop(legacy_key, None)

    return migrated, migrated != source
