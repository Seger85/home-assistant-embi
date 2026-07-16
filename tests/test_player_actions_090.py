from __future__ import annotations

from pathlib import Path

from custom_components.emby.models import MaintenanceActionSummary, MaintenanceState
from custom_components.emby.player_action_common import (
    PlayerActionItem,
    PlayerActionResult,
)

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


def source(name: str) -> str:
    return (COMPONENT / name).read_text(encoding="utf-8")


def test_player_action_result_distinguishes_success_partial_and_failure() -> None:
    success = PlayerActionResult(
        "remove",
        1,
        (PlayerActionItem("media_player.one", "player-one", "One", "removed"),),
        (),
        (),
    )
    partial = PlayerActionResult(
        "remove",
        2,
        (PlayerActionItem("media_player.one", "player-one", "One", "removed"),),
        (
            PlayerActionItem(
                "media_player.two", "player-two", "Two", "protected", "paused"
            ),
        ),
        (),
    )
    failure = PlayerActionResult(
        "restore",
        1,
        (),
        (),
        (PlayerActionItem(None, "player-one", "One", "failed", "verification_failed"),),
    )

    assert success.status == "completed"
    assert partial.status == "partial"
    assert failure.status == "failed"


def test_persistent_action_summary_contains_only_aggregate_fields() -> None:
    summary = MaintenanceActionSummary(
        action="remove",
        status="partial",
        requested=3,
        succeeded=1,
        protected=1,
        failed=1,
        reason_codes=("paused", "verification_failed"),
    )
    data = MaintenanceState(last_player_action=summary).as_dict()
    serialized = repr(data)

    assert data["last_player_action"]["requested"] == 3
    assert data["last_player_action"]["protected"] == 1
    assert "record_id" not in serialized
    assert "reported_device_id" not in serialized
    assert "player_key" not in serialized
    assert "entity_id" not in serialized
    assert "user_name" not in serialized


def test_removal_orders_hidden_rule_before_registry_remove_and_verifies_reload() -> (
    None
):
    remove_source = source("player_remove.py")

    hidden_position = remove_source.index("options[CONF_HIDDEN_EXACT_PLAYERS]")
    update_position = remove_source.index("update_options_and_reload")
    registry_remove_position = remove_source.index("registry.async_remove")
    second_reload_position = remove_source.rindex("async_reload")
    verification_position = remove_source.index("still_registered")

    assert hidden_position < update_position < registry_remove_position
    assert registry_remove_position < second_reload_position < verification_position
    assert "ACTIVE_PLAYBACK_STATES" in remove_source
    assert "state_still_present" in remove_source
    assert "owned_exact" in remove_source


def test_restore_removes_only_exact_rule_and_verifies_resulting_entity() -> None:
    actions_source = source("player_actions.py")

    assert "hidden.discard(key)" in actions_source
    assert "update_options_and_reload" in actions_source
    assert "owned_exact(entity, current_entry, key)" in actions_source
    assert "verification_failed" in actions_source
    assert "async_delete_device" not in actions_source


def test_home_assistant_removal_does_not_call_server_delete() -> None:
    combined = source("player_remove.py") + source("player_actions.py")

    assert "async_delete_device" not in combined
    assert '"/Devices"' not in combined


def test_playing_and_paused_are_rechecked_by_the_destructive_path() -> None:
    remove_source = source("player_remove.py")
    context_source = source("player_context.py")

    assert "context.playback in ACTIVE_PLAYBACK_STATES" in remove_source
    assert (
        "ACTIVE_PLAYBACK_STATES = {PLAYBACK_PLAYING, PLAYBACK_PAUSED}" in context_source
    )
