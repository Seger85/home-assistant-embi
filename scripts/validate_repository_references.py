from __future__ import annotations

import ast
import json
import re
from pathlib import Path

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


def main() -> None:
    versioned_runtime = sorted(
        path.name
        for path in COMPONENT.glob("*.py")
        if re.search(r"_(?:0\d{2}|1\d{2})\.py$", path.name)
    )
    require(not versioned_runtime, f"versioned runtime modules remain: {versioned_runtime}")

    modules = {path.stem for path in COMPONENT.glob("*.py")}
    missing: dict[str, list[str]] = {}
    for path in COMPONENT.glob("*.py"):
        unresolved = sorted(local_import_targets(path) - modules)
        if unresolved:
            missing[path.name] = unresolved
    require(not missing, f"unresolved local imports: {missing}")

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
    require((COMPONENT / "legacy_migration.py").exists(), "legacy migration isolation missing")

    versioned_tests = sorted(
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").rglob("*.py")
        if re.search(r"_(?:0\d{2}|1\d{2})\.py$", path.name)
    )
    require(not versioned_tests, f"versioned current tests remain: {versioned_tests}")
    require(
        (ROOT / "tests" / "migration" / "test_legacy_options.py").exists(),
        "published upgrade coverage is not isolated under tests/migration",
    )

    expected_scripts = {
        "build_package.py",
        "read_version.py",
        "validate_legacy_migration_contract.py",
        "secret_scan.py",
        "validate_repository_references.py",
        "validate_stable_contract.py",
    }
    actual_scripts = {path.name for path in (ROOT / "scripts").glob("*.py")}
    require(
        actual_scripts == expected_scripts,
        f"script inventory differs: {sorted(actual_scripts ^ expected_scripts)}",
    )

    workflow_names = {path.name for path in WORKFLOWS.glob("*.yml")}
    require(
        "legacy-migration-contract.yml" not in workflow_names
        and "spec-contract.yml" not in workflow_names,
        "duplicate migration/specification workflow remains",
    )
    workflow_text = "\n".join(path.read_text(encoding="utf-8") for path in WORKFLOWS.glob("*.yml"))
    require(
        workflow_text.count("scripts/read_version.py") >= 3,
        "version reader is not used by every build/release workflow",
    )
    for script in (
        "build_package.py",
        "validate_legacy_migration_contract.py",
        "secret_scan.py",
        "validate_repository_references.py",
        "validate_stable_contract.py",
    ):
        require(f"scripts/{script}" in workflow_text, f"script is not referenced by CI: {script}")

    for value in (
        "from custom_components.emby.const import VERSION",
        'python -c "from custom_components.emby',
        "python -c 'from custom_components.emby",
    ):
        require(value not in workflow_text, f"forbidden pre-dependency import remains: {value}")

    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    english = json.loads((COMPONENT / "translations" / "en.json").read_text(encoding="utf-8"))
    german = json.loads((COMPONENT / "translations" / "de.json").read_text(encoding="utf-8"))
    require(strings == english, "strings.json and English translation differ")
    require(
        translation_paths(strings) == translation_paths(german),
        "German translation key structure differs",
    )
    print("Repository references and translation parity passed")


if __name__ == "__main__":
    main()
