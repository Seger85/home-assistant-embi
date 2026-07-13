from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .api import EmbyDeviceRecord
from .const import (
    CLIENT_MODE_ACTIVE_ONLY,
    CLIENT_MODE_ALLOWLIST,
    CONF_ALLOWED_DEVICE_IDS,
    CONF_IGNORED_DEVICE_IDS,
)

ACTIVE_STATES = {"playing", "paused"}


def base_device_id(device_id: str) -> str:
    """Return the raw client ID from a pyemby composite key."""
    return str(device_id).split(".", 1)[0]


def identifier_matches(device_id: str, configured_ids: Iterable[str]) -> bool:
    """Match exact pyemby keys and raw client IDs for durable filter rules."""
    configured = {str(value) for value in configured_ids}
    return device_id in configured or base_device_id(device_id) in configured


def should_expose_device(
    *,
    device_id: str,
    state: str | None,
    mode: str,
    allowed_ids: Iterable[str],
    ignored_ids: Iterable[str],
) -> bool:
    """Return whether a pyemby device should be exposed as an HA entity."""
    if identifier_matches(device_id, ignored_ids):
        return False
    if mode == CLIENT_MODE_ALLOWLIST:
        return identifier_matches(device_id, allowed_ids)
    if mode == CLIENT_MODE_ACTIVE_ONLY:
        return str(state or "").casefold() in ACTIVE_STATES
    return True


def device_selector_options(devices: Iterable[EmbyDeviceRecord]) -> dict[str, str]:
    """Return selector options keyed by pyemby/HA player identity."""
    return {device.player_key: device.label for device in devices}


def server_device_selector_options(
    devices: Iterable[EmbyDeviceRecord],
) -> dict[str, str]:
    """Return destructive-cleanup options keyed by server record ID."""
    return {device.record_id: device.label for device in devices}


def merge_missing_options(
    options: dict[str, str], configured_ids: Iterable[str], missing_label: str
) -> dict[str, str]:
    """Keep configured IDs selectable when the server temporarily omits them."""
    merged = dict(options)
    for configured_id in configured_ids:
        key = str(configured_id)
        merged.setdefault(key, f"{key} · {missing_label}")
    return merged


def migrate_legacy_device_options(
    options: dict[str, Any], devices: Iterable[EmbyDeviceRecord]
) -> tuple[dict[str, Any], bool]:
    """Migrate 0.2 numeric /Devices record IDs to stable client identities."""
    migrated = dict(options)
    by_record_id = {device.record_id: device for device in devices}
    changed = False

    allowed = []
    for configured_id in options.get(CONF_ALLOWED_DEVICE_IDS, []):
        value = str(configured_id)
        replacement = by_record_id[value].player_key if value in by_record_id else value
        allowed.append(replacement)
        changed |= replacement != value

    ignored = []
    for configured_id in options.get(CONF_IGNORED_DEVICE_IDS, []):
        value = str(configured_id)
        replacement = by_record_id[value].reported_device_id if value in by_record_id else value
        ignored.append(replacement)
        changed |= replacement != value

    if CONF_ALLOWED_DEVICE_IDS in options:
        migrated[CONF_ALLOWED_DEVICE_IDS] = sorted(set(allowed))
    if CONF_IGNORED_DEVICE_IDS in options:
        migrated[CONF_IGNORED_DEVICE_IDS] = sorted(set(ignored))

    return migrated, changed
