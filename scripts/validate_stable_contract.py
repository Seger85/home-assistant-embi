from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"
EXPECTED_VERSION = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))["version"]


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
    maintenance = (COMPONENT / "maintenance_common.py").read_text(encoding="utf-8")
    context = (COMPONENT / "player_context.py").read_text(encoding="utf-8")
    actions = (COMPONENT / "player_actions.py").read_text(encoding="utf-8")
    quality = (ROOT / ".github/workflows/quality.yml").read_text(encoding="utf-8")
    package = (ROOT / ".github/workflows/test-artifact.yml").read_text(encoding="utf-8")
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    match = re.search(r'^VERSION = "([^"]+)"$', constants, re.MULTILINE)
    require(match is not None, "const.py VERSION must be a literal")
    require(manifest.get("version") == EXPECTED_VERSION, "Manifest version differs")
    require(match.group(1) == EXPECTED_VERSION, "Runtime version differs")
    require(EXPECTED_VERSION == "0.9.7", "Stable contract version differs")
    require(strings == english, "English translation source differs")
    require(key_paths(strings) == key_paths(german), "Translation structures differ")
    require(hacs.get("zip_release") is True, "HACS ZIP contract missing")
    require(hacs.get("filename") == "embi.zip", "HACS filename differs")
    require(hacs.get("hide_default_branch") is True, "Default branch must be hidden")

    require(
        'menu_options = ["ha_players", "automatic_cleanup", "server_history_check"]' in options,
        "Direct root menu differs",
    )
    require('menu_options.append("review_changes")' in options, "Review entry missing")
    require("OptionsDraft.from_options" in options, "Draft model missing")
    require("CONF_SEARCH_QUERY" not in devices, "Player search remains")
    require("CONF_PLAYER_SORT_ORDER" not in devices, "Player sort selector remains")
    require("def _sort_group_players(players):" in devices, "Fixed player sort missing")
    require("PLAYBACK_UNKNOWN" in devices, "Unknown playback protection missing")
    require("navigation_selector" not in devices, "Back-only player actions remain")
    require("selector.BooleanSelector()" in devices, "Direct player switches missing")
    require("CONF_MANUAL_CLEANUP_SCOPE" not in cleanup, "Manual scope UI remains")
    require("manual_age_preset" not in cleanup, "Manual age UI remains")
    require("ignore_age=True" in cleanup, "Age-independent manual cleanup missing")
    require("remove_ha_entities=True" in cleanup, "Manual server lifecycle cleanup missing")
    require("async_step_last_cleanup_run" in cleanup, "Compatibility redirect missing")
    require(
        "return await self.async_step_automatic_cleanup()" in cleanup,
        "Last-run redirect differs",
    )
    require(
        "options_flow_contract" in (COMPONENT / "diagnostics.py").read_text(),
        "0.9.7 diagnostics contract missing",
    )
    require("ACTIVE_STATES" in maintenance, "Cleanup active-state protection missing")
    require('"unknown"' in maintenance, "Cleanup unknown-state protection missing")
    require("state_is_restored" in maintenance, "Stale-restored distinction missing")
    require("CONF_SEARCH_QUERY" not in ha_cleanup, "Legacy player cleanup search remains")
    require("GROUP_SHARED" in context, "Shared grouping missing")
    require("GROUP_UNASSIGNED" in context, "Unassigned grouping missing")
    require("CLIENT_CLASS_UNKNOWN" in context, "Unknown classification missing")
    require(
        "async_remove_hidden_player_entities" in actions,
        "Hidden-player transaction missing",
    )
    require("async_remove_ha_players" in actions, "Player removal transaction missing")
    require("async_restore_players" in actions, "Player restoration transaction missing")

    serialized = json.dumps(strings, ensure_ascii=False)
    require("manual_cleanup_scope" not in serialized, "Raw manual scope appears in UI")
    require("search_query" not in serialized, "Search field appears in UI")
    require("player_sort_order" not in serialized, "Sort field appears in UI")

    for workflow in (quality, package, release):
        require(
            "python scripts/build_package.py" in workflow,
            "Shared package builder missing",
        )
        require("embi.zip.sha256" in workflow, "Checksum validation missing")
    require(
        "pull_request:" in release and "closed" in release,
        "Merged-PR release trigger missing",
    )
    require("workflow_dispatch:" in release, "Manual recovery trigger missing")
    require("scripts/read_version.py" in release, "Dependency-free version reader missing")
    require(
        "from custom_components.emby.const import VERSION" not in release,
        "Release imports the HA package before dependencies",
    )
    require(
        "FETCH_HEAD" in release and "origin/main" not in release,
        "Fresh main identity check differs",
    )
    require("git tag -a" in release, "Annotated tag creation missing")
    require("prerelease: false" in release, "Stable prerelease setting differs")
    require("make_latest: true" in release, "Stable latest setting differs")
    require("gh release download" in release, "Published asset verification missing")
    require("cmp dist/embi.zip verify-release/embi.zip" in release, "ZIP comparison missing")

    print(f"Stable {EXPECTED_VERSION} repository contract passed")


if __name__ == "__main__":
    main()
