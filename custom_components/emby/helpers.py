from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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


def legacy_initial_run_completed(options: dict[str, Any]) -> bool:
    """Return the rc3 completion marker before stable migration removes it."""
    return bool(options.get(_LEGACY_INITIAL_RUN_COMPLETED, False))


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


def _display_zone(time_zone: str) -> ZoneInfo:
    try:
        return ZoneInfo(time_zone)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _server_record_base_label(
    device: EmbyDeviceRecord,
    *,
    time_zone: str,
    german: bool,
) -> str:
    app = device.app_name or ("Unbekannte App" if german else "Unknown app")
    user = device.last_user_name or ("Ohne Benutzer" if german else "No user")
    activity = device.last_activity_datetime
    if activity is None:
        date_label = "unbekannt" if german else "unknown"
    else:
        local = activity.astimezone(_display_zone(time_zone))
        date_label = local.strftime("%d.%m.%Y" if german else "%Y-%m-%d")
    last_label = f"zuletzt {date_label}" if german else f"last active {date_label}"
    return f"{device.name} · {app} · {user} · {last_label}"


def server_device_selector_options(
    devices: Iterable[EmbyDeviceRecord],
    *,
    time_zone: str,
    german: bool,
) -> dict[str, str]:
    """Return stable mobile-safe options without versions, UTC or internal IDs."""
    records = list(devices)
    base_by_id = {
        device.record_id: _server_record_base_label(
            device,
            time_zone=time_zone,
            german=german,
        )
        for device in records
    }
    counts = Counter(base_by_id.values())
    ordinals: Counter[str] = Counter()
    options: dict[str, str] = {}
    for device in sorted(
        records,
        key=lambda item: (base_by_id[item.record_id].casefold(), item.record_id),
    ):
        base = base_by_id[device.record_id]
        ordinals[base] += 1
        label = base
        if counts[base] > 1:
            suffix = (
                f"Eintrag {ordinals[base]}/{counts[base]}"
                if german
                else f"record {ordinals[base]}/{counts[base]}"
            )
            label = f"{base} · {suffix}"
        options[device.record_id] = label
    return options


def server_device_confirmation_details(
    devices: Iterable[EmbyDeviceRecord],
    *,
    time_zone: str,
    german: bool,
) -> str:
    """Render full selected-record details only on the confirmation page."""
    zone = _display_zone(time_zone)
    lines: list[str] = []
    for device in sorted(devices, key=lambda item: (item.name.casefold(), item.record_id)):
        app = device.app_name or ("Unbekannte App" if german else "Unknown app")
        if device.app_version:
            app = f"{app} {device.app_version}"
        user = device.last_user_name or ("Ohne Benutzer" if german else "No user")
        activity = device.last_activity_datetime
        timestamp = (
            activity.astimezone(zone).strftime("%d.%m.%Y %H:%M:%S %Z")
            if activity is not None
            else ("Unbekannt" if german else "Unknown")
        )
        lines.append(
            " · ".join(
                (
                    device.name,
                    app,
                    user,
                    timestamp,
                    f"Record {device.short_record_id}",
                )
            )
        )
    return "\n".join(lines) or "-"


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
    by_record_id: dict[str, list[EmbyDeviceRecord]] = {}
    for device in records:
        by_record_id.setdefault(device.record_id, []).append(device)
    known_player_keys = {device.player_key for device in records}
    known_reported_ids = {device.reported_device_id for device in records}

    allowed: set[str] = set()
    for configured_id in options.get(CONF_ALLOWED_DEVICE_IDS, []):
        value = str(configured_id)
        matches = by_record_id.get(value, [])
        allowed.add(matches[0].player_key if len(matches) == 1 else value)
    if CONF_ALLOWED_DEVICE_IDS in options:
        migrated[CONF_ALLOWED_DEVICE_IDS] = sorted(allowed)

    ignored_players = {str(value) for value in options.get(CONF_IGNORED_PLAYER_KEYS, []) if value}
    ignored_devices = {
        str(value) for value in options.get(CONF_IGNORED_REPORTED_DEVICE_IDS, []) if value
    }
    unresolved = {str(value) for value in options.get(CONF_UNRESOLVED_IGNORED_IDS, []) if value}

    for configured_id in options.get(_LEGACY_IGNORED_DEVICE_IDS, []):
        value = str(configured_id)
        if value in known_player_keys:
            ignored_players.add(value)
        elif value in known_reported_ids:
            ignored_devices.add(value)
        elif len(by_record_id.get(value, [])) == 1:
            ignored_devices.add(by_record_id[value][0].reported_device_id)
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
