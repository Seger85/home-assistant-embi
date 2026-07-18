from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_required_repository_files_exist() -> None:
    required = [
        "README.md",
        "CHANGELOG.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "hacs.json",
        "requirements_test.txt",
        ".github/workflows/quality.yml",
        ".github/workflows/hacs.yml",
        ".github/workflows/hassfest.yml",
        ".github/workflows/release.yml",
        ".github/workflows/test-artifact.yml",
        "scripts/build_package.py",
        "scripts/validate_spec_contract.py",
        "scripts/validate_stable_contract.py",
        "scripts/secret_scan.py",
    ]
    for relative in required:
        assert (ROOT / relative).is_file(), relative


def test_manifest_and_hacs_contract() -> None:
    manifest = json.loads(_read("custom_components/emby/manifest.json"))
    hacs = json.loads(_read("hacs.json"))
    assert manifest["domain"] == "emby"
    assert manifest["config_flow"] is True
    assert manifest["iot_class"] == "local_push"
    assert manifest["version"] == "0.9.3"
    assert hacs["zip_release"] is True
    assert hacs["filename"] == "embi.zip"
    assert hacs["hide_default_branch"] is True


def test_runtime_version_matches_manifest() -> None:
    manifest = json.loads(_read("custom_components/emby/manifest.json"))
    tree = ast.parse(_read("custom_components/emby/const.py"))
    runtime_version = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == "VERSION" for target in node.targets):
            runtime_version = ast.literal_eval(node.value)
            break
    assert runtime_version == manifest["version"]


def test_release_workflow_builds_hacs_archive() -> None:
    workflow = _read(".github/workflows/release.yml")
    assert "scripts/build_package.py" in workflow
    assert "embi.zip" in workflow
    assert "embi.zip.sha256" in workflow
    assert "BUILD_COMMIT" in workflow
    assert "sha256sum --check" in workflow
    assert "softprops/action-gh-release@v3" in workflow


def test_quality_workflow_covers_supported_python_versions() -> None:
    workflow = _read(".github/workflows/quality.yml")
    assert '"3.13"' in workflow
    assert '"3.14"' in workflow
    assert "pytest -q" in workflow
    assert "ruff check" in workflow
    assert "ruff format --check" in workflow
    assert "mypy" in workflow
    assert "validate_spec_contract.py" in workflow
    assert "validate_stable_contract.py" in workflow
    assert "secret_scan.py" in workflow
    assert "--expected-version 0.9.3" in workflow


def test_hacs_and_hassfest_workflows_are_required_quality_checks() -> None:
    hacs = _read(".github/workflows/hacs.yml")
    hassfest = _read(".github/workflows/hassfest.yml")
    assert "hacs/action@main" in hacs
    assert "home-assistant/actions/hassfest@master" in hassfest
    assert "pull_request" in hacs
    assert "pull_request" in hassfest


def test_release_requires_release_branch_and_semver_tag() -> None:
    workflow = _read(".github/workflows/release.yml")
    assert "origin/main" in workflow
    assert 'tags:\n      - "v*"' in workflow
    assert 'branches:\n      - "release/v*"' in workflow
    assert '"[0-9]*"' not in workflow
    assert "^v[0-9]+" in workflow
    assert "Remove verified release request branch" in workflow
    assert "prerelease: false" in workflow
    assert "make_latest: true" in workflow


def test_test_package_is_bound_to_exact_source_commit() -> None:
    workflow = (ROOT / ".github" / "workflows" / "test-artifact.yml").read_text()
    assert "github.event.pull_request.head.sha || github.sha" in workflow
    assert "ref: ${{ env.BUILD_COMMIT_SHA }}" in workflow
    assert '--commit "${BUILD_COMMIT_SHA}"' in workflow
    assert 'test "$(cat dist/BUILD_COMMIT)" = "${BUILD_COMMIT_SHA}"' in workflow
    assert "embi-test-${{ env.BUILD_COMMIT_SHA }}" in workflow
    assert "--expected-version 0.9.3" in workflow
