from __future__ import annotations

from collections.abc import Iterable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from . import player_actions
from .maintenance_common import _async_save_state
from .models import EmbiRuntimeData, MaintenanceActionSummary
from .player_actions import PlayerActionItem, PlayerActionResult


async def _async_record_reconciliation(
    hass: HomeAssistant,
    entry: ConfigEntry,
    result: PlayerActionResult,
    *,
    started_at: str,
    runtime: EmbiRuntimeData | None = None,
) -> None:
    runtime = runtime or getattr(entry, "runtime_data", None)
    if runtime is None or not runtime.is_current(entry):
        return
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
    await _async_save_state(hass, entry, runtime=runtime)


async def async_reconcile_player_visibility(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    requested_keys: Iterable[str] | None = None,
) -> PlayerActionResult:
    """Reconcile disallowed exact EMBi entities on every setup and visibility change."""
    runtime = getattr(entry, "runtime_data", None)
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
        await _async_record_reconciliation(
            hass, entry, result, started_at=started_at, runtime=runtime
        )
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
        await _async_record_reconciliation(
            hass, entry, result, started_at=started_at, runtime=runtime
        )
        return result

    return await player_actions.async_remove_hidden_player_entities(
        hass,
        entry,
        (player.player_key for player in invisible),
        action="reconcile",
    )
