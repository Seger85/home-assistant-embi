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
    assert "player.player_key for player in players if player.visible_in_embi" in flow


def test_active_technical_and_user_groups_cannot_be_hidden_by_normal_apply() -> None:
    devices = source("options_devices.py")
    flow = source("options_flow.py")

    assert "active_technical" in devices
    assert 'errors["base"] = "playback_protected"' in devices
    assert "hide_user_group" in devices
    assert "active_group" in devices
    assert "protected_technical" in flow
    assert "user_visibility[user_name] = True" in flow


def test_diagnostics_redact_server_host_and_title() -> None:
    diagnostics = source("diagnostics.py")

    assert "from homeassistant.const import CONF_API_KEY, CONF_HOST" in diagnostics
    assert '"title": "<redacted>"' in diagnostics
    assert (
        "async_redact_data(dict(entry.data), {CONF_API_KEY, CONF_HOST})" in diagnostics
    )
