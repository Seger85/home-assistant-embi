"""Normalize malformed stored settings without accidentally enabling deletion."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .const import (
    CONF_ALLOWED_DEVICE_IDS,
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_ENABLED_SENSORS,
    CONF_GLOBAL_PLAYER_MODE,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_HIDDEN_WHOLE_DEVICES,
    CONF_MAINTENANCE_STORE_INITIALIZED,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_AGE_DAYS,
    CONF_SERVER_CLEANUP_ENABLED,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_UNRESOLVED_LEGACY_RULES,
    CONF_USER_MASTER_VISIBILITY,
    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
    MAX_SERVER_CLEANUP_AGE_DAYS,
    PLAYER_MODE_ACTIVE_ONLY,
    PLAYER_MODE_PERSISTENT,
)


def _boolean(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.casefold() in {"true", "false"}:
        return value.casefold() == "true"
    return default


def normalize_stored_options(options: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
    """Return safe usable values plus whether malformed current settings were found."""
    result = dict(options)
    changed = False
    for key, fallback in (
        (CONF_AUTO_SHOW_NEW_PLAYERS, True),
        (CONF_TECHNICAL_ACCESS_VISIBILITY, False),
        (CONF_SERVER_CLEANUP_ENABLED, False),
        (CONF_SERVER_AUTO_CLEANUP_ENABLED, False),
        (CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES, False),
        (CONF_MAINTENANCE_STORE_INITIALIZED, True),
    ):
        if key in result and not isinstance(result[key], bool):
            result[key] = _boolean(result[key], fallback)
            changed = True
    for key in (CONF_SERVER_CLEANUP_AGE_DAYS, CONF_SERVER_AUTO_CLEANUP_AGE_DAYS):
        if key not in result:
            continue
        value = result[key]
        try:
            if isinstance(value, bool) or (isinstance(value, float) and not value.is_integer()):
                raise ValueError
            days = int(value)
            if not 1 <= days <= MAX_SERVER_CLEANUP_AGE_DAYS:
                raise ValueError
        except (ValueError, TypeError, OverflowError):
            days = DEFAULT_SERVER_CLEANUP_AGE_DAYS
            changed = True
        result[key] = days
    if CONF_GLOBAL_PLAYER_MODE in result and result[CONF_GLOBAL_PLAYER_MODE] not in (
        PLAYER_MODE_PERSISTENT,
        PLAYER_MODE_ACTIVE_ONLY,
    ):
        result[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_PERSISTENT
        changed = True
    for key in (
        CONF_ALLOWED_DEVICE_IDS,
        CONF_HIDDEN_EXACT_PLAYERS,
        CONF_HIDDEN_WHOLE_DEVICES,
        CONF_UNRESOLVED_LEGACY_RULES,
        CONF_ENABLED_SENSORS,
    ):
        if key in result and not isinstance(result[key], (list, tuple, set)):
            result[key] = [result[key]] if isinstance(result[key], str) and result[key] else []
            changed = True
    for key in (
        CONF_ALLOWED_DEVICE_IDS,
        CONF_HIDDEN_EXACT_PLAYERS,
        CONF_HIDDEN_WHOLE_DEVICES,
        CONF_UNRESOLVED_LEGACY_RULES,
        CONF_ENABLED_SENSORS,
    ):
        if key in result:
            values = result[key]
            if any(not isinstance(value, str) for value in values):
                result[key] = [value for value in values if isinstance(value, str)]
                changed = True
    if CONF_USER_MASTER_VISIBILITY in result:
        users = result[CONF_USER_MASTER_VISIBILITY]
        if not isinstance(users, Mapping):
            result[CONF_USER_MASTER_VISIBILITY] = {}
            changed = True
        else:
            result[CONF_USER_MASTER_VISIBILITY] = {
                str(key): _boolean(value, True) for key, value in users.items()
            }
            changed |= any(not isinstance(value, bool) for value in users.values())
    if changed:
        # Recovery must never turn a malformed truthy value into automatic deletion.
        result[CONF_SERVER_AUTO_CLEANUP_ENABLED] = False
    return result, changed
