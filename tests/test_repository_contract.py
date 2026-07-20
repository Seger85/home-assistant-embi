from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


def test_manifest_and_runtime_versions_remain_aligned() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    constants = (COMPONENT / "const.py").read_text(encoding="utf-8")
    assert manifest["version"] == "1.0.1"
    assert 'VERSION = "1.0.1"' in constants
    assert manifest["codeowners"] == ["@Seger85"]
    assert manifest["requirements"] == ["pyEmby==1.10"]


def test_runtime_and_normal_tests_are_version_neutral() -> None:
    versioned_runtime = [
        path.name
        for path in COMPONENT.glob("*.py")
        if re.search(r"_(?:0\d{2}|1\d{2})\.py$", path.name)
    ]
    versioned_tests = [
        path.name
        for path in (ROOT / "tests").glob("*.py")
        if re.search(r"_(?:0\d{2}|1\d{2})\.py$", path.name)
    ]
    assert versioned_runtime == []
    assert versioned_tests == []
    assert (COMPONENT / "legacy_migration.py").exists()
    assert (ROOT / "tests" / "migration" / "test_legacy_options.py").exists()
    assert not (ROOT / "docs" / "specs").exists()


def test_documentation_is_current_and_has_one_release_source() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    releasing = (ROOT / "RELEASING.md").read_text(encoding="utf-8")
    assert "Home Assistant custom integration" in readme
    assert "sensor.emby_movie_count" in readme
    assert "sensor.emby_users_watching" in readme
    assert "entity registry" in readme
    assert "python -I scripts/read_version.py" in releasing
    assert "embi.zip" in releasing and "embi.zip.sha256" in releasing
    assert "Signed-off-by: Seger" in releasing
    for removed in (
        "docs/PROJECT_STATE.md",
        "docs/development.md",
        "docs/migration-from-core.md",
        "docs/release-checklist.md",
        "docs/repository-governance.md",
    ):
        assert not (ROOT / removed).exists()


def test_workflow_inventory_and_responsibilities_are_distinct() -> None:
    workflow_dir = ROOT / ".github" / "workflows"
    assert {path.name for path in workflow_dir.glob("*.yml")} == {
        "hacs.yml",
        "hassfest.yml",
        "quality.yml",
        "release.yml",
        "test-artifact.yml",
    }
    quality = (workflow_dir / "quality.yml").read_text(encoding="utf-8")
    package = (workflow_dir / "test-artifact.yml").read_text(encoding="utf-8")
    release = (workflow_dir / "release.yml").read_text(encoding="utf-8")
    assert '"3.13"' in quality and '"3.14"' in quality
    assert "cancel-in-progress: true" in quality
    assert "build_package.py" not in quality
    assert "build_package.py" in package
    assert "github.event.pull_request.head.sha || github.sha" in package
    assert "workflow_dispatch:" not in release
    assert "startsWith(github.event.pull_request.head.ref, 'release/')" in release
    assert "make_latest: true" in release
    assert "gh release download" in release
    assert "cmp dist/embi.zip" in release


def test_release_assets_and_storage_safety_remain_exact() -> None:
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    publish_block = release.split("files: |", 1)[1].split("fail_on_unmatched_files", 1)[0]
    assert "dist/embi.zip" in publish_block
    assert "dist/embi.zip.sha256" in publish_block
    assert "BUILD_COMMIT" not in publish_block
    component_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in COMPONENT.rglob("*")
        if path.is_file() and path.suffix in {".py", ".json"}
    )
    assert "/config/.storage" not in component_text
