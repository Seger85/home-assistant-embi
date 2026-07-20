from __future__ import annotations

from custom_components.emby.const import (
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_GLOBAL_PLAYER_MODE,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_OPTIONS_SCHEMA_VERSION,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_CLEANUP_AGE_DAYS,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    OPTIONS_SCHEMA_VERSION,
    PLAYER_MODE_ACTIVE_ONLY,
    PLAYER_MODE_PERSISTENT,
)
from custom_components.emby.options_model import default_options, should_expose_player


def test_new_install_defaults_match_current_contract() -> None:
    options = default_options()
    assert options[CONF_OPTIONS_SCHEMA_VERSION] == OPTIONS_SCHEMA_VERSION
    assert options[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_PERSISTENT
    assert options[CONF_AUTO_SHOW_NEW_PLAYERS] is True
    assert options[CONF_TECHNICAL_ACCESS_VISIBILITY] is False
    assert options[CONF_SERVER_AUTO_CLEANUP_ENABLED] is False
    assert options[CONF_SERVER_CLEANUP_AGE_DAYS] == 365
    assert options[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS] == 365


def test_visibility_uses_exact_rules_and_playback_mode() -> None:
    options = default_options()
    key = "device-1.Emby App"
    assert should_expose_player(
        player_key=key,
        reported_device_id="device-1",
        state="idle",
        options=options,
        technical_access=False,
    )

    options[CONF_HIDDEN_EXACT_PLAYERS] = [key]
    assert not should_expose_player(
        player_key=key,
        reported_device_id="device-1",
        state="playing",
        options=options,
        technical_access=False,
    )

    options[CONF_HIDDEN_EXACT_PLAYERS] = []
    options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    assert not should_expose_player(
        player_key=key,
        reported_device_id="device-1",
        state="idle",
        options=options,
        technical_access=False,
    )
    assert should_expose_player(
        player_key=key,
        reported_device_id="device-1",
        state="paused",
        options=options,
        technical_access=False,
    )
