from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

from custom_components.emby.const import (
    CONF_ENABLED_SENSORS,
    SENSOR_ENTITY_IDS,
    SENSOR_KEYS,
    SENSOR_USERS_WATCHING,
)
from custom_components.emby.options_sensors import (
    SensorsOptionsMixin,
    remove_disabled_sensor_entities,
    sensor_unique_id,
)
from custom_components.emby.sensor_registry import (
    async_prepare_sensor_registry_identities,
)


class SensorFlow(SensorsOptionsMixin):
    def __init__(self, german: bool) -> None:
        self._draft_options = {CONF_ENABLED_SENSORS: list(SENSOR_KEYS)}
        self.german = german

    def _is_de(self) -> bool:
        return self.german

    def async_show_form(self, **kwargs):
        return kwargs

    async def async_step_init(self):
        return {"type": "menu"}


@pytest.mark.asyncio
@pytest.mark.parametrize("german", [False, True])
async def test_sensor_page_renders_and_submits_only_to_draft(german: bool) -> None:
    flow = SensorFlow(german)
    rendered = await flow.async_step_sensors()
    assert rendered["step_id"] == "sensors"
    assert next(iter(rendered["data_schema"].schema)).schema == CONF_ENABLED_SENSORS
    assert flow._draft_options[CONF_ENABLED_SENSORS] == list(SENSOR_KEYS)

    result = await flow.async_step_sensors(
        {CONF_ENABLED_SENSORS: [SENSOR_KEYS[0], SENSOR_USERS_WATCHING]}
    )
    assert result == {"type": "menu"}
    assert flow._draft_options[CONF_ENABLED_SENSORS] == [
        SENSOR_KEYS[0],
        SENSOR_USERS_WATCHING,
    ]


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
        self.removed: list[str] = []

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
        self,
        *,
        domain,
        platform,
        unique_id,
        config_entry,
        suggested_object_id,
    ):
        entity_id = f"{domain}.{suggested_object_id}"
        entity = RegistryEntity(
            entity_id,
            unique_id,
            config_entry.entry_id,
            platform,
            domain,
        )
        self.entities[entity_id] = entity
        return entity

    def async_update_entity(self, entity_id, *, new_entity_id=None, **kwargs):
        entity = self.entities.pop(entity_id)
        entity.entity_id = new_entity_id or entity_id
        self.entities[entity.entity_id] = entity

    def async_remove(self, entity_id):
        self.removed.append(entity_id)
        self.entities.pop(entity_id, None)


def hass(registry):
    return SimpleNamespace(registry=registry)


def entry(options=None):
    return SimpleNamespace(entry_id="entry", options=options or {})


def test_sensor_identity_only_old_entity_is_migrated_in_place() -> None:
    unique_id = sensor_unique_id("entry", SENSOR_USERS_WATCHING)
    own = RegistryEntity("sensor.active_emby_users", unique_id)
    registry = Registry([own])
    result = async_prepare_sensor_registry_identities(
        hass(registry),
        entry(),
        [SENSOR_USERS_WATCHING],
    )
    assert result.migrated == 1
    assert registry.entities["sensor.emby_users_watching"] is own
    assert (own.name, own.area_id, own.labels, own.aliases) == (
        "Custom name",
        "living_room",
        {"media"},
        {"viewer"},
    )


def test_sensor_identity_only_new_entity_is_idempotent() -> None:
    unique_id = sensor_unique_id("entry", SENSOR_USERS_WATCHING)
    own = RegistryEntity("sensor.emby_users_watching", unique_id)
    registry = Registry([own])
    result = async_prepare_sensor_registry_identities(
        hass(registry),
        entry(),
        [SENSOR_USERS_WATCHING],
    )
    assert result.migrated == 0
    assert result.duplicates_removed == 0
    assert set(registry.entities) == {"sensor.emby_users_watching"}


def test_sensor_identity_both_owned_removes_only_legacy_duplicate() -> None:
    canonical = RegistryEntity(
        "sensor.emby_users_watching",
        sensor_unique_id("entry", SENSOR_USERS_WATCHING),
    )
    legacy = RegistryEntity(
        "sensor.active_emby_users",
        "entry_active_emby_users",
    )
    registry = Registry([canonical, legacy])
    result = async_prepare_sensor_registry_identities(
        hass(registry),
        entry(),
        [SENSOR_USERS_WATCHING],
    )
    assert result.duplicates_removed == 1
    assert set(registry.entities) == {"sensor.emby_users_watching"}


def test_sensor_identity_foreign_target_is_untouched() -> None:
    own = RegistryEntity(
        "sensor.active_emby_users",
        sensor_unique_id("entry", SENSOR_USERS_WATCHING),
    )
    foreign = RegistryEntity(
        "sensor.emby_users_watching",
        "foreign",
        None,
        "template",
    )
    registry = Registry([own, foreign])
    result = async_prepare_sensor_registry_identities(
        hass(registry),
        entry(),
        [SENSOR_USERS_WATCHING],
    )
    assert result.collisions == 1
    assert registry.entities[foreign.entity_id] is foreign
    assert registry.entities[own.entity_id] is own


def test_sensor_new_install_disable_and_restore_exact_ids() -> None:
    registry = Registry()
    result = async_prepare_sensor_registry_identities(hass(registry), entry(), SENSOR_KEYS)
    assert result.prepared == 6
    assert set(registry.entities) == {f"sensor.{value}" for value in SENSOR_ENTITY_IDS.values()}
    assert remove_disabled_sensor_entities(hass(registry), entry(), frozenset()) == 6
