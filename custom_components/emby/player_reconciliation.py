from __future__ import annotations

from collections.abc import Iterable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import player_actions
from .player_actions import PlayerActionResult
from .player_context import ACTIVE_PLAYBACK_STATES, PLAYBACK_UNKNOWN
from .registry_state import (
    state_can_be_removed_after_visibility_commit,
    state_is_restored,
)


async def async_reconcile_player_visibility(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    requested_keys: Iterable[str] | None = None,
) -> PlayerActionResult:
    """Reconcile disallowed exact EMBi entities under the 1.0 lifecycle contract."""
    catalog = await player_actions._fresh_catalog(hass, entry)
    requested = {str(value) for value in requested_keys or ()}
    invisible = [
        player
        for player in catalog
        if player.registry_present
        and not player.visible_in_embi
        and (not requested or player.player_key in requested)
    ]
    if not invisible:
        return PlayerActionResult("reconcile", 0, (), (), ())

    prevalidated = {
        player.player_key
        for player in invisible
        if player.playback not in ACTIVE_PLAYBACK_STATES
        and (
            player.playback != PLAYBACK_UNKNOWN
            or (
                bool(player.entity_id)
                and (
                    state_is_restored(hass.states.get(player.entity_id))
                    or state_can_be_removed_after_visibility_commit(
                        hass.states.get(player.entity_id)
                    )
                )
            )
        )
    }
    return await player_actions.async_remove_hidden_player_entities(
        hass,
        entry,
        (player.player_key for player in invisible),
        prevalidated_non_playing_keys=prevalidated,
        action="reconcile",
    )


async def async_reconcile_invisible_player_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> PlayerActionResult:
    """Backward-compatible name for startup callers."""
    return await async_reconcile_player_visibility(hass, entry)
