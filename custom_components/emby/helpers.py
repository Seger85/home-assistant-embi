from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .api import EmbyDeviceRecord
from .const import AGE_PRESET_CUSTOM, AGE_PRESETS


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
        key=lambda item: (
            item.last_activity_datetime is None,
            item.last_activity_datetime.timestamp()
            if item.last_activity_datetime is not None
            else 0,
            base_by_id[item.record_id].casefold(),
            item.record_id,
        ),
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
