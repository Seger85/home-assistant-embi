from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "custom_components" / "emby" / "manifest.json"
CONSTANTS = ROOT / "custom_components" / "emby" / "const.py"


def manifest_version() -> str:
    value = json.loads(MANIFEST.read_text(encoding="utf-8")).get("version")
    if not isinstance(value, str) or not value:
        raise RuntimeError("manifest version is missing")
    return value


def constant_version() -> str:
    tree = ast.parse(CONSTANTS.read_text(encoding="utf-8"), filename=str(CONSTANTS))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "VERSION" for target in node.targets
        ):
            continue
        value = ast.literal_eval(node.value)
        if isinstance(value, str) and value:
            return value
        break
    raise RuntimeError("VERSION literal is missing from const.py")


def main() -> None:
    manifest = manifest_version()
    constant = constant_version()
    if manifest != constant:
        raise RuntimeError(f"manifest/const version mismatch: {manifest} != {constant}")
    print(manifest)


if __name__ == "__main__":
    main()
