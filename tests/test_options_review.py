from __future__ import annotations

from custom_components.emby.const import (
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_GLOBAL_PLAYER_MODE,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    PLAYER_MODE_ACTIVE_ONLY,
    PLAYER_MODE_PERSISTENT,
)
from custom_components.emby.options_review import semantic_changes


def test_semantic_review_renders_meaningful_before_after_values() -> None:
    original = {
        CONF_GLOBAL_PLAYER_MODE: PLAYER_MODE_PERSISTENT,
        CONF_AUTO_SHOW_NEW_PLAYERS: True,
        CONF_SERVER_AUTO_CLEANUP_ENABLED: False,
        CONF_SERVER_AUTO_CLEANUP_AGE_DAYS: 364,
        CONF_HIDDEN_EXACT_PLAYERS: [],
    }
    draft = {
        CONF_GLOBAL_PLAYER_MODE: PLAYER_MODE_ACTIVE_ONLY,
        CONF_AUTO_SHOW_NEW_PLAYERS: False,
        CONF_SERVER_AUTO_CLEANUP_ENABLED: True,
        CONF_SERVER_AUTO_CLEANUP_AGE_DAYS: 365,
        CONF_HIDDEN_EXACT_PLAYERS: ["private-player-key"],
    }

    changes = semantic_changes(
        original,
        draft,
        player_labels={"private-player-key": "Emby TV · Living room"},
        german=False,
    )
    rendered = "\n".join(change.render() for change in changes)

    assert "Keep players → Only during playback" in rendered
    assert "On → Off" in rendered
    assert "364 days → 365 days" in rendered
    assert "Emby TV · Living room" in rendered
    assert "private-player-key" not in rendered


def test_unchanged_values_do_not_create_review_noise() -> None:
    options = {
        CONF_GLOBAL_PLAYER_MODE: PLAYER_MODE_PERSISTENT,
        CONF_AUTO_SHOW_NEW_PLAYERS: True,
        CONF_SERVER_AUTO_CLEANUP_ENABLED: False,
        CONF_SERVER_AUTO_CLEANUP_AGE_DAYS: 364,
        CONF_HIDDEN_EXACT_PLAYERS: [],
    }

    assert semantic_changes(options, dict(options)) == []


def test_review_includes_allowlist_and_unresolved_rule_changes_even_with_same_count():
    original = {"allowed_device_ids": ["a"], "unresolved_legacy_rules": ["old"]}
    draft = {"allowed_device_ids": ["b"], "unresolved_legacy_rules": []}
    changes = semantic_changes(original, draft, german=True)
    assert {change.key for change in changes} == {"allowed_device_ids", "unresolved_legacy_rules"}
