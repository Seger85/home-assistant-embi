from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .api import EmbyDeviceRecord
from .const import (
    AGE_PRESET_CUSTOM,
    AGE_PRESETS,
    CLIENT_MODE_ACTIVE_ONLY,
    CLIENT_MODE_ALLOWLIST,
    CONF_ALLOWED_DEVICE_IDS,
    CONF_IGNORED_PLAYER_KEYS,
    CONF_IGNORED_REPORTED_DEVICE_IDS,
    CONF_UNRESOLVED_IGNORED_IDS,
)

ACTIVE_STATES = {"playing", "paused"}
_LEGACY_IGNORED_DEVICE_IDS = "ignored_device_ids"
_LEGACY_CLEANUP_API_KEY = "server_cleanup_api_key"
_LEGACY_AUTO_CONFIRMATION_TEXT = "auto_cleanup_confirmation_text"
_LEGACY_ADD_DELETED_TO_IGNORED = "add_deleted_to_ignored"
_LEGACY_INITIAL_RUN_COMPLETED = "server_auto_cleanup_initial_run_completed"


def age_preset_for_days(age_days: int) -> str:
    """Return a stable UI preset or custom for a numeric age."""
    normalized = int(age_days)
    for preset, days in AGE_PRESETS.items():
        if normalized == days:
            return preset
    return AGE_PRESET_CUSTOM


def age_days_from_input(preset: str, custom_days: int | None) -> int:
    """Resolve one selector submission to a numeric source of truth."""
    if preset in AGE_PRESETS:
        return AGE_PRESETS[preset]
    if preset == AGE_PRESET_CUSTOM and custom_days is not None:
        return int(custom_days)
    raise ValueError("A custom cleanup age requires a numeric value")


def reported_device_id_for_player_key(
    devices: Iterable[EmbyDeviceRecord], player_key: str
) -> str | None:
    """Return the exact raw client identity for one known player key."""
    for device in devices:
        if device.player_key == player_key:
            return device.reported_device_id
    return None


def device_is_ignored(
    *,
    player_key: str,
    reported_device_id: str | None,
    ignored_player_keys: Iterable[str],
    ignored_reported_device_ids: Iterable[str],
) -> bool:
    """Apply exact app-specific and device-wide ignore rules."""
    if player_key in {str(value) for value in ignored_player_keys}:
        return True
    if reported_device_id is None:
        return False
    return reported_device_id in {str(value) for value in ignored_reported_device_ids}


def should_expose_device(
    *,
    device_id: str,
    reported_device_id: str | None,
    state: str | None,
    mode: str,
    allowed_ids: Iterable[str],
    ignored_player_keys: Iterable[str],
    ignored_reported_device_ids: Iterable[str],
) -> bool:
    """Return whether a pyemby device should be exposed as an HA entity."""
    if device_is_ignored(
        player_key=device_id,
        reported_device_id=reported_device_id,
        ignored_player_keys=ignored_player_keys,
        ignored_reported_device_ids=ignored_reported_device_ids,
    ):
        return False
    if mode == CLIENT_MODE_ALLOWLIST:
        return device_id in {str(value) for value in allowed_ids}
    if mode == CLIENT_MODE_ACTIVE_ONLY:
        return str(state or "").casefold() in ACTIVE_STATES
    return True


def unique_player_keys(devices: Iterable[EmbyDeviceRecord]) -> list[str]:
    """Return sorted unique pyemby/HA player identities."""
    return sorted({device.player_key for device in devices})


def unique_reported_device_ids(devices: Iterable[EmbyDeviceRecord]) -> list[str]:
    """Return sorted unique raw client identities."""
    return sorted({device.reported_device_id for device in devices})


def device_selector_options(devices: Iterable[EmbyDeviceRecord]) -> dict[str, str]:
    """Return selector options keyed by pyemby/HA player identity."""
    return {device.player_key: device.label for device in devices}


def reported_device_selector_options(devices: Iterable[EmbyDeviceRecord]) -> dict[str, str]:
    """Return one human-readable selector option per raw client identity."""
    options: dict[str, str] = {}
    grouped: dict[str, list[EmbyDeviceRecord]] = {}
    for device in devices:
        grouped.setdefault(device.reported_device_id, []).append(device)
    for reported_id, records in grouped.items():
        names = sorted({record.name for record in records})
        apps = sorted({record.app_name for record in records if record.app_name})
        label = names[0] if names else "Unknown"
        if apps:
            label = f"{label} · {', '.join(apps)}"
        options[reported_id] = label
    return options


def server_device_selector_options(
    devices: Iterable[EmbyDeviceRecord],
) -> dict[str, str]:
    """Return destructive-cleanup options keyed by server record ID."""
    return {device.record_id: device.server_cleanup_label for device in devices}


def registry_cleanup_reason(
    *,
    has_state: bool,
    config_entry_id: str | None,
    target_entry_id: str,
    unique_id: str,
    reported_device_id: str | None,
    ignored_player_keys: Iterable[str],
    ignored_reported_device_ids: Iterable[str],
) -> str | None:
    """Return why an inactive EMBi registry entry is safe to offer for cleanup."""
    if has_state:
        return None
    if config_entry_id is None:
        return "legacy_yaml"
    if config_entry_id != target_entry_id:
        return None
    if device_is_ignored(
        player_key=unique_id,
        reported_device_id=reported_device_id,
        ignored_player_keys=ignored_player_keys,
        ignored_reported_device_ids=ignored_reported_device_ids,
    ):
        return "ignored"
    return "registry_only"


def merge_missing_options(
    options: dict[str, str], configured_ids: Iterable[str], missing_label: str
) -> dict[str, str]:
    """Keep configured IDs selectable when the server temporarily omits them."""
    merged = dict(options)
    for configured_id in configured_ids:
        key = str(configured_id)
        merged.setdefault(key, f"{key} · {missing_label}")
    return merged


def migrate_stable_options(
    options: dict[str, Any], devices: Iterable[EmbyDeviceRecord]
) -> tuple[dict[str, Any], bool]:
    """Migrate rc3 options to the stable identity and safety contract."""
    migrated = dict(options)
    records = list(devices)
    by_record_id = {device.record_id: device for device in records}
    known_player_keys = {device.player_key for device in records}
    known_reported_ids = {device.reported_device_id for device in records}

    allowed: set[str] = set()
    for configured_id in options.get(CONF_ALLOWED_DEVICE_IDS, []):
        value = str(configured_id)
        allowed.add(by_record_id[value].player_key if value in by_record_id else value)
    if CONF_ALLOWED_DEVICE_IDS in options:
        migrated[CONF_ALLOWED_DEVICE_IDS] = sorted(allowed)

    ignored_players = {
        str(value) for value in options.get(CONF_IGNORED_PLAYER_KEYS, []) if value
    }
    ignored_devices = {
        str(value)
        for value in options.get(CONF_IGNORED_REPORTED_DEVICE_IDS, [])
        if value
    }
    unresolved = {
        str(value) for value in options.get(CONF_UNRESOLVED_IGNORED_IDS, []) if value
    }

    for configured_id in options.get(_LEGACY_IGNORED_DEVICE_IDS, []):
        value = str(configured_id)
        if value in known_player_keys:
            ignored_players.add(value)
        elif value in known_reported_ids:
            ignored_devices.add(value)
        elif value in by_record_id:
            ignored_devices.add(by_record_id[value].reported_device_id)
        else:
            unresolved.add(value)

    migrated[CONF_IGNORED_PLAYER_KEYS] = sorted(ignored_players)
    migrated[CONF_IGNORED_REPORTED_DEVICE_IDS] = sorted(ignored_devices)
    migrated[CONF_UNRESOLVED_IGNORED_IDS] = sorted(unresolved)

    for legacy_key in (
        _LEGACY_IGNORED_DEVICE_IDS,
        _LEGACY_CLEANUP_API_KEY,
        _LEGACY_AUTO_CONFIRMATION_TEXT,
        _LEGACY_ADD_DELETED_TO_IGNORED,
        _LEGACY_INITIAL_RUN_COMPLETED,
    ):
        migrated.pop(legacy_key, None)

    return migrated, migrated != options


def migrate_legacy_device_options(
    options: dict[str, Any], devices: Iterable[EmbyDeviceRecord]
) -> tuple[dict[str, Any], bool]:
    """Backward-compatible alias for the stable options migration."""
    return migrate_stable_options(options, devices)
