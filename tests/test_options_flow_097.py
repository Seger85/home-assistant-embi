from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from custom_components.emby.options_devices import _player_toggle_fields, _sort_group_players
from custom_components.emby.player_context import PlayerContext


def _player(name: str, when: datetime | None, playback: str = "non_playing") -> PlayerContext:
    return PlayerContext(
        player_key=f"{name}.Emby",
        reported_device_id=name,
        app_name="Emby for iOS",
        device_name=name,
        users=("Alex",),
        latest_user="Alex",
        last_activity=when,
        client_class="playback",
        classification_reason="test",
        entity_id=f"media_player.{name.casefold()}",
        ha_name=name,
        registry_present=True,
        registry_enabled=True,
        registry_hidden=False,
        runtime_state="idle",
        playback=playback,
        emby_present=True,
        visible_in_embi=True,
        orphan=False,
        removable=playback == "non_playing",
        protected_reason=None if playback == "non_playing" else playback,
    )


def test_player_rows_are_two_line_local_and_never_expose_entity_ids() -> None:
    player = _player("iPhone", datetime(2026, 7, 18, 12, 30, tzinfo=UTC))
    fields = _player_toggle_fields([player], german=True, time_zone="Europe/Berlin")
    label, selected = fields[0]
    assert selected is player
    assert label == "iPhone · Emby for iOS\nZuletzt: 18.07.2026 14:30"
    assert "media_player" not in label


def test_group_sort_is_always_oldest_first_and_unknown_last() -> None:
    old = _player("Old", datetime(2025, 1, 1, tzinfo=UTC))
    new = _player("New", datetime(2026, 1, 1, tzinfo=UTC))
    unknown = _player("Unknown", None)
    assert _sort_group_players([new, unknown, old]) == [old, new, unknown]
    assert _sort_group_players([unknown, old, new]) == [old, new, unknown]


def test_no_search_sort_or_back_only_fields_remain() -> None:
    root = Path("custom_components/emby")
    devices = (root / "options_devices.py").read_text(encoding="utf-8")
    cleanup = (root / "options_cleanup.py").read_text(encoding="utf-8")
    ha_cleanup = (root / "options_ha_cleanup.py").read_text(encoding="utf-8")
    assert "CONF_SEARCH_QUERY" not in devices + ha_cleanup
    assert "CONF_PLAYER_SORT_ORDER" not in devices
    assert "navigation_selector" not in devices
    automatic = cleanup.split("async def async_step_automatic_cleanup", 1)[1].split(
        "async def async_step_server_history_check", 1
    )[0]
    assert "CONF_FLOW_ACTION" not in automatic


def test_manual_cleanup_does_not_mutate_automatic_threshold_contract() -> None:
    cleanup = Path("custom_components/emby/options_cleanup.py").read_text(encoding="utf-8")
    manual = cleanup.split("async def async_step_server_history_check", 1)[1].split(
        "async def async_step_confirm_server_deletion", 1
    )[0]
    assert "ignore_age=True" in manual
    assert "CONF_SERVER_AUTO_CLEANUP_AGE_DAYS" in manual
    assert "self._draft_options[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS]" not in manual
    assert "manual_age" not in manual
    assert "manual_cleanup_scope" not in manual


def test_unknown_and_active_lifecycle_states_are_fail_safe() -> None:
    devices = Path("custom_components/emby/options_devices.py").read_text(encoding="utf-8")
    maintenance = Path("custom_components/emby/maintenance_common.py").read_text(encoding="utf-8")
    assert "player.playback == PLAYBACK_UNKNOWN" in devices
    assert "player.playback in ACTIVE_PLAYBACK_STATES" in devices
    assert "state_value in ACTIVE_STATES" in maintenance
    assert '"unknown"' in maintenance
    assert "state_is_restored(state)" in maintenance


def test_diagnostics_identifies_current_contract_without_private_data() -> None:
    diagnostics = Path("custom_components/emby/diagnostics.py").read_text(encoding="utf-8")
    assert '"options_flow_contract": "0.9.9"' in diagnostics
    assert '"manual_cleanup_policy": "all_safe_inactive_age_independent"' in diagnostics
