from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


def source(name: str) -> str:
    return (COMPONENT / name).read_text(encoding="utf-8")


def test_disabling_auto_show_preserves_current_visible_players() -> None:
    devices = source("options_devices.py")
    flow = source("options_flow.py")
    assert "CONF_ALLOWED_DEVICE_IDS" in devices
    assert "allowed.update(" in devices
    assert "player.player_key" in devices
    assert "player.visible_in_embi" in devices
    assert "CONF_ALLOWED_DEVICE_IDS" in flow
    assert "for player in original_players" in flow
    assert "if player.visible_in_embi" in flow


def test_playback_protection_never_rewrites_master_options() -> None:
    devices = source("options_devices.py")
    flow = source("options_flow.py")
    actions = source("player_actions.py")
    assert "playback_protected_named" in devices
    assert "blocked_players" in devices
    assert "CONF_TECHNICAL_ACCESS_VISIBILITY] = True" not in flow
    assert "user_visibility[player.users[0]] = True" not in flow
    assert '"GET", "/Sessions"' in actions
    assert "_unknown_is_safe" in actions
    assert "_fresh_sessions" in actions


def test_diagnostics_redact_server_host_and_title() -> None:
    diagnostics = source("diagnostics.py")
    assert "from homeassistant.const import CONF_API_KEY, CONF_HOST" in diagnostics
    assert '"title": "<redacted>"' in diagnostics
    assert "async_redact_data(dict(entry.data), {CONF_API_KEY, CONF_HOST})" in diagnostics
    assert "player_key" not in diagnostics
