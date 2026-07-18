from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from custom_components.emby.options_devices import (
    _player_toggle_fields,
    _sort_group_players,
)
from custom_components.emby.player_context import PlayerContext


def _player(name: str, when: datetime | None) -> PlayerContext:
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
        playback="non_playing",
        emby_present=True,
        visible_in_embi=True,
        orphan=False,
        removable=True,
        protected_reason=None,
    )


def test_player_rows_are_two_line_local_and_never_expose_entity_ids() -> None:
    player = _player("iPhone", datetime(2026, 7, 18, 12, 30, tzinfo=UTC))
    fields = _player_toggle_fields([player], german=True, time_zone="Europe/Berlin")
    label, selected = fields[0]
    assert selected is player
    assert label == "iPhone · Emby for iOS\nZuletzt: 18.07.2026 14:30"
    assert "media_player" not in label


def test_group_sort_oldest_first_and_unknown_last() -> None:
    old = _player("Old", datetime(2025, 1, 1, tzinfo=UTC))
    new = _player("New", datetime(2026, 1, 1, tzinfo=UTC))
    unknown = _player("Unknown", None)
    assert _sort_group_players([new, unknown, old], "oldest_first") == [old, new, unknown]
    assert _sort_group_players([old, unknown, new], "newest_first") == [new, old, unknown]


def test_non_destructive_pages_use_back_only_and_apply_is_backgrounded() -> None:
    devices = Path("custom_components/emby/options_devices.py").read_text(encoding="utf-8")
    cleanup = Path("custom_components/emby/options_cleanup.py").read_text(encoding="utf-8")
    flow = Path("custom_components/emby/options_flow.py").read_text(encoding="utf-8")
    assert "Speichern & zurück" not in devices
    assert "Save & back" not in devices
    automatic = cleanup.split("async def async_step_automatic_cleanup", 1)[1].split(
        "async def async_step_server_history_check", 1
    )[0]
    assert "Speichern & zurück" not in automatic
    assert "Save & back" not in automatic
    apply = flow.split("async def async_step_apply_changes", 1)[1]
    assert "async_create_task" in apply
    assert 'return self.async_abort(reason="apply_complete")' in apply
    assert "await self.hass.config_entries.async_reload" not in apply
