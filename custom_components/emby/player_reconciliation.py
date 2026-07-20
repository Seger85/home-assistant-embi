from __future__ import annotations

from collections.abc import Iterable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from . import player_actions
from .maintenance_common import _async_save_state
from .models import EmbiRuntimeData, MaintenanceActionSummary
from .player_actions import PlayerActionItem, PlayerActionResult
from .player_context import ACTIVE_PLAYBACK_STATES, PLAYBACK_UNKNOWN
from .registry_state import (
    state_can_be_removed_after_visibility_commit,
    state_is_restored,
)


async def _async_record_reconciliation(
    hass: HomeAssistant,
    entry: ConfigEntry,
    result: PlayerActionResult,
    *,
    started_at: str,
) -> None:
    runtime: EmbiRuntimeData = entry.runtime_data
    runtime.maintenance_state.last_player_action = MaintenanceActionSummary(
        action="reconcile",
        status=result.status,
        started_at=started_at,
        completed_at=dt_util.utcnow().isoformat(),
        requested=result.requested,
        succeeded=len(result.succeeded),
        protected=len(result.protected),
        failed=len(result.failed),
        reason_codes=tuple(
            sorted({item.reason for item in (*result.protected, *result.failed) if item.reason})
        ),
    )
    await _async_save_state(hass, entry)


async def async_reconcile_player_visibility(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    requested_keys: Iterable[str] | None = None,
) -> PlayerActionResult:
    """Reconcile disallowed exact EMBi entities on every setup and visibility change."""
    started_at = dt_util.utcnow().isoformat()
    try:
        catalog = await player_actions._fresh_catalog(hass, entry)
    except Exception:
        result = PlayerActionResult(
            "reconcile",
            0,
            (),
            (),
            (
                PlayerActionItem(
                    None,
                    "",
                    "Emby player",
                    "failed",
                    "refresh_failed",
                ),
            ),
        )
        await _async_record_reconciliation(hass, entry, result, started_at=started_at)
        return result

    requested = {str(value) for value in requested_keys or ()}
    invisible = [
        player
        for player in catalog
        if player.registry_present
        and not player.visible_in_embi
        and (not requested or player.player_key in requested)
    ]
    if not invisible:
        result = PlayerActionResult("reconcile", 0, (), (), ())
        await _async_record_reconciliation(hass, entry, result, started_at=started_at)
        return result

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
