from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


def source(name: str) -> str:
    return (COMPONENT / name).read_text(encoding="utf-8")


def test_draft_write_contract() -> None:
    flow = source("options_flow.py")
    pages = "\n".join(
        source(name)
        for name in (
            "options_devices.py",
            "options_cleanup.py",
            "options_ha_cleanup.py",
            "options_review.py",
        )
    )
    assert "async_update_entry" not in pages
    assert flow.count("async_update_entry") == 1
    assert "async_step_apply_changes" in flow
    assert "async_step_discard_changes" in flow
    assert "self._draft.discard()" in flow


def test_navigation_contract() -> None:
    flow = source("options_flow.py")
    navigation = source("options_navigation.py")
    assert 'menu_options = ["ha_players", "server_cleanup"]' in flow
    assert 'menu_options.append("review_changes")' in flow
    assert "async_step_back_to_init" in flow
    assert "FLOW_ACTION_BACK" in navigation
    assert "navigation_selector" in navigation
    assert "SelectSelectorMode.DROPDOWN" in navigation
    assert "BooleanSelector" not in navigation


def test_inline_error_contract() -> None:
    flow = source("options_flow.py")
    server = source("options_cleanup.py")
    players = source("options_ha_cleanup.py")
    assert 'self._review_error = "no_changes"' in flow
    assert "MANUAL_CLEANUP_SCOPE_ALL_SAFE" in server
    assert 'errors["base"] = "invalid_selection"' in server
    assert 'errors["base"] = "unsaved_changes"' in players


def test_preview_execution_contract() -> None:
    server = source("options_cleanup.py")
    players = source("options_ha_cleanup.py")
    assert "confirm_server_deletion" in server
    assert "execute_server_deletion" in server
    assert "confirm_ha_removal" in players
    assert "execute_ha_removal" in players


def test_draft_does_not_schedule_runtime() -> None:
    combined = "\n".join(
        source(name)
        for name in (
            "options_flow.py",
            "options_devices.py",
            "options_cleanup.py",
            "options_ha_cleanup.py",
        )
    )
    assert "async_setup_automatic_cleanup" not in combined
    assert "async_schedule_automatic_cleanup" not in combined
