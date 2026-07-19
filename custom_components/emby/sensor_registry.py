from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_SENSOR_IDENTITY_VERSION,
    DOMAIN,
    SENSOR_ENTITY_IDS,
    SENSOR_IDENTITY_VERSION,
    SENSOR_USERS_WATCHING,
)
from .options_sensors import sensor_unique_id

_LOGGER = logging.getLogger(__name__)
_LEGACY_USERS_WATCHING_ENTITY_ID = "sensor.active_emby_users"


@dataclass(frozen=True, slots=True)
class SensorRegistryIdentityResult:
    """Aggregate result without exposing private server data."""

    prepared: int = 0
    migrated: int = 0
    duplicates_removed: int = 0
    collisions: int = 0
    already_current: bool = False


def _owned(entity: object | None, entry: ConfigEntry) -> bool:
    return bool(
        entity is not None
        and getattr(entity, "domain", None) == "sensor"
        and getattr(entity, "platform", None) == DOMAIN
        and getattr(entity, "config_entry_id", None) == entry.entry_id
    )


def _legacy_users_watching_owned(entity: object | None, entry: ConfigEntry) -> bool:
    if not _owned(entity, entry):
        return False
    unique_id = str(getattr(entity, "unique_id", ""))
    return unique_id in {
        sensor_unique_id(entry.entry_id, SENSOR_USERS_WATCHING),
        f"{entry.entry_id}_active_emby_users",
        f"{entry.entry_id}_active_users",
    }


def async_prepare_sensor_registry_identities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    sensor_keys: Iterable[str],
) -> SensorRegistryIdentityResult:
    """Prepare canonical sensor IDs and remove only an exact EMBi duplicate rest."""
    if int(entry.options.get(CONF_SENSOR_IDENTITY_VERSION, 0) or 0) >= SENSOR_IDENTITY_VERSION:
        return SensorRegistryIdentityResult(already_current=True)

    registry = er.async_get(hass)
    prepared = migrated = duplicates_removed = collisions = 0

    for key in sensor_keys:
        object_id = SENSOR_ENTITY_IDS[key]
        expected_entity_id = f"sensor.{object_id}"
        unique_id = sensor_unique_id(entry.entry_id, key)
        mapped_entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        target = registry.async_get(expected_entity_id)

        if mapped_entity_id is None and target is None:
            entity = registry.async_get_or_create(
                domain="sensor",
                platform=DOMAIN,
                unique_id=unique_id,
                config_entry=entry,
                suggested_object_id=object_id,
            )
            mapped_entity_id = entity.entity_id
            target = entity
            prepared += 1

        if mapped_entity_id == expected_entity_id and _owned(target, entry):
            if key == SENSOR_USERS_WATCHING:
                legacy = registry.async_get(_LEGACY_USERS_WATCHING_ENTITY_ID)
                if (
                    legacy is not None
                    and legacy.entity_id != expected_entity_id
                    and _legacy_users_watching_owned(legacy, entry)
                ):
                    registry.async_remove(legacy.entity_id)
                    duplicates_removed += 1
            continue

        mapped = registry.async_get(mapped_entity_id) if mapped_entity_id else None
        if target is not None:
            if _owned(target, entry) and str(getattr(target, "unique_id", "")) == unique_id:
                if (
                    key == SENSOR_USERS_WATCHING
                    and mapped is not None
                    and mapped.entity_id != target.entity_id
                    and _legacy_users_watching_owned(mapped, entry)
                ):
                    registry.async_remove(mapped.entity_id)
                    duplicates_removed += 1
                continue
            collisions += 1
            _LOGGER.warning(
                "EMBi sensor identity target is occupied; the unrelated entity remains untouched"
            )
            continue

        if mapped is not None and _owned(mapped, entry) and str(mapped.unique_id) == unique_id:
            registry.async_update_entity(mapped.entity_id, new_entity_id=expected_entity_id)
            migrated += 1
            continue

        collisions += 1

    return SensorRegistryIdentityResult(
        prepared=prepared,
        migrated=migrated,
        duplicates_removed=duplicates_removed,
        collisions=collisions,
    )
