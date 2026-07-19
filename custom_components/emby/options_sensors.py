from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    CONF_ENABLED_SENSORS,
    DOMAIN,
    SENSOR_ALBUM_COUNT,
    SENSOR_KEYS,
    SENSOR_MOVIE_COUNT,
    SENSOR_SONG_COUNT,
    SENSOR_TV_EPISODE_COUNT,
    SENSOR_TV_SERIES_COUNT,
    SENSOR_USERS_WATCHING,
)

_SENSOR_LABELS = {
    SENSOR_MOVIE_COUNT: ("Filme", "Movies"),
    SENSOR_TV_SERIES_COUNT: ("Serien", "TV series"),
    SENSOR_TV_EPISODE_COUNT: ("Episoden", "TV episodes"),
    SENSOR_ALBUM_COUNT: ("Alben", "Albums"),
    SENSOR_SONG_COUNT: ("Songs", "Songs"),
    SENSOR_USERS_WATCHING: ("Aktuell schauende Benutzer", "Users currently watching"),
}


class SensorsOptionsMixin:
    """Configure EMBi sensors with one stable serializable selector."""

    async def async_step_sensors(self, user_input: dict[str, Any] | None = None):
        enabled = {
            str(value) for value in self._draft_options.get(CONF_ENABLED_SENSORS, list(SENSOR_KEYS))
        }
        if user_input is not None:
            selected = {str(value) for value in user_input.get(CONF_ENABLED_SENSORS, [])}
            self._draft_options[CONF_ENABLED_SENSORS] = [
                key for key in SENSOR_KEYS if key in selected
            ]
            return await self.async_step_init()

        german = self._is_de()
        options = [
            {"value": key, "label": _SENSOR_LABELS[key][0 if german else 1]} for key in SENSOR_KEYS
        ]
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ENABLED_SENSORS,
                    default=[key for key in SENSOR_KEYS if key in enabled],
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
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
