from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .player_actions import (
    PlayerActionResult,
    _fresh_catalog,
    async_remove_hidden_player_entities,
)
from .player_context import ACTIVE_PLAYBACK_STATES, PLAYBACK_UNKNOWN
from .registry_state import state_is_restored


async def async_reconcile_invisible_player_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> PlayerActionResult:
    """Reconcile hidden stale-restored players under contract version 2."""
    catalog = await _fresh_catalog(hass, entry)
    invisible = [
        player for player in catalog if player.registry_present and not player.visible_in_embi
    ]
    if not invisible:
        return PlayerActionResult("reconcile", 0, (), (), ())
    prevalidated = {
        player.player_key
        for player in invisible
        if player.playback not in ACTIVE_PLAYBACK_STATES
        and (
            player.playback != PLAYBACK_UNKNOWN
            or (bool(player.entity_id) and state_is_restored(hass.states.get(player.entity_id)))
        )
    }
    return await async_remove_hidden_player_entities(
        hass,
        entry,
        (player.player_key for player in invisible),
        prevalidated_non_playing_keys=prevalidated,
    )
