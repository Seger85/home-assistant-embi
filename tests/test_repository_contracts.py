from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


def test_temporary_and_duplicate_workflows_are_not_committed() -> None:
    workflows = ROOT / ".github" / "workflows"
    forbidden = {
        "embi-09-style-fix.yml",
        "embi-09-diagnostic.yml",
        "embi-09-pytest-diagnostic.yml",
        "embi-09-evidence-update.yml",
        "embi-09-cleanup-temp.yml",
        "format-091-once.yml",
        "legacy-migration-contract.yml",
        "spec-contract.yml",
    }
    assert forbidden.isdisjoint({path.name for path in workflows.glob("*.yml")})


def test_readme_is_community_oriented_and_documents_current_lifecycle() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Home Assistant players" in readme
    assert "sensor.emby_movie_count" in readme
    assert "sensor.emby_users_watching" in readme
    assert "paused sessions are not counted" in readme
    assert "YAML sensors" in readme
    assert "entity registry" in readme
    assert "after every setup, config-entry reload, and restart" in readme
    for forbidden in ("Gerry", "ChatGPT", "AI agent", "Upgrade to 0.9.7"):
        assert forbidden not in readme


def test_main_documents_share_the_public_product_contract() -> None:
    expected_terms = {
        "docs/PROJECT_STATE.md": ("Product overview", "stable GitHub release", "HACS"),
        "docs/architecture.md": ("PlayerContext", "legacy_migration.py", "reload"),
        "docs/configuration.md": ("Review changes", "sensor.emby_movie_count", "YAML"),
        "docs/server-cleanup.md": ("skipped_recent", "Playing", "Manual selection"),
        "docs/security.md": ("`.storage`", "unique ID", "unrelated"),
        "docs/troubleshooting.md": ("unavailable", "YAML", "HACS"),
        "docs/development.md": (
            "Ruff",
            "validate_legacy_migration_contract.py",
            "pull request",
        ),
        "docs/ui-qa.md": ("iPhone", "iPad", "desktop"),
        "docs/release-checklist.md": ("BUILD_COMMIT", "HACS", "latest"),
        "docs/repository-governance.md": ("main", "release/<version>", "never rewritten"),
    }
    for relative_path, terms in expected_terms.items():
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        for term in terms:
            assert term in content, f"{relative_path} misses {term}"


def test_translations_are_structurally_identical_and_use_current_navigation() -> None:
    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    english = json.loads((COMPONENT / "translations" / "en.json").read_text(encoding="utf-8"))
    german = json.loads((COMPONENT / "translations" / "de.json").read_text(encoding="utf-8"))

    def paths(value, prefix=()):
        result = set()
        if isinstance(value, Mapping):
            for key, child in value.items():
                current = (*prefix, str(key))
                result.add(current)
                result.update(paths(child, current))
        return result

    assert strings == english
    assert paths(english) == paths(german)
    root_menu = english["options"]["step"]["init"]["menu_options"]
    assert set(root_menu) == {
        "ha_players",
        "sensors",
        "automatic_cleanup",
        "server_history_check",
        "review_changes",
    }


def test_current_component_has_expected_platforms_and_no_direct_storage_edits() -> None:
    constants = (COMPONENT / "const.py").read_text(encoding="utf-8")
    component_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in COMPONENT.rglob("*")
        if path.is_file() and path.suffix in {".py", ".json"}
    )
    assert 'PLATFORMS = ["media_player", "sensor"]' in constants
    assert "sensor.py" in {path.name for path in COMPONENT.iterdir()}
    assert "/config/.storage" not in component_text
