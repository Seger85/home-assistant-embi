from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


def _parse_requirement_constraints(text: str) -> dict[str, str]:
    requirements: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)(.*)", line)
        assert match is not None, f"Unsupported requirement format: {line}"
        name = match.group(1).lower().replace("_", "-")
        constraints = match.group(2)
        assert name not in requirements, f"Duplicate requirement: {name}"
        requirements[name] = constraints
    return requirements


def test_manifest_and_runtime_versions_remain_aligned() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    constants = (COMPONENT / "const.py").read_text(encoding="utf-8")
    assert manifest["version"] == "1.2.2"
    assert 'VERSION = "1.2.2"' in constants
    assert manifest["codeowners"] == ["@Seger85"]
    assert manifest["requirements"] == []  # Networking uses Home Assistant's aiohttp session.


def test_legal_hacs_and_tooling_baseline() -> None:
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    notice = (ROOT / "NOTICE.md").read_text(encoding="utf-8")
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    requirements = (ROOT / "requirements_test.txt").read_text(encoding="utf-8")

    assert "Apache License" in license_text and "Version 2.0" in license_text
    assert "Home Assistant Core" in notice and "Apache License 2.0" in notice
    assert "`pyEmby`" in notice and "MIT License" in notice
    assert "independent community project" in notice
    assert hacs == {
        "name": "Emby Integration - EMBi",
        "render_readme": True,
        "homeassistant": "2026.7.2",
        "hide_default_branch": True,
        "zip_release": True,
        "filename": "embi.zip",
    }
    assert 'target-version = "py313"' in pyproject
    assert 'select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]' in pyproject
    requirement_constraints = _parse_requirement_constraints(requirements)
    assert set(requirement_constraints) == {
        "aiohttp",
        "mypy",
        "pytest",
        "pytest-asyncio",
        "pyyaml",
        "ruff",
        "voluptuous",
    }
    assert requirement_constraints["aiohttp"].startswith(">=")
    assert requirement_constraints["mypy"].startswith(">=")
    assert ",<3" in requirement_constraints["mypy"]
    assert requirement_constraints["pytest"].startswith(">=")
    assert requirement_constraints["pytest-asyncio"].startswith(">=")
    assert requirement_constraints["pyyaml"].startswith(">=")
    assert requirement_constraints["ruff"].startswith("==")
    assert requirement_constraints["voluptuous"].startswith(">=")


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


def test_confirmed_dead_runtime_surfaces_remain_removed() -> None:
    common = (COMPONENT / "player_action_common.py").read_text(encoding="utf-8")
    actions = (COMPONENT / "player_actions.py").read_text(encoding="utf-8")
    reconciliation = (COMPONENT / "player_reconciliation.py").read_text(encoding="utf-8")
    context = (COMPONENT / "player_context.py").read_text(encoding="utf-8")
    options_runtime = (COMPONENT / "options_runtime.py").read_text(encoding="utf-8")

    assert "def owned_exact(" in common
    for symbol in (
        "class PlayerActionItem",
        "class PlayerActionResult",
        "def find_context(",
        "def fresh_catalog(",
        "def update_options_and_reload(",
        "def record_action(",
    ):
        assert symbol not in common
    assert "def async_enable_ha_entities(" not in actions
    assert "def async_reconcile_invisible_player_entities(" not in actions
    assert "def async_reconcile_invisible_player_entities(" not in reconciliation
    assert "def group_label(" not in context
    assert "def filter_player_catalog(" not in context
    assert "def options_for_flow(" not in options_runtime
    assert "def render_player_rows(" not in options_runtime


def test_documentation_is_current_and_has_one_release_source() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    releasing = (ROOT / "RELEASING.md").read_text(encoding="utf-8")
    assert "Emby integration for Home Assistant" in readme
    assert "README.de.md" in readme
    assert "sensor.emby_active_players" in readme
    assert "sensor.emby_movie_count" in readme
    assert "sensor.emby_users_watching" in readme
    assert "registry layout" in readme
    assert "python -I scripts/read_version.py" in releasing
    assert "scripts/prepare_automatic_release.py" in releasing
    assert "embi.zip" in releasing and "embi.zip.sha256" in releasing
    assert "HACS kann frühere Versionen installieren" in releasing
    assert "keine laufenden Reparaturkommentare" in releasing
    assert "EMBI_AUTOMATION_PAT" in releasing
    assert "first_time_contributors" in releasing
    assert "Die Standardrechte bleiben lesend" in releasing
    for removed in (
        "docs/PROJECT_STATE.md",
        "docs/development.md",
        "docs/migration-from-core.md",
        "docs/release-checklist.md",
        "docs/repository-governance.md",
    ):
        assert not (ROOT / removed).exists()


def test_dependabot_runs_on_day_six_and_repairs_before_validated_merge() -> None:
    dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    automerge = (ROOT / ".github" / "workflows" / "dependabot-automerge.yml").read_text(
        encoding="utf-8"
    )
    assert dependabot.count("interval: cron") == 2
    assert dependabot.count("timezone: Europe/Berlin") == 2
    assert 'cronjob: "0 3 6 * *"' in dependabot
    assert 'cronjob: "15 3 6 * *"' in dependabot
    assert dependabot.count("open-pull-requests-limit: 10") == 2
    assert dependabot.count("rebase-strategy: auto") == 2
    assert "pull_request_target:" in automerge
    assert 'cron: "23 5 * * *"' in automerge
    assert "dependabot[bot]" in automerge
    assert '--arg owner "${GITHUB_REPOSITORY_OWNER}"' in automerge
    assert ".user.login == $owner" in automerge
    for workflow_name in ("Quality", "Test package", "HACS validation", "Hassfest"):
        assert f'"{workflow_name}"' in automerge
    assert "rerun-failed-jobs" not in automerge
    assert '--repo "${GITHUB_REPOSITORY}"' in automerge
    assert "ruff==${RUFF_VERSION}" in automerge
    assert "sed -n 's/^ruff==//p'" in automerge
    assert "${workdir}/requirements_test.txt" in automerge
    assert 'RUFF_VERSION: "0.15.22"' not in automerge
    assert "ruff format ." in automerge
    assert "ruff check --fix ." in automerge
    assert "gh workflow run" in automerge
    assert "embi-autonomous-repair" in automerge
    assert "issues/${pr_number}/comments" not in automerge
    assert 'pulls/${pr_number}"' in automerge
    assert '-f body="${updated_body}"' in automerge
    assert "merge_method=squash" in automerge
    assert "pulls/${pr_number}/merge" in automerge


def test_workflow_inventory_and_responsibilities_are_distinct() -> None:
    workflow_dir = ROOT / ".github" / "workflows"
    assert {path.name for path in workflow_dir.glob("*.yml")} == {
        "dependabot-automerge.yml",
        "hacs.yml",
        "hassfest.yml",
        "quality.yml",
        "release.yml",
        "test-artifact.yml",
        "repository-hygiene.yml",
    }
    quality = (workflow_dir / "quality.yml").read_text(encoding="utf-8")
    package = (workflow_dir / "test-artifact.yml").read_text(encoding="utf-8")
    hacs = (workflow_dir / "hacs.yml").read_text(encoding="utf-8")
    hassfest = (workflow_dir / "hassfest.yml").read_text(encoding="utf-8")
    release = (workflow_dir / "release.yml").read_text(encoding="utf-8")
    assert '"3.13"' in quality and '"3.14"' in quality
    assert "cancel-in-progress: true" in quality
    assert "build_package.py" not in quality
    assert "build_package.py" in package
    assert "github.event.pull_request.head.sha || github.sha" in package
    for workflow in (quality, package, hacs, hassfest):
        assert "workflow_dispatch:" in workflow
    assert "schedule:" in release and 'cron: "47 4 * * *"' in release
    assert "pull_request:" not in release
    assert "push:" not in release
    assert "prepare_automatic_release.py" in release
    assert "secrets.EMBI_AUTOMATION_PAT" in release
    assert "gh api user --jq .login" in release
    assert "select(.user.login == $owner)" in release
    assert "Allow GitHub Actions to create and approve pull requests" not in release
    assert "make_latest: true" in release
    assert "gh release download" in release
    assert "cmp dist/embi.zip" in release
    for workflow in (quality, package, release):
        assert re.search(r"actions/setup-python@[0-9a-f]{40}\s", workflow)
        assert "actions/setup-python@v6" not in workflow
    assert re.search(r"actions/upload-artifact@[0-9a-f]{40}\s", package)
    assert "actions/upload-artifact@v4" not in package


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
