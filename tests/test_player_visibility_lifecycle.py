from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from custom_components.emby import player_reconciliation
from custom_components.emby.const import (
    CONF_OPTIONS_SCHEMA_VERSION,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_USER_MASTER_VISIBILITY,
    OPTIONS_SCHEMA_VERSION,
    REGISTRY_RECONCILIATION_VERSION,
)
from custom_components.emby.legacy_migration import migrate_options
from custom_components.emby.options_devices import _player_toggle_fields, _sort_group_players
from custom_components.emby.player_actions import PlayerActionResult
from custom_components.emby.registry_state import (
    state_blocks_registry_removal,
    state_can_be_removed_after_visibility_commit,
)


def player(name: str, activity: datetime | None):
    return SimpleNamespace(selector_label=name, last_activity=activity, player_key=name)


def test_player_labels_are_single_line_oldest_first_unknown_last() -> None:
    newest = player("TV · Emby", datetime(2026, 7, 19, 10, tzinfo=UTC))
    oldest = player("Tablet · Emby", datetime(2026, 7, 18, 10, tzinfo=UTC))
    unknown = player("Phone · Emby", None)
    players = _sort_group_players([newest, unknown, oldest])
    assert players == [oldest, newest, unknown]
    labels = [label for label, _ in _player_toggle_fields(players, german=True, time_zone="UTC")]
    assert labels[0] == "Tablet · Emby · zuletzt 18.07.2026 10:00"
    assert labels[-1] == "Phone · Emby · zuletzt unbekannt"
    assert all("\n" not in label and "media_player." not in label for label in labels)


@pytest.mark.parametrize("state", ["idle", "off", "standby", "unavailable"])
def test_definitively_inactive_states_can_be_removed(state: str) -> None:
    value = SimpleNamespace(state=state, attributes={})
    assert state_can_be_removed_after_visibility_commit(value)
    assert not state_blocks_registry_removal(value)


def test_live_playback_states_remain_protected() -> None:
    for state in ("playing", "paused"):
        value = SimpleNamespace(state=state, attributes={})
        assert not state_can_be_removed_after_visibility_commit(value)
        assert state_blocks_registry_removal(value)


def test_stale_restored_state_is_removable() -> None:
    value = SimpleNamespace(state="unavailable", attributes={"restored": True})
    assert state_can_be_removed_after_visibility_commit(value)
    assert not state_blocks_registry_removal(value)


@pytest.mark.asyncio
async def test_reconciliation_prevalidates_inactive_and_restored_but_not_playback(
    monkeypatch,
) -> None:
    players = [
        SimpleNamespace(
            player_key="inactive",
            entity_id="media_player.inactive",
            registry_present=True,
            visible_in_embi=False,
            playback="non_playing",
        ),
        SimpleNamespace(
            player_key="restored",
            entity_id="media_player.restored",
            registry_present=True,
            visible_in_embi=False,
            playback="unknown",
        ),
        SimpleNamespace(
            player_key="unclear",
            entity_id="media_player.unclear",
            registry_present=True,
            visible_in_embi=False,
            playback="unknown",
        ),
        SimpleNamespace(
            player_key="playing",
            entity_id="media_player.playing",
            registry_present=True,
            visible_in_embi=False,
            playback="playing",
        ),
        SimpleNamespace(
            player_key="paused",
            entity_id="media_player.paused",
            registry_present=True,
            visible_in_embi=False,
            playback="paused",
        ),
    ]
    monkeypatch.setattr(
        player_reconciliation.player_actions,
        "_fresh_catalog",
        AsyncMock(return_value=players),
    )
    remove = AsyncMock(return_value=PlayerActionResult("reconcile", 5, (), (), ()))
    monkeypatch.setattr(
        player_reconciliation.player_actions,
        "async_remove_hidden_player_entities",
        remove,
    )
    states = {
        "media_player.restored": SimpleNamespace(
            state="unavailable", attributes={"restored": True}
        ),
        "media_player.unclear": SimpleNamespace(state="unknown", attributes={}),
    }
    hass = SimpleNamespace(states=SimpleNamespace(get=lambda entity_id: states.get(entity_id)))
    await player_reconciliation.async_reconcile_player_visibility(hass, object())
    _, kwargs = remove.await_args
    assert kwargs["prevalidated_non_playing_keys"] == {"inactive", "restored"}
    assert REGISTRY_RECONCILIATION_VERSION == 3


def test_published_options_upgrade_is_idempotent_and_preserves_master() -> None:
    source = {
        CONF_OPTIONS_SCHEMA_VERSION: 3,
        CONF_USER_MASTER_VISIBILITY: {"Alex": True, "Sam": False},
        CONF_TECHNICAL_ACCESS_VISIBILITY: True,
        "Alex": False,
        "Sam": True,
    }
    migrated, changed = migrate_options(source, [])
    assert changed
    assert migrated[CONF_OPTIONS_SCHEMA_VERSION] == OPTIONS_SCHEMA_VERSION == 4
    assert migrated[CONF_USER_MASTER_VISIBILITY] == {"Alex": True, "Sam": False}
    assert migrated[CONF_TECHNICAL_ACCESS_VISIBILITY] is True
    assert "Alex" not in migrated and "Sam" not in migrated
    repeated, changed_again = migrate_options(migrated, [])
    assert repeated == migrated
    assert changed_again is False


def test_runtime_sources_enforce_master_independence_and_named_blockers() -> None:
    component = Path("custom_components/emby")
    devices = (component / "options_devices.py").read_text(encoding="utf-8")
    flow = (component / "options_flow.py").read_text(encoding="utf-8")
    media = (component / "media_player.py").read_text(encoding="utf-8")
    actions = (component / "player_actions.py").read_text(encoding="utf-8")
    assert "include_technical=requested_technical" in devices
    assert "CONF_TECHNICAL_ACCESS_VISIBILITY] = any_visible" not in devices
    assert "playback_protected_named" in devices
    assert "blocked_players" in devices
    assert "player.playback == PLAYBACK_UNKNOWN" not in devices
    assert "CONF_TECHNICAL_ACCESS_VISIBILITY] = True" not in flow
    assert "async_remove(force_remove=True)" in media
    assert '"GET", "/Sessions"' in actions
