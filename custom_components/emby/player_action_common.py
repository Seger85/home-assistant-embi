from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .maintenance_common import _async_save_state
from .models import EmbiRuntimeData, MaintenanceActionSummary
from .player_context import PlayerContext, build_player_catalog


@dataclass(frozen=True, slots=True)
class PlayerActionItem:
    entity_id: str | None
    player_key: str
    friendly_name: str
    status: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class PlayerActionResult:
    action: str
    requested: int
    succeeded: tuple[PlayerActionItem, ...]
    protected: tuple[PlayerActionItem, ...]
    failed: tuple[PlayerActionItem, ...]

    @property
    def status(self) -> str:
        if self.failed or self.protected:
            return "partial" if self.succeeded else "failed"
        return "completed"


def find_context(
    contexts: Iterable[PlayerContext],
    *,
    entity_id: str | None = None,
    player_key: str | None = None,
) -> PlayerContext | None:
    for context in contexts:
        if entity_id is not None and context.entity_id == entity_id:
            return context
        if player_key is not None and context.player_key == player_key:
            return context
    return None


def owned_exact(entity: object | None, entry: ConfigEntry, player_key: str) -> bool:
    return bool(
        entity is not None
        and getattr(entity, "domain", None) == "media_player"
        and getattr(entity, "platform", None) == DOMAIN
        and getattr(entity, "config_entry_id", None) == entry.entry_id
        and str(getattr(entity, "unique_id", "")) == player_key
    )


async def fresh_catalog(hass: HomeAssistant, entry: ConfigEntry) -> list[PlayerContext]:
    runtime: EmbiRuntimeData = entry.runtime_data
    records = await runtime.api_client.async_get_devices()
    runtime.devices = records
    registry = er.async_get(hass)
    return build_player_catalog(
        records,
        registry_entries=registry.entities.values(),
        states=hass.states,
        entry_id=entry.entry_id,
        options=entry.options,
        pyemby_devices=getattr(runtime.pyemby, "devices", None),
    )


async def update_options_and_reload(hass: HomeAssistant, entry: ConfigEntry, options: dict) -> bool:
    runtime: EmbiRuntimeData = entry.runtime_data
    runtime.suppress_update_listener = True
    try:
        hass.config_entries.async_update_entry(entry, options=options)
        blocker = getattr(hass, "async_block_till_done", None)
        if blocker is not None:
            await blocker()
    finally:
        runtime.suppress_update_listener = False
    return bool(await hass.config_entries.async_reload(entry.entry_id))


async def record_action(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    action: str,
    started_at: str,
    result: PlayerActionResult,
) -> None:
    runtime: EmbiRuntimeData = entry.runtime_data
    summary = MaintenanceActionSummary(
        action=action,
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
    if action == "restore":
        runtime.maintenance_state.last_restore = summary
    else:
        runtime.maintenance_state.last_player_action = summary
    await _async_save_state(hass, entry)
