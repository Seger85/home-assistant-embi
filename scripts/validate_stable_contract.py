from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"
EXPECTED_VERSION = "0.3.0"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def key_paths(value: Any, prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    if not isinstance(value, Mapping):
        return set()
    paths: set[tuple[str, ...]] = set()
    for key, child in value.items():
        path = (*prefix, str(key))
        paths.add(path)
        paths.update(key_paths(child, path))
    return paths


def main() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    constants = (COMPONENT / "const.py").read_text(encoding="utf-8")
    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    english = json.loads((COMPONENT / "translations" / "en.json").read_text(encoding="utf-8"))
    german = json.loads((COMPONENT / "translations" / "de.json").read_text(encoding="utf-8"))
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    workflows = {
        name: (ROOT / ".github" / "workflows" / path).read_text(encoding="utf-8")
        for name, path in {
            "Quality": "quality.yml",
            "Test package": "test-artifact.yml",
            "Release": "release.yml",
        }.items()
    }

    match = re.search(r'^VERSION = "([^"]+)"$', constants, re.MULTILINE)
    require(match is not None, "const.py VERSION must be a literal")
    require(manifest.get("version") == EXPECTED_VERSION, "Manifest is not stable 0.3.0")
    require(match.group(1) == EXPECTED_VERSION, "const.py is not stable 0.3.0")
    require(manifest.get("requirements") == ["pyEmby==1.10"], "pyEmby pin differs")
    require(manifest.get("loggers") == ["pyemby"], "pyEmby logger contract differs")
    require(strings == english, "English translation source differs")
    require(key_paths(strings) == key_paths(german), "German translation structure differs")
    require(hacs.get("zip_release") is True, "HACS ZIP contract missing")
    require(hacs.get("filename") == "embi.zip", "HACS filename differs")
    require(
        hacs.get("hide_default_branch") is True,
        "Default branch fallback must be hidden",
    )

    component_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in COMPONENT.rglob("*")
        if path.is_file() and path.suffix in {".py", ".json"}
    )
    for obsolete in (
        "CONF_SERVER_CLEANUP_API_KEY",
        "CONF_AUTO_CLEANUP_CONFIRMATION_TEXT",
        "CONF_ADD_DELETED_TO_IGNORED",
    ):
        require(obsolete not in component_text, f"Obsolete symbol remains: {obsolete}")

    require('PLATFORMS = ["media_player"]' in constants, "Only media_player is allowed")
    require("Store(" in (COMPONENT / "maintenance_store.py").read_text(), "Store missing")
    require(
        "OptionsDraft.from_options" in (COMPONENT / "options_flow.py").read_text(),
        "Draft missing",
    )

    for name, workflow in workflows.items():
        require(
            "python scripts/build_package.py" in workflow,
            f"{name} needs shared builder",
        )
        require("embi.zip.sha256" in workflow, f"{name} needs checksum validation")

    quality = workflows["Quality"]
    require("BUILD_COMMIT" in quality, "Quality needs commit binding")

    test_package = workflows["Test package"]
    require("BUILD_COMMIT" in test_package, "Test package needs commit binding")
    require(
        "softprops/action-gh-release" not in test_package,
        "Test package must stay private",
    )
    require("gh release" not in test_package, "Test package must stay private")

    release = workflows["Release"]
    require("origin/develop" in release, "Prerelease source constraint missing")
    require("origin/main" in release, "Stable source constraint missing")
    require("prerelease:" in release, "Prerelease flag missing")
    require("make_latest:" in release, "Latest flag missing")
    require("gh release download" in release, "Asset revalidation missing")
    require(
        "cmp dist/embi.zip verify-release/embi.zip" in release, "Published ZIP comparison missing"
    )
    publish_block = release.split("files: |", 1)[1].split("fail_on_unmatched_files", 1)[0]
    require("dist/embi.zip" in publish_block, "Release ZIP asset missing")
    require("dist/embi.zip.sha256" in publish_block, "Release checksum asset missing")
    require("BUILD_COMMIT" not in publish_block, "BUILD_COMMIT must not be a release asset")

    print("Stable 0.3.0 repository contract passed")


if __name__ == "__main__":
    main()
