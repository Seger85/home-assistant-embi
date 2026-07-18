from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any

from homeassistant.helpers import entity_registry as er

from .player_context import (
    GROUP_SHARED,
    GROUP_TECHNICAL,
    GROUP_UNASSIGNED,
    GROUP_UNKNOWN,
    GROUP_USER_PREFIX,
    PlayerCatalogStats,
    PlayerContext,
    build_player_catalog,
    catalog_stats,
    group_player_catalog,
)

_STATUS_DE = {
    "idle": "Noch nicht ausgeführt",
    "running": "Läuft",
    "server_completed": "Serverbereinigung abgeschlossen",
    "registry_pending": "Registry-Prüfung ausstehend",
    "completed": "Abgeschlossen",
    "partial_failure": "Teilweise fehlgeschlagen",
    "failed": "Fehlgeschlagen",
    "interrupted": "Unterbrochen",
    "not_run": "Noch nicht ausgeführt",
    "ready": "Bereit",
    "playing": "Wiedergabe läuft",
    "paused": "Pausiert",
    "disabled": "In Home Assistant deaktiviert",
    "hidden": "In EMBi ausgeblendet",
    "not_reported": "Nicht mehr vom Emby-Server gemeldet",
    "unknown": "Unklar",
}
_STATUS_EN = {
    "idle": "Not run yet",
    "running": "Running",
    "server_completed": "Server cleanup completed",
    "registry_pending": "Registry verification pending",
    "completed": "Completed",
    "partial_failure": "Partially failed",
    "failed": "Failed",
    "interrupted": "Interrupted",
    "not_run": "Not run yet",
    "ready": "Ready",
    "playing": "Playing",
    "paused": "Paused",
    "disabled": "Disabled in Home Assistant",
    "hidden": "Hidden in EMBi",
    "not_reported": "No longer reported by the Emby server",
    "unknown": "Unclear",
}


def registry_entries(hass: Any) -> list[object]:
    return list(er.async_get(hass).entities.values())


async def fresh_catalog(flow: Any) -> tuple[list[PlayerContext], PlayerCatalogStats]:
    records = await flow._devices()
    flow._runtime.devices = records
    players = build_player_catalog(
        records,
        registry_entries=registry_entries(flow.hass),
        states=flow.hass.states,
        entry_id=flow._entry.entry_id,
        options=flow._draft_options,
        pyemby_devices=getattr(flow._runtime.pyemby, "devices", None),
    )
    return players, catalog_stats(players, server_history_records=len(records))


def group_options(players: list[PlayerContext], *, german: bool) -> list[dict[str, str]]:
    grouped = group_player_catalog(players)
    options: list[dict[str, str]] = []
    user_keys = sorted(
        (key for key in grouped if key.startswith(GROUP_USER_PREFIX)),
        key=lambda key: key.removeprefix(GROUP_USER_PREFIX).casefold(),
    )
    for key in user_keys:
        user = key.removeprefix(GROUP_USER_PREFIX)
        count = len(grouped[key])
        options.append({"value": key, "label": f"{user} · {count} Player"})
    labels = {
        GROUP_SHARED: "Gemeinsam genutzt" if german else "Shared devices",
        GROUP_UNASSIGNED: ("Ohne Benutzerzuordnung" if german else "Without user assignment"),
        GROUP_TECHNICAL: "Technische Zugriffe" if german else "Technical access",
        GROUP_UNKNOWN: "Unklare Clients" if german else "Unclear clients",
    }
    for key in (GROUP_SHARED, GROUP_UNASSIGNED, GROUP_TECHNICAL, GROUP_UNKNOWN):
        if key in grouped:
            options.append({"value": key, "label": f"{labels[key]} · {len(grouped[key])}"})
    return options


def _compact_options(players: list[PlayerContext], *, value_getter) -> list[dict[str, str]]:
    base_counts = Counter(player.selector_label for player in players)
    seen: Counter[str] = Counter()
    options: list[dict[str, str]] = []
    for player in players:
        value = value_getter(player)
        if not value:
            continue
        base = player.compact_label(include_user=base_counts[player.selector_label] > 1)
        seen[base] += 1
        label = base
        if base_counts[player.selector_label] > 1 and not player.users:
            if player.last_activity is not None:
                label = f"{base} · {player.last_activity.date().isoformat()}"
            if seen[base] > 1 or any(option["label"] == label for option in options):
                label = f"{label} ({seen[base]})"
        options.append({"value": str(value), "label": label})
    return options


def player_options(players: list[PlayerContext]) -> list[dict[str, str]]:
    return _compact_options(players, value_getter=lambda player: player.player_key)


def entity_options(players: list[PlayerContext]) -> list[dict[str, str]]:
    return _compact_options(players, value_getter=lambda player: player.entity_id)


def player_label_map(players: list[PlayerContext]) -> Mapping[str, str]:
    return {option["value"]: option["label"] for option in player_options(players)}


def render_player_rows(players: list[PlayerContext]) -> str:
    return "\n".join(option["label"] for option in player_options(players)) or "-"


def render_player_details(players: list[PlayerContext], *, german: bool) -> str:
    if not players:
        return "-"
    lines: list[str] = []
    for player in players:
        user = (
            ", ".join(player.users) if player.users else ("Ohne Benutzer" if german else "No user")
        )
        entity = player.entity_id or "-"
        lines.append(
            "\n".join(
                (
                    player.selector_label,
                    f"Home Assistant: {player.ha_name}",
                    f"Entity-ID: {entity}",
                    (f"Benutzer: {user}" if german else f"Users: {user}"),
                    f"Status: {status_label(player.status, german=german)}",
                )
            )
        )
    return "\n\n".join(lines)


def status_label(value: str | None, *, german: bool) -> str:
    key = str(value or "unknown").casefold()
    mapping = _STATUS_DE if german else _STATUS_EN
    return mapping.get(key, mapping["unknown"])


def page_slice[T](items: list[T], page: int, *, page_size: int) -> tuple[list[T], int, int]:
    """Return one bounded page plus normalized page and total-page counts."""
    total_pages = max(1, (len(items) + page_size - 1) // page_size)
    normalized = min(max(1, int(page)), total_pages)
    start = (normalized - 1) * page_size
    return items[start : start + page_size], normalized, total_pages
