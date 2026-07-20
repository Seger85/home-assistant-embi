from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"
LEGACY_SPEC_DIR = ROOT / "docs" / "specs" / "0.9.0"


def _collect_requirement_ids(value) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        if "id" in value:
            found.add(str(value["id"]))
        for child in value.values():
            found.update(_collect_requirement_ids(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_collect_requirement_ids(child))
    return found


def test_every_frozen_legacy_requirement_has_traceable_acceptance_evidence() -> None:
    requirements = yaml.safe_load(
        (LEGACY_SPEC_DIR / "requirements.yaml").read_text(encoding="utf-8")
    )
    matrix = (LEGACY_SPEC_DIR / "10-test-and-acceptance-matrix.md").read_text(encoding="utf-8")
    requirement_ids = _collect_requirement_ids(requirements)
    assert requirement_ids
    assert "EMBI-0.9-EVIDENCE-START" in matrix
    missing = sorted(
        requirement_id for requirement_id in requirement_ids if requirement_id not in matrix
    )
    assert missing == []
    assert "Noch nicht als bestanden markiert" in matrix


def test_temporary_implementation_workflows_are_not_committed() -> None:
    workflows = ROOT / ".github" / "workflows"
    forbidden = {
        "embi-09-style-fix.yml",
        "embi-09-diagnostic.yml",
        "embi-09-pytest-diagnostic.yml",
        "embi-09-evidence-update.yml",
        "embi-09-cleanup-temp.yml",
        "format-091-once.yml",
    }
    assert forbidden.isdisjoint({path.name for path in workflows.glob("*.yml")})


def test_readme_is_community_oriented_and_documents_sensor_lifecycle() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Home Assistant players" in readme
    assert "sensor.emby_movie_count" in readme
    assert "sensor.emby_users_watching" in readme
    assert "paused sessions are not counted" in readme
    assert "YAML sensors" in readme
    assert "entity registry" in readme
    for forbidden in ("Gerry", "ChatGPT", "AI agent", "Upgrade to 0.9.7"):
        assert forbidden not in readme


def test_main_documents_share_the_public_product_contract() -> None:
    expected_terms = {
        "docs/PROJECT_STATE.md": ("Product overview", "stable GitHub release", "HACS"),
        "docs/architecture.md": ("PlayerContext", "sensor", "update coordinator"),
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
    english = json.loads((COMPONENT / "translations/en.json").read_text(encoding="utf-8"))
    german = json.loads((COMPONENT / "translations/de.json").read_text(encoding="utf-8"))

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
    assert "sensors" in english["options"]["step"]
    assert "sensors" in german["options"]["step"]
    assert "older_rules" in english["options"]["step"]
    assert "older_rules" in german["options"]["step"]


def test_current_component_has_expected_sensor_platform_and_no_direct_storage_edits() -> None:
    constants = (COMPONENT / "const.py").read_text(encoding="utf-8")
    component_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in COMPONENT.rglob("*")
        if path.is_file() and path.suffix in {".py", ".json"}
    )
    direct_storage_path = "/config/" + ".storage"

    assert 'PLATFORMS = ["media_player", "sensor"]' in constants
    assert "sensor.py" in {path.name for path in COMPONENT.iterdir()}
    assert "button.py" not in {path.name for path in COMPONENT.iterdir()}
    assert "update.py" not in {path.name for path in COMPONENT.iterdir()}
    assert direct_storage_path not in component_text
