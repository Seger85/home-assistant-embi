from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"
WORKFLOWS = ROOT / ".github" / "workflows"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def translation_paths(value, prefix=()):
    result = set()
    if isinstance(value, dict):
        for key, child in value.items():
            current = (*prefix, str(key))
            result.add(current)
            result.update(translation_paths(child, current))
    return result


def local_import_targets(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            targets.add(node.module.split(".", 1)[0])
    return targets


def markdown_paths() -> list[Path]:
    return sorted(
        path for path in ROOT.rglob("*.md") if ".git" not in path.parts and "dist" not in path.parts
    )


def validate_markdown_links() -> None:
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    missing: list[str] = []
    for path in markdown_paths():
        content = path.read_text(encoding="utf-8")
        for raw_target in pattern.findall(content):
            target = raw_target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith(("mailto:", "#")):
                continue
            resolved = (path.parent / unquote(target)).resolve()
            if not resolved.exists():
                missing.append(f"{path.relative_to(ROOT)} -> {target}")
    require(not missing, f"dead Markdown links: {missing}")


def main() -> None:
    versioned_runtime = sorted(
        path.name
        for path in COMPONENT.glob("*.py")
        if re.search(r"_(?:0\d{2}|1\d{2})\.py$", path.name)
    )
    require(not versioned_runtime, f"versioned runtime modules remain: {versioned_runtime}")

    modules = {path.stem for path in COMPONENT.glob("*.py")}
    missing_imports: dict[str, list[str]] = {}
    for path in COMPONENT.glob("*.py"):
        unresolved = sorted(local_import_targets(path) - modules)
        if unresolved:
            missing_imports[path.name] = unresolved
    require(not missing_imports, f"unresolved local imports: {missing_imports}")

    current_runtime = "\n".join(
        path.read_text(encoding="utf-8")
        for path in COMPONENT.glob("*.py")
        if path.name != "legacy_migration.py"
    )
    for old_name in (
        "default_options_090",
        "migrate_options_090",
        "CLIENT_MODE_ACTIVE_ONLY",
        "CLIENT_MODE_ALLOWLIST",
        "CONF_CLIENT_MODE",
        "CONF_IGNORED_PLAYER_KEYS",
        "CONF_IGNORED_REPORTED_DEVICE_IDS",
    ):
        require(old_name not in current_runtime, f"legacy runtime name remains: {old_name}")
    require(
        (COMPONENT / "legacy_migration.py").exists(),
        "legacy migration isolation missing",
    )

    versioned_tests = sorted(
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("*.py")
        if re.search(r"_(?:0\d{2}|1\d{2})\.py$", path.name)
    )
    require(not versioned_tests, f"versioned current tests remain: {versioned_tests}")
    require(
        (ROOT / "tests" / "migration" / "test_legacy_options.py").exists(),
        "published upgrade coverage is not isolated under tests/migration",
    )
    require(
        not (ROOT / "docs" / "specs").exists(),
        "obsolete public specification tree remains",
    )

    expected_scripts = {
        "build_package.py",
        "prepare_automatic_release.py",
        "read_version.py",
        "secret_scan.py",
        "validate_legacy_migration_contract.py",
        "validate_repository_references.py",
        "validate_stable_contract.py",
    }
    actual_scripts = {path.name for path in (ROOT / "scripts").glob("*.py")}
    require(
        actual_scripts == expected_scripts,
        f"script inventory differs: {sorted(actual_scripts ^ expected_scripts)}",
    )

    expected_workflows = {
        "dependabot-automerge.yml",
        "hacs.yml",
        "hassfest.yml",
        "quality.yml",
        "release.yml",
        "test-artifact.yml",
    }
    workflow_names = {path.name for path in WORKFLOWS.glob("*.yml")}
    require(
        workflow_names == expected_workflows,
        f"workflow inventory differs: {sorted(workflow_names ^ expected_workflows)}",
    )

    workflow_text = {
        path.name: path.read_text(encoding="utf-8") for path in WORKFLOWS.glob("*.yml")
    }
    build_workflows = {name: text for name, text in workflow_text.items() if "pip install" in text}
    require(
        set(build_workflows)
        == {
            "dependabot-automerge.yml",
            "quality.yml",
            "release.yml",
            "test-artifact.yml",
        },
        "build workflow inventory differs",
    )
    for name in ("quality.yml", "release.yml", "test-artifact.yml"):
        text = build_workflows[name]
        setup = text.find("actions/setup-python@")
        version = text.find("scripts/read_version.py")
        install = text.find("pip install")
        require(
            -1 not in {setup, version, install} and setup < version < install,
            f"unsafe startup order: {name}",
        )
        require(
            "from custom_components.emby" not in text,
            f"pre-dependency integration import: {name}",
        )

    quality = workflow_text["quality.yml"]
    require(
        '"3.13"' in quality and '"3.14"' in quality,
        "supported Python test matrix differs",
    )
    require("cancel-in-progress: true" in quality, "PR concurrency cancellation missing")
    require(quality.count("pytest -q") == 1, "Pytest matrix command should be defined once")
    require("build_package.py" not in quality, "package build is duplicated in Quality")

    package = workflow_text["test-artifact.yml"]
    require(
        "github.event.pull_request.head.sha || github.sha" in package,
        "test package is not commit-bound",
    )
    require(
        "build_package.py" in package and "embi.zip.sha256" in package,
        "test package contract differs",
    )
    for validator in (
        "validate_legacy_migration_contract.py",
        "validate_stable_contract.py",
        "validate_repository_references.py",
    ):
        require(
            validator not in package,
            f"duplicate contract work remains in test package: {validator}",
        )

    for name in ("quality.yml", "test-artifact.yml", "hacs.yml", "hassfest.yml"):
        require(
            "workflow_dispatch:" in workflow_text[name],
            f"repair validation dispatch missing: {name}",
        )

    dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    require(dependabot.count("interval: cron") == 2, "Dependabot cron schedule differs")
    require(
        dependabot.count("timezone: Europe/Berlin") == 2,
        "Dependabot timezone differs",
    )
    require(
        'cronjob: "0 3 6 * *"' in dependabot and 'cronjob: "15 3 6 * *"' in dependabot,
        "Dependabot day-six schedule differs",
    )
    require(
        dependabot.count("open-pull-requests-limit: 10") == 2,
        "Dependabot pull-request limit differs",
    )
    require(
        dependabot.count("rebase-strategy: auto") == 2,
        "Dependabot rebase strategy differs",
    )

    automerge = workflow_text["dependabot-automerge.yml"]
    require("pull_request_target:" in automerge, "Dependabot event trigger missing")
    require('cron: "23 5 * * *"' in automerge, "daily autonomous recovery missing")
    require("dependabot[bot]" in automerge, "Dependabot actor gate missing")
    for workflow_name in ("Quality", "Test package", "HACS validation", "Hassfest"):
        require(
            f'"{workflow_name}"' in automerge,
            f"required check missing: {workflow_name}",
        )
    for repair_contract in (
        "rerun-failed-jobs",
        "ruff==${RUFF_VERSION}",
        "ruff format .",
        "ruff check --fix .",
        "gh workflow run",
        "embi-autonomous-repair",
    ):
        require(repair_contract in automerge, f"repair contract missing: {repair_contract}")
    require(
        "issues/${pr_number}/comments" not in automerge,
        "autonomous repair still posts noisy pull-request comments",
    )
    require(
        'pulls/${pr_number}"' in automerge and '-f body="${updated_body}"' in automerge,
        "silent exhausted-head marker missing",
    )
    require("merge_method=squash" in automerge, "Dependabot squash merge missing")

    release = workflow_text["release.yml"]
    require("pull_request:" not in release, "legacy release PR trigger remains")
    require("push:" not in release, "per-push release trigger remains")
    require(
        "schedule:" in release and 'cron: "47 4 * * *"' in release,
        "daily stable recovery trigger missing",
    )
    require(
        "scripts/prepare_automatic_release.py" in release,
        "automatic patch preparation missing",
    )
    require("cancel-in-progress: false" in release, "stable release may be cancelled")
    require(
        "Pin candidate release commit through protected pull request" in release
        and "git push --force-with-lease origin" in release,
        "protected release candidate publication differs",
    )
    require(
        "git push origin HEAD:main" not in release,
        "direct protected-main push remains",
    )
    require(
        "Allow GitHub Actions to create and approve pull requests" in release
        and "Resource not accessible by integration" in release,
        "release pull-request permission handling missing",
    )
    require(
        "git tag -a" in release and "make_latest: true" in release,
        "stable publication contract differs",
    )
    require(
        "gh release download" in release and "cmp dist/embi.zip" in release,
        "asset provenance verification missing",
    )

    all_text = "\n".join(workflow_text.values())
    for script in expected_scripts:
        require(
            f"scripts/{script}" in all_text
            or f"scripts/{script}" in (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
            or f"scripts/{script}" in (ROOT / "RELEASING.md").read_text(encoding="utf-8"),
            f"script has no workflow or documented caller: {script}",
        )

    removed_paths = (
        "docs/PROJECT_STATE.md",
        "docs/development.md",
        "docs/migration-from-core.md",
        "docs/release-checklist.md",
        "docs/repository-governance.md",
        "tests/test_repository_contracts.py",
        "tests/migration/test_frozen_spec_contract.py",
    )
    for relative in removed_paths:
        require(not (ROOT / relative).exists(), f"obsolete duplicate remains: {relative}")
    require((ROOT / "RELEASING.md").exists(), "authoritative release documentation missing")

    current_public_docs = [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "ROADMAP.md",
        ROOT / "SECURITY.md",
        ROOT / "RELEASING.md",
        *sorted((ROOT / "docs").glob("*.md")),
    ]
    for path in current_public_docs:
        content = path.read_text(encoding="utf-8")
        require(
            not re.search(r"\bv?0\.[0-8]\.", content),
            f"obsolete public version reference: {path.relative_to(ROOT)}",
        )
        for forbidden in ("ChatGPT", "AI agent", "release-request PR", "finalizer PR"):
            if path.name != "RELEASING.md":
                require(
                    forbidden not in content,
                    f"internal release language remains in {path.relative_to(ROOT)}",
                )

    validate_markdown_links()

    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    english = json.loads((COMPONENT / "translations" / "en.json").read_text(encoding="utf-8"))
    german = json.loads((COMPONENT / "translations" / "de.json").read_text(encoding="utf-8"))
    require(strings == english, "strings.json and English translation differ")
    require(
        translation_paths(strings) == translation_paths(german),
        "German translation key structure differs",
    )

    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    constants = (COMPONENT / "const.py").read_text(encoding="utf-8")
    require(manifest["version"] == "1.0.3", "cleanup changed manifest version")
    require('VERSION = "1.0.3"' in constants, "cleanup changed runtime version")
    print("Repository baseline and translation parity passed")


if __name__ == "__main__":
    main()
