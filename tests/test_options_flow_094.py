from __future__ import annotations

from pathlib import Path

from custom_components.emby.player_context import CLIENT_CLASS_TECHNICAL, classify_client


def test_registry_only_home_assistant_identity_is_technical() -> None:
    client_class, reason = classify_client(
        [],
        registry_backed=True,
        registry_name="Home Assistant player",
        entity_id="media_player.emby_homeassistant",
    )
    assert client_class == CLIENT_CLASS_TECHNICAL
    assert reason == "explicit_technical_identity"


def test_group_switches_are_the_only_normal_player_action() -> None:
    source = Path("custom_components/emby/options_devices.py").read_text(encoding="utf-8")
    root = source.split("async def async_step_ha_players", 1)[1].split(
        "async def async_step_back_to_ha_players", 1
    )[0]
    group = source.split("async def async_step_player_group", 1)[1].split(
        "async def async_step_player_exceptions", 1
    )[0]
    assert "CONF_PLAYER_ACTION" not in root
    assert "CONF_SELECTED_PLAYER_KEY" not in group
    assert "selector.BooleanSelector()" in group


def test_apply_reconciles_hidden_entities_and_runs_changed_auto_cleanup_immediately() -> None:
    source = Path("custom_components/emby/options_flow.py").read_text(encoding="utf-8")
    apply = source.split("async def async_step_apply_changes", 1)[1]
    assert "async_remove_hidden_player_entities" in apply
    assert "prevalidated_non_playing_keys=remove_keys" in apply
    assert "prevalidated_non_playing_keys=remove_keys" in apply
    assert "prevalidated_non_playing_keys=remove_keys" in apply
    assert "prevalidated_non_playing_keys=remove_keys" in apply
    assert "prevalidated_non_playing_keys=remove_keys" in apply
    assert "async_run_automatic_cleanup" in apply
    assert "cleanup_changed and updated_auto" in apply


def test_release_after_merge_and_package_version_is_dynamic() -> None:
    release = Path(".github/workflows/release.yml").read_text(encoding="utf-8")
    quality = Path(".github/workflows/quality.yml").read_text(encoding="utf-8")
    package = Path(".github/workflows/test-artifact.yml").read_text(encoding="utf-8")
    assert "pull_request:" in release and "closed" in release
    assert "workflow_dispatch:" in release
    assert "FETCH_HEAD" in release
    assert "origin/main" not in release
    assert "manifest.json" in quality and '--expected-version "${VERSION}"' in quality
    assert "manifest.json" in package and '--expected-version "${VERSION}"' in package
