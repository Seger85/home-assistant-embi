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

    expected_scripts = {
        "build_package.py",
        "read_version.py",
        "secret_scan.py",
        "validate_repository_references.py",
        "validate_spec_contract.py",
        "validate_stable_contract.py",
    }
    actual_scripts = {path.name for path in (ROOT / "scripts").glob("*.py")}
    require(
        actual_scripts == expected_scripts,
        f"script inventory differs: {sorted(actual_scripts ^ expected_scripts)}",
    )

    workflow_text = "\n".join(path.read_text(encoding="utf-8") for path in WORKFLOWS.glob("*.yml"))
    for script in expected_scripts:
        if script == "read_version.py":
            require(
                workflow_text.count("scripts/read_version.py") >= 3,
                "version reader is not used by every build/release workflow",
            )
        else:
            require(
                f"scripts/{script}" in workflow_text
                or script in {"build_package.py", "validate_spec_contract.py"},
                f"script is not referenced by CI: {script}",
            )

    forbidden = (
        "from custom_components.emby.const import VERSION",
        'python -c "from custom_components.emby',
        "python -c 'from custom_components.emby",
    )
    for value in forbidden:
        require(
            value not in workflow_text,
            f"forbidden pre-dependency import remains: {value}",
        )

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
