from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"
VERSION = "0.9.9"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    manifest = json.loads(text("custom_components/emby/manifest.json"))
    constants = text("custom_components/emby/const.py")
    strings = json.loads(text("custom_components/emby/strings.json"))
    english = json.loads(text("custom_components/emby/translations/en.json"))
    german = json.loads(text("custom_components/emby/translations/de.json"))
    api = text("custom_components/emby/api.py")
    models = text("custom_components/emby/models.py")
    execution = text("custom_components/emby/maintenance_cycle_execute.py")
    flow = text("custom_components/emby/options_flow_098.py")
    cleanup = text("custom_components/emby/options_cleanup.py")
    devices = text("custom_components/emby/options_devices_099.py")
    options_model = text("custom_components/emby/options_model.py")
    reconciliation = text("custom_components/emby/player_reconciliation_099.py")
    diagnostics = text("custom_components/emby/diagnostics.py")
    sensor_options = text("custom_components/emby/options_sensors.py")
    sensor_registry = text("custom_components/emby/sensor_registry.py")
    sensors = text("custom_components/emby/sensor.py")
    readme = text("README.md")
    hacs = json.loads(text("hacs.json"))
    quality = text(".github/workflows/quality.yml")
    package = text(".github/workflows/test-artifact.yml")
    release = text(".github/workflows/release.yml")

    require(manifest["version"] == VERSION, "manifest version differs")
    require(f'VERSION = "{VERSION}"' in constants, "runtime version differs")
    require('PLATFORMS = ["media_player", "sensor"]' in constants, "sensor platform missing")
    require("OPTIONS_SCHEMA_VERSION = 3" in constants, "options schema differs")
    require("REGISTRY_RECONCILIATION_VERSION = 2" in constants, "reconciliation differs")
    require(
        "SENSOR_ENTITY_IDS" in constants and "emby_users_watching" in constants,
        "canonical sensor identity missing",
    )
    require(strings == english, "English translation source differs")
    require(_paths(strings) == _paths(german), "translation structures differ")
    require(
        hacs.get("zip_release") is True and hacs.get("filename") == "embi.zip",
        "HACS ZIP contract differs",
    )

    require('menu.insert(1, "sensors")' in flow, "sensor menu entry missing")
    require("SensorsOptionsMixin" in flow, "sensor options mixin missing")
    require("remove_disabled_sensor_entities" in flow, "sensor registry follow-up missing")
    require("report.report_version >= 2" in cleanup, "versioned recent UI count missing")
    require(
        "Not recorded yet" in cleanup and "Noch nicht erfasst" in cleanup,
        "legacy report copy missing",
    )
    require('placeholders["age_limit"] = str(age_limit)' in flow, "dynamic age placeholder missing")
    require(
        "skipped_recent" in models and "skipped_recent" in execution,
        "persistent recent count missing",
    )
    require(
        "report_version" in models and '"report_version" not in data' in models,
        "report version migration missing",
    )

    require('self._request("GET", "/Items/Counts")' in api, "Items/Counts endpoint missing")
    require('self._request("GET", "/Sessions")' in api, "Sessions endpoint missing")
    require(
        'play_state.get("IsPaused") is not False' in api,
        "paused/unclear session protection missing",
    )
    require(
        "UpdateFailed" in sensors and "async_refresh()" in sensors,
        "sensor unavailable behavior differs",
    )
    require(
        "entity.platform != DOMAIN" in sensor_options, "sensor platform ownership check missing"
    )
    require(
        "entity.config_entry_id != entry.entry_id" in sensor_options,
        "sensor config-entry ownership check missing",
    )
    require(
        "async_update_entity" in sensor_registry and "new_entity_id" in sensor_registry,
        "in-place sensor migration missing",
    )
    require(
        "collisions" in sensor_registry and "unrelated target untouched" in sensor_registry,
        "sensor collision safety missing",
    )

    require('candidate = f"{primary} · {activity}"' in devices, "compact player label missing")
    require(
        "_sort_group_players" in devices and "last_activity is None" in devices,
        "player sorting contract missing",
    )
    require(
        "migrated.pop(user_name, None)" in options_model, "duplicate user option cleanup missing"
    )
    require("state_is_restored" in reconciliation, "restored reconciliation safety missing")
    require('"options_flow_contract": "0.9.9"' in diagnostics, "diagnostics contract differs")
    require("sensor_identity_mismatches" in diagnostics, "sensor diagnostics missing")
    require("duplicate_user_option_keys" in diagnostics, "option diagnostics missing")
    require("cleanup_report_version" in diagnostics, "report diagnostics missing")

    for entity_id in (
        "sensor.emby_movie_count",
        "sensor.emby_tv_series_count",
        "sensor.emby_tv_episode_count",
        "sensor.emby_album_count",
        "sensor.emby_song_count",
        "sensor.emby_users_watching",
    ):
        require(entity_id in readme, f"README misses {entity_id}")
    require(
        "YAML" in readme and "restart home assistant" in readme.casefold(),
        "YAML collision guidance missing",
    )
    for forbidden in ("Gerry", "ChatGPT", "AI agent", "Upgrade to 0.9.7"):
        require(forbidden not in readme, f"public README contains {forbidden}")

    for workflow in (quality, package, release):
        require("python scripts/build_package.py" in workflow, "shared package builder missing")
        require("embi.zip.sha256" in workflow, "checksum validation missing")
    require("pull_request:" in release and "closed" in release, "merged-PR release trigger missing")
    require("python scripts/read_version.py" in release, "dependency-free version reader missing")
    require("FETCH_HEAD" in release and "origin/main" not in release, "fresh main check differs")
    require(
        "from custom_components.emby.const import VERSION" not in release, "early HA import remains"
    )
    require(
        "git tag -a" in release and "make_latest: true" in release,
        "stable release contract differs",
    )
    require(
        "gh release download" in release and "cmp dist/embi.zip" in release,
        "asset verification missing",
    )

    print(f"Stable {VERSION} repository contract passed")


def _paths(value, prefix=()):
    result = set()
    if isinstance(value, dict):
        for key, child in value.items():
            current = (*prefix, str(key))
            result.add(current)
            result.update(_paths(child, current))
    return result


if __name__ == "__main__":
    main()
