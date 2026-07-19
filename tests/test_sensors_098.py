from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from custom_components.emby.api import EmbyApiClient, EmbyApiError
from custom_components.emby.const import (
    CONF_ENABLED_SENSORS,
    SENSOR_ALBUM_COUNT,
    SENSOR_KEYS,
    SENSOR_MOVIE_COUNT,
    SENSOR_SONG_COUNT,
    SENSOR_TV_EPISODE_COUNT,
    SENSOR_TV_SERIES_COUNT,
    SENSOR_USERS_WATCHING,
)
from custom_components.emby.models import CleanupRunReport
from custom_components.emby.options_model import default_options_090, migrate_options_090
from custom_components.emby.options_sensors import (
    remove_disabled_sensor_entities,
    sensor_unique_id,
)

COMPONENT = Path("custom_components/emby")


async def sensor_values(counts, sessions):
    client = object.__new__(EmbyApiClient)

    async def request(_method, path, **_kwargs):
        return counts if path == "/Items/Counts" else sessions

    client._request = request
    return await client.async_get_sensor_data()


@pytest.mark.asyncio
async def test_all_values_unique_users_and_paused_or_unclear_sessions() -> None:
    values = await sensor_values(
        {
            "MovieCount": 12,
            "SeriesCount": 34,
            "EpisodeCount": 567,
            "AlbumCount": 89,
            "SongCount": 1234,
        },
        [
            {"UserId": "A", "NowPlayingItem": {"Id": "one"}, "PlayState": {"IsPaused": False}},
            {"UserId": "A", "NowPlayingItem": {"Id": "two"}, "PlayState": {"IsPaused": False}},
            {
                "UserName": "Sam",
                "NowPlayingItem": {"Id": "three"},
                "PlayState": {"IsPaused": False},
            },
            {
                "UserName": "Paused",
                "NowPlayingItem": {"Id": "four"},
                "PlayState": {"IsPaused": True},
            },
            {"UserName": "Unclear", "NowPlayingItem": {"Id": "five"}, "PlayState": {}},
            {"UserName": "Idle", "PlayState": {"IsPaused": False}},
        ],
    )
    assert values == {
        SENSOR_MOVIE_COUNT: 12,
        SENSOR_TV_SERIES_COUNT: 34,
        SENSOR_TV_EPISODE_COUNT: 567,
        SENSOR_ALBUM_COUNT: 89,
        SENSOR_SONG_COUNT: 1234,
        SENSOR_USERS_WATCHING: 2,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("counts", "sessions"),
    [
        ([], []),
        ({}, {}),
        ({"MovieCount": None}, []),
        (
            {
                "MovieCount": 1,
                "SeriesCount": 2,
                "EpisodeCount": 3,
                "AlbumCount": 4,
                "SongCount": -1,
            },
            [],
        ),
    ],
)
async def test_malformed_api_data_never_becomes_false_zero(counts, sessions) -> None:
    with pytest.raises(EmbyApiError):
        await sensor_values(counts, sessions)


def test_defaults_upgrade_and_exact_entity_id_contract() -> None:
    defaults = default_options_090()
    assert defaults[CONF_ENABLED_SENSORS] == list(SENSOR_KEYS)
    migrated, _ = migrate_options_090({}, [], new_install=False)
    assert migrated[CONF_ENABLED_SENSORS] == list(SENSOR_KEYS)
    migrated, _ = migrate_options_090(
        {CONF_ENABLED_SENSORS: [SENSOR_MOVIE_COUNT, "unknown", SENSOR_SONG_COUNT]},
        [],
    )
    assert migrated[CONF_ENABLED_SENSORS] == [SENSOR_MOVIE_COUNT, SENSOR_SONG_COUNT]

    source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    for object_id in (
        "emby_movie_count",
        "emby_tv_series_count",
        "emby_tv_episode_count",
        "emby_album_count",
        "emby_song_count",
        "emby_users_watching",
    ):
        assert f'object_id="{object_id}"' in source
    assert "UpdateFailed" in source
    assert "await coordinator.async_refresh()" in source


class FakeRegistry:
    def __init__(self, entries):
        self.entities = {entry.entity_id: entry for entry in entries}
        self.removed = []

    def async_remove(self, entity_id):
        self.removed.append(entity_id)
        self.entities.pop(entity_id, None)


def entity(entity_id, unique_id, *, entry_id="entry", platform="emby", domain="sensor"):
    return SimpleNamespace(
        entity_id=entity_id,
        unique_id=unique_id,
        config_entry_id=entry_id,
        platform=platform,
        domain=domain,
    )


def test_disabled_sensor_removal_is_owned_and_never_deletes_yaml_or_foreign_entities() -> None:
    own_movie = entity("sensor.emby_movie_count", sensor_unique_id("entry", SENSOR_MOVIE_COUNT))
    own_song = entity("sensor.emby_song_count", sensor_unique_id("entry", SENSOR_SONG_COUNT))
    yaml_collision = entity(
        "sensor.emby_album_count", "yaml_unique", entry_id=None, platform="template"
    )
    foreign_entry = entity(
        "sensor.emby_tv_series_count",
        sensor_unique_id("other", SENSOR_TV_SERIES_COUNT),
        entry_id="other",
    )
    wrong_platform = entity(
        "sensor.emby_tv_episode_count",
        sensor_unique_id("entry", SENSOR_TV_EPISODE_COUNT),
        platform="other",
    )
    registry = FakeRegistry([own_movie, own_song, yaml_collision, foreign_entry, wrong_platform])
    hass = SimpleNamespace(registry=registry)
    entry_value = SimpleNamespace(entry_id="entry")

    removed = remove_disabled_sensor_entities(hass, entry_value, frozenset({SENSOR_SONG_COUNT}))
    assert removed == 1
    assert registry.removed == ["sensor.emby_movie_count"]


def test_skipped_recent_roundtrip_is_persistent() -> None:
    report = CleanupRunReport(age_threshold_days=365, skipped_recent=17)
    restored = CleanupRunReport.from_dict(report.as_dict())
    assert restored.skipped_recent == 17
    assert restored.as_dict()["skipped_recent"] == 17
