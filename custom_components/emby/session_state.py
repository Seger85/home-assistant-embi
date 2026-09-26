"""Exact session identity and conservative activity decisions shared by all callers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

ACTIVE = frozenset({"playing", "paused"})
INACTIVE = "non_playing"
UNKNOWN = "unknown"


def session_key(session: Mapping[str, Any]) -> str | None:
    """Use the same complete client/app identity as established EMBi players."""
    device = session.get("DeviceId")
    client = session.get("Client")
    if not isinstance(device, str) or not device.strip():
        return None
    if not isinstance(client, str) or not client.strip():
        return None
    return f"{device}.{client}"


def session_activity(session: Mapping[str, Any]) -> str:
    """An incomplete playback description is uncertainty, never permission to delete."""
    item = session.get("NowPlayingItem")
    if item is None:
        return INACTIVE
    if not isinstance(item, Mapping) or not item.get("Id"):
        return UNKNOWN
    state = session.get("PlayState")
    if not isinstance(state, Mapping) or not isinstance(state.get("IsPaused"), bool):
        return UNKNOWN
    return "paused" if state["IsPaused"] else "playing"


def aggregate_activity(values: Iterable[str | None]) -> str:
    """Any active observation wins, independent of input order."""
    states = {str(value or "").casefold() for value in values}
    if "playing" in states:
        return "playing"
    if "paused" in states:
        return "paused"
    if states & {"", "unknown", "unavailable"}:
        return UNKNOWN
    if states and states <= {INACTIVE, "idle", "off", "standby"}:
        return INACTIVE
    return UNKNOWN


def validate_sessions(data: Any) -> list[dict[str, Any]]:
    """Require a complete, identifiable inventory; playback quality is per client."""
    if not isinstance(data, list) or any(
        not isinstance(item, dict) or session_key(item) is None for item in data
    ):
        raise ValueError("Invalid session inventory")
    return data


def player_activity(sessions: Iterable[Mapping[str, Any]], player_key: str) -> str:
    """Absence is inactive only when the caller supplied a validated fresh snapshot."""
    matches = [session_activity(item) for item in sessions if session_key(item) == player_key]
    return aggregate_activity(matches) if matches else INACTIVE


def record_activity(
    sessions: Iterable[Mapping[str, Any]], device_id: str, app_name: str | None
) -> str:
    """Missing app metadata cannot accidentally exempt another app on that device."""
    matches = [
        session_activity(item)
        for item in sessions
        if item.get("DeviceId") == device_id and (not app_name or item.get("Client") == app_name)
    ]
    return aggregate_activity(matches) if matches else INACTIVE
