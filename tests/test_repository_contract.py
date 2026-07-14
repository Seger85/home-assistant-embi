from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


def test_manifest_points_to_canonical_repository() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text())

    assert manifest["domain"] == "emby"
    assert manifest["name"] == "Emby Integration - EMBi"
    assert manifest["version"] == "0.3.0-rc3"
    assert manifest["codeowners"] == ["@Seger85"]
    assert manifest["documentation"].endswith("Seger85/home-assistant-embi")
    assert manifest["issue_tracker"].endswith("Seger85/home-assistant-embi/issues")


def test_legacy_yaml_platform_is_removed() -> None:
    media_player = (COMPONENT / "media_player.py").read_text()

    assert "PLATFORM_SCHEMA" not in media_player
    assert "async_setup_platform" not in media_player
    assert "Legacy YAML" not in media_player


def test_english_strings_match_translation_source() -> None:
    strings = json.loads((COMPONENT / "strings.json").read_text())
    english = json.loads((COMPONENT / "translations" / "en.json").read_text())

    assert strings == english


def test_server_cleanup_credentials_are_redacted() -> None:
    diagnostics = (COMPONENT / "diagnostics.py").read_text()

    assert "CONF_SERVER_CLEANUP_API_KEY" in diagnostics
    assert "TO_REDACT" in diagnostics


def test_password_fields_do_not_reuse_stored_secrets_as_defaults() -> None:
    config_flow = (COMPONENT / "config_flow.py").read_text()
    maintenance_flow = (COMPONENT / "maintenance_flow.py").read_text()

    assert "defaults.get(CONF_API_KEY" not in config_flow
    assert "default=current.get(CONF_SERVER_CLEANUP_API_KEY" not in maintenance_flow
    assert "submitted_api_key or entry.data[CONF_API_KEY]" in config_flow
    assert "submitted_cleanup_key or stored_cleanup_key" in maintenance_flow


def test_media_player_unique_id_contract_is_unchanged() -> None:
    media_player = (COMPONENT / "media_player.py").read_text()

    assert "self._attr_unique_id = device_id" in media_player


def test_all_sensitive_device_identity_fields_are_redacted() -> None:
    diagnostics = (COMPONENT / "diagnostics.py").read_text()

    for field in (
        '"record_id"',
        '"reported_device_id"',
        '"player_key"',
        '"name"',
        '"last_user_name"',
    ):
        assert field in diagnostics


def test_automatic_cleanup_contract_is_explicit_and_uncapped() -> None:
    constants = (COMPONENT / "const.py").read_text()
    cleanup = (COMPONENT / "cleanup.py").read_text()
    maintenance = (COMPONENT / "maintenance.py").read_text()

    assert "AUTO_CLEANUP_INITIAL_DELAY_SECONDS = 120" in constants
    assert "DEFAULT_SERVER_CLEANUP_AGE_DAYS = 365" in constants
    assert "there is deliberately no run cap" in cleanup
    assert "plan.candidates" in maintenance
    assert "[:" not in maintenance


def test_registry_removal_requires_post_delete_revalidation() -> None:
    maintenance = (COMPONENT / "maintenance.py").read_text()
    maintenance_flow = (COMPONENT / "maintenance_flow.py").read_text()

    assert "remaining_player_keys" in maintenance
    assert "hass.states.get(entity.entity_id) is not None" in maintenance
    assert "removable_player_keys" in maintenance_flow
    assert "queue_registry_cleanup" in maintenance_flow
