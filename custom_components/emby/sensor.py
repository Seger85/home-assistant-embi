from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_ENABLED_SENSORS,
    DOMAIN,
    SENSOR_ALBUM_COUNT,
    SENSOR_KEYS,
    SENSOR_MOVIE_COUNT,
    SENSOR_SONG_COUNT,
    SENSOR_TV_EPISODE_COUNT,
    SENSOR_TV_SERIES_COUNT,
    SENSOR_UPDATE_INTERVAL_SECONDS,
    SENSOR_USERS_WATCHING,
)
from .models import EmbiRuntimeData
from .options_sensors import sensor_unique_id

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class EmbiSensorEntityDescription(SensorEntityDescription):
    """Description for one EMBi statistic sensor."""

    object_id: str


SENSOR_DESCRIPTIONS: tuple[EmbiSensorEntityDescription, ...] = (
    EmbiSensorEntityDescription(
        key=SENSOR_MOVIE_COUNT,
        name="Emby Movie Count",
        object_id="emby_movie_count",
        icon="mdi:movie-open",
    ),
    EmbiSensorEntityDescription(
        key=SENSOR_TV_SERIES_COUNT,
        name="Emby TV Series Count",
        object_id="emby_tv_series_count",
        icon="mdi:television-classic",
    ),
    EmbiSensorEntityDescription(
        key=SENSOR_TV_EPISODE_COUNT,
        name="Emby TV Episode Count",
        object_id="emby_tv_episode_count",
        icon="mdi:television-play",
    ),
    EmbiSensorEntityDescription(
        key=SENSOR_ALBUM_COUNT,
        name="Emby Album Count",
        object_id="emby_album_count",
        icon="mdi:album",
    ),
    EmbiSensorEntityDescription(
        key=SENSOR_SONG_COUNT,
        name="Emby Song Count",
        object_id="emby_song_count",
        icon="mdi:music-note",
    ),
    EmbiSensorEntityDescription(
        key=SENSOR_USERS_WATCHING,
        name="Active Emby Users",
        object_id="emby_users_watching",
        icon="mdi:account-eye",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up enabled EMBi statistics sensors."""
    runtime: EmbiRuntimeData = entry.runtime_data
    enabled = {str(value) for value in entry.options.get(CONF_ENABLED_SENSORS, list(SENSOR_KEYS))}
    descriptions = [
        description for description in SENSOR_DESCRIPTIONS if description.key in enabled
    ]
    if not descriptions:
        return

    async def _async_update_data() -> dict[str, int]:
        try:
            return await runtime.api_client.async_get_sensor_data()
        except Exception as err:
            raise UpdateFailed("Unable to update EMBi sensors") from err

    coordinator: DataUpdateCoordinator[dict[str, int]] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_sensors_{entry.entry_id}",
        update_method=_async_update_data,
        update_interval=timedelta(seconds=SENSOR_UPDATE_INTERVAL_SECONDS),
    )
    await coordinator.async_refresh()
    async_add_entities(EmbiSensor(coordinator, entry, description) for description in descriptions)


class EmbiSensor(CoordinatorEntity[DataUpdateCoordinator[dict[str, int]]], SensorEntity):
    """A numeric statistic supplied by the local Emby server."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, int]],
        entry: ConfigEntry,
        description: EmbiSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = sensor_unique_id(entry.entry_id, description.key)
        self._attr_name = description.name
        self._attr_suggested_object_id = description.object_id

    @property
    def native_value(self) -> int | None:
        """Return the last successfully fetched value."""
        data = self.coordinator.data
        return data.get(self.entity_description.key) if data is not None else None
