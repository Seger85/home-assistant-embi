from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


def source(name: str) -> str:
    return (COMPONENT / name).read_text(encoding="utf-8")


def test_normal_pages_are_draft_only_and_apply_is_the_only_normal_write() -> None:
    options_flow = source("options_flow.py")
    normal_pages = "\n".join(
        source(name)
        for name in (
            "options_devices.py",
            "options_cleanup.py",
            "options_ha_cleanup.py",
            "options_review.py",
        )
    )

    assert "async_update_entry" not in normal_pages
    assert options_flow.count("async_update_entry") == 1
    assert "async_step_apply_changes" in options_flow
    assert "async_step_discard_changes" in options_flow
    assert "self._draft.discard()" in options_flow
    assert "CONF_CONFIRM_APPLY" not in options_flow
    assert "CONF_CONFIRM_DISCARD" not in options_flow


def test_root_navigation_matches_the_frozen_contract() -> None:
    options_flow = source("options_flow.py")

    assert 'menu_options = ["devices_players", "cleanup"]' in options_flow
    assert 'menu_options.append("review_changes")' in options_flow
    assert "clients_bulk" not in options_flow
    assert "about" not in options_flow
    assert "server_cleanup_settings" not in options_flow


def test_apply_no_change_discard_and_close_contract() -> None:
    options_flow = source("options_flow.py")

    assert 'reason="no_changes"' in options_flow
    assert "self._draft.discard()" in options_flow
    assert "__del__" not in options_flow
    assert "async_close" not in options_flow
    assert "async_step_apply_changes(" in options_flow
    assert "async_step_discard_changes(" in options_flow


def test_dirty_draft_blocks_destructive_actions() -> None:
    server_cleanup = source("options_cleanup.py")
    ha_cleanup = source("options_ha_cleanup.py")
    guard = 'if self._dirty:\n            return self.async_abort(reason="unsaved_changes")'

    assert guard in server_cleanup
    assert guard in ha_cleanup
    assert "if not self._dirty:" in server_cleanup


def test_destructive_actions_have_one_final_boolean_confirmation_each() -> None:
    server_cleanup = source("options_cleanup.py")
    ha_cleanup = source("options_ha_cleanup.py")

    assert server_cleanup.count("CONF_CONFIRM_SERVER_DELETION") >= 2
    assert server_cleanup.count("BooleanSelector") >= 1
    assert "CONF_CONFIRMATION_TEXT" not in server_cleanup
    assert "TextSelector" not in server_cleanup
    assert ha_cleanup.count("CONF_CONFIRM_HA_REMOVAL") >= 2
    assert ha_cleanup.count("BooleanSelector") >= 1


def test_automation_is_not_scheduled_from_the_draft_flow() -> None:
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
