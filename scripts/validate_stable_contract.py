from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"
VERSION = "0.9.8"


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
    sensor_options = text("custom_components/emby/options_sensors.py")
    sensors = text("custom_components/emby/sensor.py")
    readme = text("README.md")
    hacs = json.loads(text("hacs.json"))
    quality = text(".github/workflows/quality.yml")
    package = text(".github/workflows/test-artifact.yml")
    release = text(".github/workflows/release.yml")

    require(manifest["version"] == VERSION, "manifest version differs")
    require(f'VERSION = "{VERSION}"' in constants, "runtime version differs")
    require('PLATFORMS = ["media_player", "sensor"]' in constants, "sensor platform missing")
    require(strings == english, "English translation source differs")
    require(_paths(strings) == _paths(german), "translation structures differ")
    require(
        hacs.get("zip_release") is True and hacs.get("filename") == "embi.zip",
        "HACS ZIP contract differs",
    )

    require('menu.insert(1, "sensors")' in flow, "sensor menu entry missing")
    require("SensorsOptionsMixin" in flow, "sensor options mixin missing")
    require("remove_disabled_sensor_entities" in flow, "sensor registry follow-up missing")
    require(
        'placeholders["recent"] = str(report.skipped_recent)' in flow,
        "recent UI count missing",
    )
    require(
        'placeholders["age_limit"] = str(age_limit)' in flow,
        "dynamic age placeholder missing",
    )
    require(
        "skipped_recent" in models and "skipped_recent" in execution,
        "persistent recent count missing",
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
        "entity.platform != DOMAIN" in sensor_options,
        "sensor platform ownership check missing",
    )
    require(
        "entity.config_entry_id != entry.entry_id" in sensor_options,
        "sensor config-entry ownership check missing",
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
    require(
        "YAML" in readme and "restart home assistant" in readme.casefold(),
        "YAML collision guidance missing",
    )
    for forbidden in ("Gerry", "ChatGPT", "AI agent", "Upgrade to 0.9.7"):
        require(forbidden not in readme, f"public README contains {forbidden}")

    for workflow in (quality, package, release):
        require("python scripts/build_package.py" in workflow, "shared package builder missing")
        require("embi.zip.sha256" in workflow, "checksum validation missing")
    require(
        "pull_request:" in release and "closed" in release,
        "merged-PR release trigger missing",
    )
    require("python scripts/read_version.py" in release, "dependency-free version reader missing")
    require("FETCH_HEAD" in release and "origin/main" not in release, "fresh main check differs")
    require(
        "from custom_components.emby.const import VERSION" not in release,
        "early HA import remains",
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
