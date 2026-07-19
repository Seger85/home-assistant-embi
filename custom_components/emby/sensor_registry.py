from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, SENSOR_ENTITY_IDS
from .options_sensors import sensor_unique_id

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SensorRegistryIdentityResult:
    """Aggregate result without exposing private server data."""

    prepared: int = 0
    migrated: int = 0
    collisions: int = 0


def async_prepare_sensor_registry_identities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    sensor_keys: Iterable[str],
) -> SensorRegistryIdentityResult:
    """Create or migrate exact EMBi-owned sensor registry identities.

    Existing metadata and history are preserved because an existing registry
    entry is renamed in place. A foreign entity occupying the documented target
    is never adopted, renamed or deleted.
    """
    registry = er.async_get(hass)
    prepared = migrated = collisions = 0

    for key in sensor_keys:
        object_id = SENSOR_ENTITY_IDS[key]
        expected_entity_id = f"sensor.{object_id}"
        unique_id = sensor_unique_id(entry.entry_id, key)

        entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        if entity_id is None:
            entity = registry.async_get_or_create(
                domain="sensor",
                platform=DOMAIN,
                unique_id=unique_id,
                config_entry=entry,
                suggested_object_id=object_id,
            )
            entity_id = entity.entity_id
            prepared += 1

        if entity_id == expected_entity_id:
            continue

        occupied = registry.async_get(expected_entity_id)
        if occupied is not None:
            collisions += 1
            _LOGGER.error(
                "EMBi sensor identity collision for %s; keeping %s and leaving "
                "the unrelated target untouched",
                key,
                entity_id,
            )
            continue

        registry.async_update_entity(entity_id, new_entity_id=expected_entity_id)
        migrated += 1

    return SensorRegistryIdentityResult(
        prepared=prepared,
        migrated=migrated,
        collisions=collisions,
    )
