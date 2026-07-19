from __future__ import annotations

import json
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
    assert flow.count(".async_update_entry(") == 1
    assert "async_step_apply_changes" in flow
    assert "async_step_discard_changes" in flow
    assert "self._draft.discard()" in flow


def test_direct_navigation_contract() -> None:
    flow = source("options_flow.py")
    devices = source("options_devices.py")
    cleanup = source("options_cleanup.py")
    for step in (
        '"ha_players"',
        '"sensors"',
        '"automatic_cleanup"',
        '"server_history_check"',
    ):
        assert step in flow
    assert 'menu_options.append("review_changes")' in flow
    assert "navigation_selector" not in devices
    automatic = cleanup.split("async def async_step_automatic_cleanup", 1)[1].split(
        "async def async_step_server_history_check", 1
    )[0]
    assert "navigation_selector" not in automatic
    assert "CONF_FLOW_ACTION" not in automatic


def test_player_search_and_sort_controls_are_absent() -> None:
    devices = source("options_devices.py")
    ha_cleanup = source("options_ha_cleanup.py")
    translations = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    rendered = json.dumps(translations)
    assert "CONF_SEARCH_QUERY" not in devices
    assert "CONF_PLAYER_SORT_ORDER" not in devices
    assert "CONF_SEARCH_QUERY" not in ha_cleanup
    assert "search_query" not in rendered
    assert "player_sort_order" not in rendered


def test_manual_cleanup_is_all_safe_and_age_independent() -> None:
    cleanup = source("options_cleanup.py")
    assert "CONF_MANUAL_CLEANUP_SCOPE" not in cleanup
    assert "manual_age_preset" not in cleanup
    assert "ignore_age=True" in cleanup
    assert "remove_ha_entities=True" in cleanup
    assert "CONF_SERVER_CLEANUP_AGE_DAYS" not in cleanup


def test_preview_execution_and_lifecycle_contract() -> None:
    cleanup = source("options_cleanup.py")
    players = source("options_ha_cleanup.py")
    maintenance = source("maintenance_common.py")
    actions = source("player_actions.py")
    assert "confirm_server_deletion" in cleanup
    assert "execute_server_deletion" in cleanup
    assert "confirm_ha_removal" in players
    assert "execute_ha_removal" in players
    assert "ACTIVE_STATES" in maintenance
    assert '"unknown"' in maintenance
    assert "state_is_restored" in maintenance
    assert "async_remove_hidden_player_entities" in actions


def test_apply_completion_remains_backgrounded() -> None:
    flow = source("options_flow.py")
    apply = flow.split("async def async_step_apply_changes", 1)[1]
    assert 'return self.async_abort(reason="apply_complete")' in apply
    assert "async_create_task" in apply
    assert "await self.hass.config_entries.async_reload" not in apply
