from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
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


def test_readme_is_product_oriented_and_not_a_prerelease_history_page() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "mehr Geräte in der Liste haben als im Haus" in readme
    assert "Geräte & Player" in readme
    assert "Gemeinsam genutzt" in readme
    assert "Technische Zugriffe" in readme
    assert "Unklare Clients" in readme
    assert "Player wiederherstellen" in readme
    assert "Release Candidate" not in readme
    assert "0.3.0-rc" not in readme


def test_main_documents_share_the_product_contract() -> None:
    expected_terms = {
        "docs/PROJECT_STATE.md": ("0.9.0", "Geräte & Player", "private"),
        "docs/architecture.md": ("PlayerContext", "Gemeinsam genutzt", "Store"),
        "docs/configuration.md": ("Änderungen prüfen", "364", "disabled"),
        "docs/server-cleanup.md": ("playing", "paused", "Wiederherstellung"),
        "docs/security.md": (
            "keine direkten Änderungen an `.storage`",
            "Unklare Clients",
        ),
        "docs/troubleshooting.md": ("Unklare Clients", "v0.3.0"),
        "docs/development.md": ("feature/embi-0.9.0", "validate_spec_contract.py"),
        "docs/ui-qa.md": ("iPhone", "iPad", "Desktop"),
        "docs/release-checklist.md": ("v0.9.0", "BUILD_COMMIT", "HACS"),
        "docs/repository-governance.md": ("PR #29", "feature/embi-0.9.0"),
    }
    for relative_path, terms in expected_terms.items():
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        for term in terms:
            assert term in content, f"{relative_path} misses {term}"


def test_translations_are_structurally_identical_and_use_091_navigation() -> None:
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
    assert set(root_menu) == {"ha_players", "server_cleanup", "review_changes"}
    assert "older_rules" in english["options"]["step"]
    assert "older_rules" in german["options"]["step"]


def test_091_does_not_add_reserved_entity_platforms_or_direct_storage_edits() -> None:
    constants = (COMPONENT / "const.py").read_text(encoding="utf-8")
    component_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in COMPONENT.rglob("*")
        if path.is_file() and path.suffix in {".py", ".json"}
    )
    direct_storage_path = "/config/" + ".storage"

    assert 'PLATFORMS = ["media_player"]' in constants
    assert "sensor.py" not in {path.name for path in COMPONENT.iterdir()}
    assert "button.py" not in {path.name for path in COMPONENT.iterdir()}
    assert "update.py" not in {path.name for path in COMPONENT.iterdir()}
    assert direct_storage_path not in component_text
