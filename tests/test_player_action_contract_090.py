from __future__ import annotations

from pathlib import Path

from custom_components.emby.models import MaintenanceActionSummary, MaintenanceState
from custom_components.emby.player_action_common import PlayerActionItem, PlayerActionResult

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


def source(name: str) -> str:
    return (COMPONENT / name).read_text(encoding="utf-8")


def test_player_action_result_statuses() -> None:
    completed = PlayerActionResult(
        "action",
        1,
        (PlayerActionItem("media_player.one", "key-one", "One", "done"),),
        (),
        (),
    )
    partial = PlayerActionResult(
        "action",
        2,
        (PlayerActionItem("media_player.one", "key-one", "One", "done"),),
        (PlayerActionItem("media_player.two", "key-two", "Two", "protected", "paused"),),
        (),
    )
    failed = PlayerActionResult(
        "action",
        1,
        (),
        (),
        (PlayerActionItem(None, "key-one", "One", "failed", "verification_failed"),),
    )

    assert completed.status == "completed"
    assert partial.status == "partial"
    assert failed.status == "failed"


def test_persistent_action_summary_is_aggregate_only() -> None:
    summary = MaintenanceActionSummary(
        action="action",
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
    for private_field in (
        "record_id",
        "reported_device_id",
        "player_key",
        "entity_id",
        "user_name",
    ):
        assert private_field not in serialized


def test_hidden_rule_precedes_reload_and_success_verification() -> None:
    actions_source = source("player_actions.py")

    hidden_position = actions_source.index("options[CONF_HIDDEN_EXACT_PLAYERS]")
    update_position = actions_source.index("_update_options_and_reload(", hidden_position)
    verification_position = actions_source.index("still_registered", update_position)
    success_position = actions_source.index('"removed"', verification_position)

    assert hidden_position < update_position < verification_position < success_position
    assert "state_still_present" in actions_source
    assert "owned_exact" in actions_source


def test_restore_and_playback_safety_contract() -> None:
    actions_source = source("player_actions.py")
    context_source = source("player_context.py")

    assert "hidden.discard(key)" in actions_source
    assert "owned_exact(entity, current_entry, key)" in actions_source
    assert "verification_failed" in actions_source
    assert "context.playback in ACTIVE_PLAYBACK_STATES" in actions_source
    assert "ACTIVE_PLAYBACK_STATES = {PLAYBACK_PLAYING, PLAYBACK_PAUSED}" in context_source
