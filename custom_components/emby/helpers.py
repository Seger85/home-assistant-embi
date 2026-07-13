from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .const import CLIENT_MODE_ACTIVE_ONLY, CLIENT_MODE_ALLOWLIST

ACTIVE_STATES = {"playing", "paused"}


def base_device_id(device_id: str) -> str:
    """Return the raw Emby device ID from a pyemby composite key."""
    return str(device_id).split(".", 1)[0]


def identifier_matches(device_id: str, configured_ids: Iterable[str]) -> bool:
    """Match exact pyemby keys and raw Emby IDs for durable ignore rules."""
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
    if identifier_matches(device_id, ignored_ids):
        return False
    if mode == CLIENT_MODE_ALLOWLIST:
        return identifier_matches(device_id, allowed_ids)
    if mode == CLIENT_MODE_ACTIVE_ONLY:
        return str(state or "").casefold() in ACTIVE_STATES
    return True


def device_selector_options(devices: Iterable[Any]) -> dict[str, str]:
    """Options for HA player filtering; keys match entity unique IDs."""
    return {device.player_key: device.label for device in devices}


def server_device_selector_options(devices: Iterable[Any]) -> dict[str, str]:
    """Options for destructive Emby server cleanup; keys are raw IDs."""
    return {device.id: device.label for device in devices}


def merge_missing_options(
    options: dict[str, str], configured_ids: Iterable[str], missing_label: str
) -> dict[str, str]:
    """Keep previously configured IDs selectable even when the server omits them."""
    merged = dict(options)
    for configured_id in configured_ids:
        key = str(configured_id)
        merged.setdefault(key, f"{key} · {missing_label}")
    return merged
