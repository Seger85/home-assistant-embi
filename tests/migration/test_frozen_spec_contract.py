from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPONENT = ROOT / "custom_components" / "emby"
SPEC_DIR = ROOT / "docs" / "specs" / "0.9.0"


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


def test_every_frozen_requirement_has_traceable_acceptance_evidence() -> None:
    requirements = yaml.safe_load((SPEC_DIR / "requirements.yaml").read_text(encoding="utf-8"))
    matrix = (SPEC_DIR / "10-test-and-acceptance-matrix.md").read_text(encoding="utf-8")
    requirement_ids = _collect_requirement_ids(requirements)
    assert requirement_ids
    assert "EMBI-0.9-EVIDENCE-START" in matrix
    assert sorted(item for item in requirement_ids if item not in matrix) == []


def test_current_repository_has_no_temporary_implementation_workflows() -> None:
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


def test_public_documents_match_the_current_product_contract() -> None:
    expected_terms = {
        "README.md": ("Home Assistant players", "sensor.emby_users_watching", "entity registry"),
        "docs/architecture.md": ("PlayerContext", "legacy_migration.py", "reload"),
        "docs/configuration.md": ("Review changes", "sensor.emby_movie_count", "YAML"),
        "docs/server-cleanup.md": ("skipped_recent", "Playing", "Manual selection"),
        "docs/security.md": ("`.storage`", "unique ID", "unrelated"),
        "docs/troubleshooting.md": ("unavailable", "YAML", "HACS"),
        "docs/development.md": ("Ruff", "pull request"),
        "docs/ui-qa.md": ("iPhone", "iPad", "desktop"),
        "docs/release-checklist.md": ("BUILD_COMMIT", "HACS", "latest"),
        "docs/repository-governance.md": ("main", "release/<version>", "never rewritten"),
    }
    for relative_path, terms in expected_terms.items():
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        for term in terms:
            assert term in content, f"{relative_path} misses {term}"


def test_translations_are_structurally_identical() -> None:
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


def test_current_platform_inventory_and_storage_safety() -> None:
    constants = (COMPONENT / "const.py").read_text(encoding="utf-8")
    component_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in COMPONENT.rglob("*")
        if path.is_file() and path.suffix in {".py", ".json"}
    )
    assert 'PLATFORMS = ["media_player", "sensor"]' in constants
    assert "sensor.py" in {path.name for path in COMPONENT.iterdir()}
    assert "/config/.storage" not in component_text
