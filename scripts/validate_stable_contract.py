from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"
VERSION = "1.0.1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _paths(value, prefix=()):
    result = set()
    if isinstance(value, dict):
        for key, child in value.items():
            current = (*prefix, str(key))
            result.add(current)
            result.update(_paths(child, current))
    return result


def main() -> None:
    manifest = json.loads(text("custom_components/emby/manifest.json"))
    constants = text("custom_components/emby/const.py")
    strings = json.loads(text("custom_components/emby/strings.json"))
    english = json.loads(text("custom_components/emby/translations/en.json"))
    german = json.loads(text("custom_components/emby/translations/de.json"))
    flow = text("custom_components/emby/options_flow.py")
    devices = text("custom_components/emby/options_devices.py")
    sensor_options = text("custom_components/emby/options_sensors.py")
    sensor_registry = text("custom_components/emby/sensor_registry.py")
    player_actions = text("custom_components/emby/player_actions.py")
    reconciliation = text("custom_components/emby/player_reconciliation.py")
    media_player = text("custom_components/emby/media_player.py")
    entry_setup = text("custom_components/emby/entry_setup.py")
    diagnostics = text("custom_components/emby/diagnostics.py")
    options_model = text("custom_components/emby/options_model.py")
    legacy_migration = text("custom_components/emby/legacy_migration.py")
    readme = text("README.md")
    hacs = json.loads(text("hacs.json"))
    workflows = {
        name: text(f".github/workflows/{name}")
        for name in ("quality.yml", "test-artifact.yml", "release.yml")
    }

    require(manifest["version"] == VERSION, "manifest version differs")
    require(f'VERSION = "{VERSION}"' in constants, "runtime version differs")
    require("CONFIG_ENTRY_MINOR_VERSION = 2" in constants, "minor version differs")
    require("OPTIONS_SCHEMA_VERSION = 4" in constants, "options schema differs")
    require(
        "REGISTRY_RECONCILIATION_VERSION = 3" in constants,
        "reconciliation contract differs",
    )
    require(strings == english, "English translation source differs")
    require(_paths(strings) == _paths(german), "translation structures differ")
    require(
        hacs.get("zip_release") is True and hacs.get("filename") == "embi.zip",
        "HACS ZIP contract differs",
    )

    for forbidden in (
        "options_flow_098.py",
        "options_devices_099.py",
        "player_reconciliation_099.py",
    ):
        require(
            not (COMPONENT / forbidden).exists(),
            f"versioned runtime remains: {forbidden}",
        )
    require(
        "from .options_flow import EmbyOptionsFlow"
        in text("custom_components/emby/config_flow.py"),
        "config flow does not use canonical options flow",
    )
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
        "technical master is still coupled to individual switches",
    )
    require(
        "player.playback == PLAYBACK_UNKNOWN" not in devices,
        "unknown playback still blocks the whole group",
    )
    require(
        "state_can_be_removed_after_visibility_commit" in player_actions
        and "hass.states.async_remove" in player_actions,
        "state-machine cleanup missing",
    )
    require(
        "async_remove(force_remove=True)" in media_player,
        "entity-platform visibility removal missing",
    )
    require(
        "requested_keys=(device_id,)" in media_player,
        "fresh-platform exact visibility reconciliation missing",
    )
    require(
        "await _async_enforce_player_visibility(hass, entry, migrated_options)" in entry_setup,
        "visibility is not enforced on every setup",
    )
    require(
        "migration_pending = reconciliation_version < REGISTRY_RECONCILIATION_VERSION"
        in entry_setup,
        "migration marker is not separated from recurring visibility enforcement",
    )
    require("state_is_restored" in reconciliation, "stale-restored handling missing")
    require(
        "requested_keys: Iterable[str] | None = None" in reconciliation,
        "exact reconciliation scope missing",
    )
    require(
        "duplicates_removed" in sensor_registry
        and "unrelated entity remains untouched" in sensor_registry,
        "sensor duplicate migration safety missing",
    )
    require(
        "apply_legacy_option_migration" in options_model
        and "LEGACY_OPTION_KEYS" in legacy_migration,
        "isolated legacy migration adapter missing",
    )
    require(
        "default_options_090" not in options_model and "migrate_options_090" not in options_model,
        "versioned option aliases remain",
    )
    for contract in (
        '"options_flow_contract": "1.0.0"',
        '"sensor_contract": "1.0.0"',
        '"player_visibility_contract": "1.0.1"',
    ):
        require(contract in diagnostics, f"diagnostics contract missing: {contract}")
    require(
        "registry_reconciliation_failures" in diagnostics,
        "bounded reconciliation diagnostics missing",
    )

    for workflow in workflows.values():
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
            "python scripts/build_package.py" in workflow,
            "shared package builder missing",
        )
        require("embi.zip.sha256" in workflow, "checksum validation missing")
        require(
            "validate_legacy_migration_contract.py" in workflow,
            "legacy migration contract is not validated",
        )

    release = workflows["release.yml"]
    require("pull_request:" in release and "closed" in release, "merged PR trigger missing")
    require("cancel-in-progress: false" in release, "release concurrency differs")
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
