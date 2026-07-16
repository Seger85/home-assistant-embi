from __future__ import annotations

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
        options.append(
            {
                "value": key,
                "label": f"{user} · {len(grouped[key])} Player",
            }
        )
    labels = {
        GROUP_SHARED: "Gemeinsam genutzt" if german else "Shared devices",
        GROUP_UNASSIGNED: (
            "Ohne Benutzerzuordnung" if german else "Without user assignment"
        ),
        GROUP_TECHNICAL: "Technische Zugriffe" if german else "Technical access",
        GROUP_UNKNOWN: "Unklare Clients" if german else "Unknown clients",
    }
    for key in (GROUP_SHARED, GROUP_UNASSIGNED, GROUP_TECHNICAL, GROUP_UNKNOWN):
        if key in grouped:
            options.append(
                {
                    "value": key,
                    "label": f"{labels[key]} · {len(grouped[key])}",
                }
            )
    return options


def player_options(players: list[PlayerContext]) -> list[dict[str, str]]:
    return [
        {"value": player.player_key, "label": player.selector_label}
        for player in players
    ]


def entity_options(players: list[PlayerContext]) -> list[dict[str, str]]:
    return [
        {"value": player.entity_id, "label": player.selector_label}
        for player in players
        if player.entity_id
    ]


def player_label_map(players: list[PlayerContext]) -> Mapping[str, str]:
    return {player.player_key: player.selector_label for player in players}


def render_player_rows(players: list[PlayerContext]) -> str:
    return "\n\n".join(player.selector_label for player in players) or "-"
