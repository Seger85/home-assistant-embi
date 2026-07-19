from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import CONF_ENABLED_SENSORS, DOMAIN, SENSOR_KEYS


class SensorsOptionsMixin:
    """Configure the optional EMBi sensor platform in the shared draft."""

    async def async_step_sensors(self, user_input: dict[str, Any] | None = None):
        enabled = {
            str(value) for value in self._draft_options.get(CONF_ENABLED_SENSORS, list(SENSOR_KEYS))
        }

        if user_input is not None:
            self._draft_options[CONF_ENABLED_SENSORS] = [
                key for key in SENSOR_KEYS if bool(user_input.get(key, False))
            ]
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(key, default=key in enabled): selector.BooleanSelector()
                for key in SENSOR_KEYS
            }
        )
        return self.async_show_form(
            step_id="sensors",
            data_schema=schema,
            description_placeholders={
                "enabled": str(len(enabled)),
                "total": str(len(SENSOR_KEYS)),
            },
        )


def sensor_unique_id(entry_id: str, key: str) -> str:
    """Return the stable registry identity for one config entry and sensor."""
    return f"{entry_id}_{key}"


def remove_disabled_sensor_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    enabled_sensor_keys: set[str] | frozenset[str],
) -> int:
    """Delete only disabled sensor entities owned by this EMBi config entry."""
    registry = er.async_get(hass)
    enabled = {str(value) for value in enabled_sensor_keys}
    known_unique_ids = {sensor_unique_id(entry.entry_id, key): key for key in SENSOR_KEYS}
    removed = 0
    for entity in list(registry.entities.values()):
        key = known_unique_ids.get(str(entity.unique_id))
        if (
            entity.domain != "sensor"
            or entity.platform != DOMAIN
            or entity.config_entry_id != entry.entry_id
            or key is None
            or key in enabled
        ):
            continue
        registry.async_remove(entity.entity_id)
        removed += 1
    return removed
