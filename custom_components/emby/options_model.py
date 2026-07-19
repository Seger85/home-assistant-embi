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
    DEFAULT_REMOVE_HA_ENTITIES,
    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
    DEFAULT_TECHNICAL_ACCESS_VISIBILITY,
    OPTIONS_SCHEMA_VERSION,
    PLAYER_MODE_ACTIVE_ONLY,
    PLAYER_MODE_PERSISTENT,
    SENSOR_KEYS,
)
from .legacy_migration import apply_legacy_option_migration

ACTIVE_STATES = {"playing", "paused"}


def default_options() -> dict[str, Any]:
    """Return safe canonical defaults for a newly configured EMBi installation."""
    return {
        CONF_OPTIONS_SCHEMA_VERSION: OPTIONS_SCHEMA_VERSION,
        CONF_GLOBAL_PLAYER_MODE: PLAYER_MODE_PERSISTENT,
        CONF_AUTO_SHOW_NEW_PLAYERS: DEFAULT_AUTO_SHOW_NEW_PLAYERS,
        CONF_TECHNICAL_ACCESS_VISIBILITY: DEFAULT_TECHNICAL_ACCESS_VISIBILITY,
        CONF_ALLOWED_DEVICE_IDS: [],
        CONF_HIDDEN_EXACT_PLAYERS: [],
        CONF_HIDDEN_WHOLE_DEVICES: [],
        CONF_USER_MASTER_VISIBILITY: {},
        CONF_UNRESOLVED_LEGACY_RULES: [],
        CONF_ENABLED_SENSORS: list(SENSOR_KEYS),
        CONF_SERVER_CLEANUP_ENABLED: True,
        CONF_SERVER_CLEANUP_AGE_DAYS: DEFAULT_SERVER_CLEANUP_AGE_DAYS,
        CONF_SERVER_AUTO_CLEANUP_ENABLED: False,
        CONF_SERVER_AUTO_CLEANUP_AGE_DAYS: DEFAULT_SERVER_CLEANUP_AGE_DAYS,
        CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES: DEFAULT_REMOVE_HA_ENTITIES,
        CONF_REGISTRY_RECONCILIATION_VERSION: 0,
        CONF_REGISTRY_RECONCILIATION_FAILURES: 0,
        CONF_SENSOR_IDENTITY_VERSION: 0,
    }


def migrate_options(
    options: Mapping[str, Any],
    devices: Iterable[EmbyDeviceRecord],
    *,
    new_install: bool = False,
) -> tuple[dict[str, Any], bool]:
    """Idempotently normalize options and isolate historical-key translation."""
    source = dict(options)
    defaults = default_options()
    migrated = dict(defaults)
    migrated.update(source)

    apply_legacy_option_migration(
        migrated,
        source,
        devices,
        new_install=new_install,
    )
    migrated[CONF_OPTIONS_SCHEMA_VERSION] = OPTIONS_SCHEMA_VERSION

    migrated[CONF_SERVER_CLEANUP_ENABLED] = bool(
        source.get(CONF_SERVER_CLEANUP_ENABLED, defaults[CONF_SERVER_CLEANUP_ENABLED])
    )
    migrated[CONF_SERVER_CLEANUP_AGE_DAYS] = int(
        source.get(
            CONF_SERVER_CLEANUP_AGE_DAYS,
            defaults[CONF_SERVER_CLEANUP_AGE_DAYS],
        )
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

    configured_sensors = source.get(
        CONF_ENABLED_SENSORS,
        defaults[CONF_ENABLED_SENSORS],
    )
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

    return migrated, migrated != source


def should_expose_player(
    *,
    player_key: str,
    reported_device_id: str | None,
    state: str | None,
    options: Mapping[str, Any],
    technical_access: bool,
    users: Iterable[str] = (),
) -> bool:
    """Apply exact hidden rules and canonical global visibility settings."""
    hidden_exact = {str(value) for value in options.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
    hidden_devices = {str(value) for value in options.get(CONF_HIDDEN_WHOLE_DEVICES, [])}
    if player_key in hidden_exact:
        return False
    if reported_device_id and reported_device_id in hidden_devices:
        return False

    named_users = tuple(str(value) for value in users if str(value))
    user_visibility = options.get(CONF_USER_MASTER_VISIBILITY, {})
    if (
        len(named_users) == 1
        and isinstance(user_visibility, Mapping)
        and user_visibility.get(named_users[0]) is False
    ):
        return False

    if technical_access and not bool(options.get(CONF_TECHNICAL_ACCESS_VISIBILITY, False)):
        return False
    if options.get(CONF_GLOBAL_PLAYER_MODE) == PLAYER_MODE_ACTIVE_ONLY:
        return str(state or "").casefold() in ACTIVE_STATES
    if not bool(options.get(CONF_AUTO_SHOW_NEW_PLAYERS, DEFAULT_AUTO_SHOW_NEW_PLAYERS)):
        return player_key in {str(value) for value in options.get(CONF_ALLOWED_DEVICE_IDS, [])}
    return True


# Compatibility aliases remain only while current callers are migrated in the same
# release branch. They are removed before the stable release.
default_options_090 = default_options
migrate_options_090 = migrate_options
