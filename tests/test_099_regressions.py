from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.emby import player_reconciliation_099
from custom_components.emby.const import (
    CONF_OPTIONS_SCHEMA_VERSION,
    CONF_USER_MASTER_VISIBILITY,
    OPTIONS_SCHEMA_VERSION,
    REGISTRY_RECONCILIATION_VERSION,
    SENSOR_ENTITY_IDS,
    SENSOR_KEYS,
    SENSOR_USERS_WATCHING,
)
from custom_components.emby.models import CleanupRunReport
from custom_components.emby.options_cleanup import CleanupOptionsMixin
from custom_components.emby.options_devices_099 import _player_toggle_fields, _sort_group_players
from custom_components.emby.options_model import migrate_options_090
from custom_components.emby.options_sensors import remove_disabled_sensor_entities, sensor_unique_id
from custom_components.emby.player_actions import PlayerActionResult
from custom_components.emby.sensor_registry import async_prepare_sensor_registry_identities

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


@dataclass
class RegistryEntity:
    entity_id: str
    unique_id: str
    config_entry_id: str | None = "entry"
    platform: str = "emby"
    domain: str = "sensor"
    name: str | None = "Custom name"
    area_id: str | None = "living_room"
    labels: set[str] = field(default_factory=lambda: {"media"})
    aliases: set[str] = field(default_factory=lambda: {"viewer"})


class Registry:
    def __init__(self, entries=()):
        self.entities = {entry.entity_id: entry for entry in entries}

    def async_get_entity_id(self, domain, platform, unique_id):
        return next(
            (
                item.entity_id
                for item in self.entities.values()
                if (item.domain, item.platform, item.unique_id) == (domain, platform, unique_id)
            ),
            None,
        )

    def async_get(self, entity_id):
        return self.entities.get(entity_id)

    def async_get_or_create(
        self, *, domain, platform, unique_id, config_entry, suggested_object_id
    ):
        entity_id = f"{domain}.{suggested_object_id}"
        if entity_id in self.entities:
            suffix = 2
            while f"{entity_id}_{suffix}" in self.entities:
                suffix += 1
            entity_id = f"{entity_id}_{suffix}"
        entity = RegistryEntity(entity_id, unique_id, config_entry.entry_id, platform, domain)
        self.entities[entity_id] = entity
        return entity

    def async_update_entity(self, entity_id, *, new_entity_id):
        entity = self.entities.pop(entity_id)
        entity.entity_id = new_entity_id
        self.entities[new_entity_id] = entity

    def async_remove(self, entity_id):
        self.entities.pop(entity_id, None)


def _hass(registry):
    return SimpleNamespace(registry=registry)


def _entry():
    return SimpleNamespace(entry_id="entry")


def test_sensor_identity_migration_preserves_metadata_and_foreign_collision() -> None:
    unique_id = sensor_unique_id("entry", SENSOR_USERS_WATCHING)
    own = RegistryEntity("sensor.active_emby_users", unique_id)
    registry = Registry([own])
    result = async_prepare_sensor_registry_identities(
        _hass(registry), _entry(), [SENSOR_USERS_WATCHING]
    )
    assert result.migrated == 1 and result.collisions == 0
    assert registry.entities["sensor.emby_users_watching"] is own
    assert (own.name, own.area_id, own.labels, own.aliases) == (
        "Custom name",
        "living_room",
        {"media"},
        {"viewer"},
    )

    own.entity_id = "sensor.active_emby_users"
    foreign = RegistryEntity("sensor.emby_users_watching", "foreign", None, "template")
    registry = Registry([own, foreign])
    result = async_prepare_sensor_registry_identities(
        _hass(registry), _entry(), [SENSOR_USERS_WATCHING]
    )
    assert result.collisions == 1 and result.migrated == 0
    assert registry.entities[foreign.entity_id] is foreign


def test_new_install_remove_and_recreate_all_sensor_ids() -> None:
    registry = Registry()
    result = async_prepare_sensor_registry_identities(_hass(registry), _entry(), SENSOR_KEYS)
    assert result.prepared == 6
    assert set(registry.entities) == {f"sensor.{value}" for value in SENSOR_ENTITY_IDS.values()}
    assert remove_disabled_sensor_entities(_hass(registry), _entry(), frozenset()) == 6
    async_prepare_sensor_registry_identities(_hass(registry), _entry(), [SENSOR_USERS_WATCHING])
    assert set(registry.entities) == {"sensor.emby_users_watching"}


def test_duplicate_user_options_are_removed_idempotently() -> None:
    source = {
        CONF_OPTIONS_SCHEMA_VERSION: 2,
        CONF_USER_MASTER_VISIBILITY: {"Alex": True, "Sam": False},
        "Alex": False,
        "Sam": True,
    }
    migrated, changed = migrate_options_090(source, [])
    assert changed and migrated[CONF_OPTIONS_SCHEMA_VERSION] == OPTIONS_SCHEMA_VERSION == 3
    assert migrated[CONF_USER_MASTER_VISIBILITY] == {"Alex": True, "Sam": False}
    assert "Alex" not in migrated and "Sam" not in migrated
    repeated, changed_again = migrate_options_090(migrated, [])
    assert repeated == migrated and changed_again is False


def _player(name, activity):
    return SimpleNamespace(selector_label=name, last_activity=activity, player_key=name)


def test_player_labels_are_compact_and_oldest_first() -> None:
    newest = _player("TV · Emby", datetime(2026, 7, 19, 10, tzinfo=UTC))
    oldest = _player("Tablet · Emby", datetime(2026, 7, 18, 10, tzinfo=UTC))
    unknown = _player("Phone · Emby", None)
    players = _sort_group_players([newest, unknown, oldest])
    assert players == [oldest, newest, unknown]
    labels = [label for label, _ in _player_toggle_fields(players, german=True, time_zone="UTC")]
    assert labels[0] == "Tablet · Emby · zuletzt 18.07.2026 10:00"
    assert labels[-1] == "Phone · Emby · zuletzt unbekannt"
    assert all(
        "\n" not in label and "sensor." not in label and "media_player." not in label
        for label in labels
    )


class CleanupView(CleanupOptionsMixin):
    def __init__(self, report, german):
        self._runtime = SimpleNamespace(maintenance_state=SimpleNamespace(report=report))
        self._german = german
        self.hass = SimpleNamespace(config=SimpleNamespace(time_zone="UTC"))

    def _is_de(self):
        return self._german


def test_report_versions_and_legacy_ui_do_not_manufacture_zero() -> None:
    legacy = CleanupRunReport.from_dict({"status": "idle"})
    upgraded = CleanupRunReport.from_dict({"status": "idle", "skipped_recent": 4})
    assert legacy.report_version == 1
    assert upgraded.report_version == 2 and upgraded.skipped_recent == 4
    assert (
        CleanupView(legacy, True)._cleanup_report_placeholders()["recent"] == "Noch nicht erfasst"
    )
    assert CleanupView(legacy, False)._cleanup_report_placeholders()["recent"] == "Not recorded yet"
    assert (
        CleanupView(CleanupRunReport(skipped_recent=9), True)._cleanup_report_placeholders()[
            "recent"
        ]
        == "9"
    )


@pytest.mark.asyncio
async def test_reconciliation_v2_prevalidates_only_safe_or_restored(monkeypatch) -> None:
    players = [
        SimpleNamespace(
            player_key="inactive",
            entity_id="media_player.inactive",
            registry_present=True,
            visible_in_embi=False,
            playback="non_playing",
        ),
        SimpleNamespace(
            player_key="restored",
            entity_id="media_player.restored",
            registry_present=True,
            visible_in_embi=False,
            playback="unknown",
        ),
        SimpleNamespace(
            player_key="unclear",
            entity_id="media_player.unclear",
            registry_present=True,
            visible_in_embi=False,
            playback="unknown",
        ),
        SimpleNamespace(
            player_key="playing",
            entity_id="media_player.playing",
            registry_present=True,
            visible_in_embi=False,
            playback="playing",
        ),
        SimpleNamespace(
            player_key="paused",
            entity_id="media_player.paused",
            registry_present=True,
            visible_in_embi=False,
            playback="paused",
        ),
    ]
    monkeypatch.setattr(
        player_reconciliation_099, "_fresh_catalog", AsyncMock(return_value=players)
    )
    remove = AsyncMock(return_value=PlayerActionResult("remove", 5, (), (), ()))
    monkeypatch.setattr(player_reconciliation_099, "async_remove_hidden_player_entities", remove)
    states = {
        "media_player.restored": SimpleNamespace(attributes={"restored": True}),
        "media_player.unclear": SimpleNamespace(attributes={}),
    }
    hass = SimpleNamespace(states=SimpleNamespace(get=lambda entity_id: states.get(entity_id)))
    await player_reconciliation_099.async_reconcile_invisible_player_entities(hass, object())
    _, kwargs = remove.await_args
    assert kwargs["prevalidated_non_playing_keys"] == {"inactive", "restored"}
    assert REGISTRY_RECONCILIATION_VERSION == 2


def test_translations_and_manifest_define_complete_099_contract() -> None:
    strings = json.loads((COMPONENT / "strings.json").read_text())
    english = json.loads((COMPONENT / "translations/en.json").read_text())
    german = json.loads((COMPONENT / "translations/de.json").read_text())
    assert strings == english
    assert set(strings["options"]["error"]) == set(german["options"]["error"])
    assert set(strings["options"]["abort"]) == set(german["options"]["abort"])
    assert "" not in strings["options"]["error"].values()
    assert json.loads((COMPONENT / "manifest.json").read_text())["version"] == "0.9.9"
