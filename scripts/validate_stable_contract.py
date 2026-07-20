from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"
VERSION = "1.0.2"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def paths(value, prefix=()):
    result = set()
    if isinstance(value, dict):
        for key, child in value.items():
            current = (*prefix, str(key))
            result.add(current)
            result.update(paths(child, current))
    return result


def main() -> None:
    manifest = json.loads(text("custom_components/emby/manifest.json"))
    constants = text("custom_components/emby/const.py")
    strings = json.loads(text("custom_components/emby/strings.json"))
    english = json.loads(text("custom_components/emby/translations/en.json"))
    german = json.loads(text("custom_components/emby/translations/de.json"))
    flow = text("custom_components/emby/options_flow.py")
    devices = text("custom_components/emby/options_devices.py")
    options_runtime = text("custom_components/emby/options_runtime.py")
    sensor_options = text("custom_components/emby/options_sensors.py")
    sensor_registry = text("custom_components/emby/sensor_registry.py")
    player_action_common = text("custom_components/emby/player_action_common.py")
    player_actions = text("custom_components/emby/player_actions.py")
    player_context = text("custom_components/emby/player_context.py")
    reconciliation = text("custom_components/emby/player_reconciliation.py")
    media_player = text("custom_components/emby/media_player.py")
    entry_setup = text("custom_components/emby/entry_setup.py")
    diagnostics = text("custom_components/emby/diagnostics.py")
    legacy_migration = text("custom_components/emby/legacy_migration.py")
    readme = text("README.md")
    hacs = json.loads(text("hacs.json"))
    quality = text(".github/workflows/quality.yml")
    package = text(".github/workflows/test-artifact.yml")
    release = text(".github/workflows/release.yml")

    require(manifest["version"] == VERSION, "manifest version differs")
    require(f'VERSION = "{VERSION}"' in constants, "runtime version differs")
    require("CONFIG_ENTRY_MINOR_VERSION = 2" in constants, "minor version differs")
    require("OPTIONS_SCHEMA_VERSION = 4" in constants, "options schema differs")
    require(
        "REGISTRY_RECONCILIATION_VERSION = 3" in constants,
        "reconciliation migration differs",
    )
    require(strings == english, "English translation source differs")
    require(paths(strings) == paths(german), "translation structures differ")
    require(
        hacs.get("zip_release") is True and hacs.get("filename") == "embi.zip",
        "HACS ZIP contract differs",
    )

    require((COMPONENT / "legacy_migration.py").exists(), "legacy upgrade isolation missing")
    require("def migrate_options(" in legacy_migration, "published upgrade path missing")
    require(
        "from .legacy_migration import legacy_cleanup_completed, migrate_options" in entry_setup,
        "entry setup does not use isolated legacy migration",
    )

    require("def owned_exact(" in player_action_common, "exact ownership helper missing")
    for symbol in (
        "class PlayerActionItem",
        "class PlayerActionResult",
        "def find_context(",
        "def fresh_catalog(",
        "def update_options_and_reload(",
        "def record_action(",
    ):
        require(symbol not in player_action_common, f"dead common helper remains: {symbol}")
    for symbol, content in (
        ("def async_enable_ha_entities(", player_actions),
        ("def async_reconcile_invisible_player_entities(", player_actions),
        ("def async_reconcile_invisible_player_entities(", reconciliation),
        ("def group_label(", player_context),
        ("def filter_player_catalog(", player_context),
        ("def options_for_flow(", options_runtime),
        ("def render_player_rows(", options_runtime),
    ):
        require(symbol not in content, f"dead runtime symbol remains: {symbol}")

    require("SensorsOptionsMixin" in flow, "sensor flow not consolidated")
    require("menu_options = [" in flow and '"sensors",' in flow, "sensor menu missing")
    require(
        "selector.SelectSelectorConfig" in sensor_options and "multiple=True" in sensor_options,
        "stable sensor multi-select missing",
    )
    require(
        "if not count:" in flow and "return await self.async_step_init()" in flow,
        "zero-change review redirect missing",
    )
    require(
        "playback_protected_named" in devices and "blocked_players" in devices,
        "named playback blocker contract missing",
    )
    require(
        "include_technical=requested_technical" in devices,
        "technical group master contract missing",
    )
    require(
        "CONF_TECHNICAL_ACCESS_VISIBILITY] = any_visible" not in devices,
        "technical master is coupled to individual switches",
    )
    require(
        "player.playback == PLAYBACK_UNKNOWN" not in devices,
        "unknown playback blocks the whole group",
    )

    require(
        "state_can_be_removed_after_visibility_commit" in player_actions
        and "hass.states.async_remove" in player_actions,
        "state-machine cleanup missing",
    )
    require(
        "async_remove(force_remove=True)" in media_player,
        "entity-platform removal missing",
    )
    require(
        "entity: EmbyDevice | None" in media_player
        and "async_reconcile_player_visibility(" in media_player,
        "fresh-platform visibility fallback missing",
    )
    require(
        "await _async_enforce_player_visibility(hass, entry, migrated_options)" in entry_setup,
        "visibility invariant is not enforced on every setup",
    )
    require(
        entry_setup.find("await _async_enforce_player_visibility")
        > entry_setup.find("async_forward_entry_setups"),
        "visibility invariant must run after platform setup",
    )
    require(
        "if not migration_pending:\n        return" in entry_setup,
        "migration marker separation missing",
    )
    require(
        "if not invisible:" in reconciliation
        and "await _async_record_reconciliation" in reconciliation,
        "no-op reconciliation diagnostics refresh missing",
    )
    require("state_is_restored" in reconciliation, "stale-restored handling missing")
    require('"GET", "/Sessions"' in player_actions, "unknown playback revalidation missing")
    require(
        'and getattr(entity, "domain", None) == "media_player"' in player_actions
        and 'and getattr(entity, "platform", None) == DOMAIN' in player_actions
        and 'and getattr(entity, "config_entry_id", None) == entry.entry_id' in player_actions,
        "exact registry ownership contract missing",
    )
    require(
        "duplicates_removed" in sensor_registry
        and "unrelated entity remains untouched" in sensor_registry,
        "sensor duplicate migration safety missing",
    )

    for contract in (
        '"options_flow_contract": "1.0.0"',
        '"sensor_contract": "1.0.0"',
        '"player_visibility_contract": "1.0.1"',
    ):
        require(contract in diagnostics, f"diagnostics contract missing: {contract}")

    for workflow in (quality, package, release):
        setup = workflow.find("actions/setup-python@")
        version = workflow.find("scripts/read_version.py")
        install = workflow.find("pip install")
        require(
            -1 not in {setup, version, install} and setup < version < install,
            "workflow startup order differs",
        )
        require(
            "from custom_components.emby" not in workflow,
            "workflow imports integration before dependencies",
        )

    require(
        "python scripts/build_package.py" not in quality,
        "Quality duplicates package build",
    )
    for workflow in (package, release):
        require(
            "python scripts/build_package.py" in workflow,
            "shared package builder missing",
        )
        require("embi.zip.sha256" in workflow, "checksum validation missing")

    require("pull_request:" in release and "closed" in release, "merged PR trigger missing")
    require("workflow_dispatch:" not in release, "manual release path remains")
    require("cancel-in-progress: false" in release, "release concurrency differs")
    require(
        'test "${HEAD_BRANCH}" = "release/${version}"' in release,
        "canonical release branch gate missing",
    )
    require("release/${version}-final" not in release, "temporary release branch fallback remains")
    require(
        "git tag -a" in release and "make_latest: true" in release,
        "stable release differs",
    )
    require(
        "gh release download" in release and "cmp dist/embi.zip" in release,
        "published asset byte verification missing",
    )
    require(
        "FETCH_HEAD" in release and "origin/main" not in release,
        "fresh main check differs",
    )

    for entity_id in (
        "sensor.emby_movie_count",
        "sensor.emby_tv_series_count",
        "sensor.emby_tv_episode_count",
        "sensor.emby_album_count",
        "sensor.emby_song_count",
        "sensor.emby_users_watching",
    ):
        require(entity_id in readme, f"README misses {entity_id}")

    print(f"Stable {VERSION} repository contract passed")


if __name__ == "__main__":
    main()
