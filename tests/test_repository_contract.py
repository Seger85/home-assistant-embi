from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


def test_manifest_points_to_canonical_repository() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text())

    assert manifest["domain"] == "emby"
    assert manifest["name"] == "Emby Integration - EMBi"
    assert manifest["version"] == "0.3.0-rc1"
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
