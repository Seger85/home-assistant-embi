from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.emby import player_actions
from custom_components.emby.maintenance_registry_evaluate import evaluate_registry_targets
from custom_components.emby.models import PendingRegistryTarget
from custom_components.emby.player_actions import PlayerActionResult
from custom_components.emby.registry_state import state_blocks_registry_removal, state_is_restored


@dataclass
class FakeState:
    attributes: dict = field(default_factory=dict)


@dataclass
class FakeEntry:
    entry_id: str = "entry-target"


@dataclass
class FakeRegistryEntry:
    entity_id: str
    unique_id: str
    domain: str = "media_player"
    platform: str = "emby"
    config_entry_id: str = "entry-target"


class FakeRegistry:
    def __init__(self, entry: FakeRegistryEntry) -> None:
        self.entities = {entry.entity_id: entry}

    def async_get(self, entity_id: str):
        return self.entities.get(entity_id)


class FakeStates:
    def __init__(self, state) -> None:
        self.state = state

    def get(self, _entity_id: str):
        return self.state


def test_restored_state_does_not_block_exact_registry_cleanup() -> None:
    restored = FakeState({"restored": True})
    live = FakeState({})
    assert state_is_restored(restored) is True
    assert state_blocks_registry_removal(restored) is False
    assert state_blocks_registry_removal(live) is True
    assert state_blocks_registry_removal(None) is False


def test_registry_followup_accepts_stale_restored_state() -> None:
    entity = FakeRegistryEntry("media_player.stale", "player-key")
    evaluation = evaluate_registry_targets(
        registry=FakeRegistry(entity),
        states=FakeStates(FakeState({"restored": True})),
        entry=FakeEntry(),
        current_devices=[],
        targets={"player-key": PendingRegistryTarget("player-key", entity.entity_id)},
    )
    assert evaluation.result.matched == 1
    assert evaluation.result.state_still_present == 0
    assert evaluation.entity_ids_to_remove == (entity.entity_id,)


def test_registry_followup_still_protects_live_state() -> None:
    entity = FakeRegistryEntry("media_player.live", "player-key")
    evaluation = evaluate_registry_targets(
        registry=FakeRegistry(entity),
        states=FakeStates(FakeState()),
        entry=FakeEntry(),
        current_devices=[],
        targets={"player-key": PendingRegistryTarget("player-key", entity.entity_id)},
    )
    assert evaluation.result.state_still_present == 1
    assert evaluation.entity_ids_to_remove == ()


@pytest.mark.asyncio
async def test_startup_reconciliation_targets_only_invisible_registered_players(
    monkeypatch,
) -> None:
    visible = SimpleNamespace(
        player_key="visible", registry_present=True, visible_in_embi=True, playback="non_playing"
    )
    hidden = SimpleNamespace(
        player_key="hidden", registry_present=True, visible_in_embi=False, playback="non_playing"
    )
    missing = SimpleNamespace(
        player_key="missing", registry_present=False, visible_in_embi=False, playback="non_playing"
    )
    monkeypatch.setattr(
        player_actions, "_fresh_catalog", AsyncMock(return_value=[visible, hidden, missing])
    )
    remove = AsyncMock(return_value=PlayerActionResult("remove", 1, (), (), ()))
    monkeypatch.setattr(player_actions, "async_remove_hidden_player_entities", remove)
    result = await player_actions.async_reconcile_invisible_player_entities(object(), object())
    assert result.requested == 1
    args, kwargs = remove.await_args
    assert list(args[2]) == ["hidden"]
    assert kwargs["prevalidated_non_playing_keys"] == {"hidden"}
