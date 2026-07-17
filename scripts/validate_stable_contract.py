from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"
EXPECTED_VERSION = "0.9.1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def key_paths(value: Any, prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    if not isinstance(value, Mapping):
        return set()
    result: set[tuple[str, ...]] = set()
    for key, child in value.items():
        path = (*prefix, str(key))
        result.add(path)
        result.update(key_paths(child, path))
    return result


def main() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    constants = (COMPONENT / "const.py").read_text(encoding="utf-8")
    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    english = json.loads((COMPONENT / "translations" / "en.json").read_text(encoding="utf-8"))
    german = json.loads((COMPONENT / "translations" / "de.json").read_text(encoding="utf-8"))
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    options = (COMPONENT / "options_flow.py").read_text(encoding="utf-8")
    devices = (COMPONENT / "options_devices.py").read_text(encoding="utf-8")
    cleanup = (COMPONENT / "options_cleanup.py").read_text(encoding="utf-8")
    ha_cleanup = (COMPONENT / "options_ha_cleanup.py").read_text(encoding="utf-8")
    context = (COMPONENT / "player_context.py").read_text(encoding="utf-8")
    actions = (COMPONENT / "player_actions.py").read_text(encoding="utf-8")
    quality = (ROOT / ".github/workflows/quality.yml").read_text(encoding="utf-8")
    package = (ROOT / ".github/workflows/test-artifact.yml").read_text(encoding="utf-8")
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    match = re.search(r'^VERSION = "([^"]+)"$', constants, re.MULTILINE)
    require(match is not None, "const.py VERSION must be a literal")
    require(manifest.get("version") == EXPECTED_VERSION, "Manifest version differs")
    require(match.group(1) == EXPECTED_VERSION, "Runtime version differs")
    require(strings == english, "English translation source differs")
    require(key_paths(strings) == key_paths(german), "Translation structures differ")
    require(hacs.get("zip_release") is True, "HACS ZIP contract missing")
    require(hacs.get("filename") == "embi.zip", "HACS filename differs")
    require(hacs.get("hide_default_branch") is True, "Default branch must be hidden")

    require('menu_options = ["ha_players", "server_cleanup"]' in options, "Root menu differs")
    require('menu_options.append("review_changes")' in options, "Review entry missing")
    require("async_step_back_to_init" in options, "Back navigation missing")
    require("OptionsDraft.from_options" in options, "Draft model missing")
    require("CONF_CONFIRM_APPLY" not in options, "Apply confirmation remains")
    require("CONF_CONFIRM_DISCARD" not in options, "Discard confirmation remains")
    require("GROUP_SHARED" in context, "Shared grouping missing")
    require("GROUP_UNASSIGNED" in context, "Unassigned grouping missing")
    require("CLIENT_CLASS_UNKNOWN" in context, "Unknown classification missing")
    require("technical_details" in context, "Technical details separation missing")
    require("ACTIVE_PLAYBACK_STATES" in devices, "Playback protection missing")
    require("execute_server_deletion" in cleanup, "Server execution step missing")
    require("execute_ha_removal" in ha_cleanup, "Player execution step missing")
    require("CONF_CONFIRM_SERVER_DELETION" not in cleanup, "Duplicate server confirmation remains")
    require("CONF_CONFIRM_HA_REMOVAL" not in ha_cleanup, "Duplicate player confirmation remains")
    require("async_remove_ha_players" in actions, "Player removal transaction missing")
    require("async_restore_players" in actions, "Player restoration transaction missing")

    for workflow in (quality, package, release):
        require("python scripts/build_package.py" in workflow, "Shared package builder missing")
        require("embi.zip.sha256" in workflow, "Checksum validation missing")
    require("--expected-version 0.9.1" in quality, "Quality package version differs")
    require("--expected-version 0.9.1" in package, "Test package version differs")
    require("origin/main" in release, "Stable source constraint missing")
    require("prerelease: false" in release, "Stable prerelease setting differs")
    require("make_latest: true" in release, "Stable latest setting differs")
    require("gh release download" in release, "Published asset verification missing")
    require("cmp dist/embi.zip verify-release/embi.zip" in release, "ZIP comparison missing")

    print("Stable 0.9.1 repository contract passed")


if __name__ == "__main__":
    main()
