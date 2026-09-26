from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import EmbyApiError, EmbyAuthError
from .const import (
    CONF_ENABLED_SENSORS,
    DOMAIN,
    SENSOR_ACTIVE_PLAYERS,
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
from .sensor_registry import async_prepare_sensor_registry_identities
from .session_stream import EmbySessionStream

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class EmbiSensorEntityDescription(SensorEntityDescription):
    """Description for one EMBi statistic sensor."""

    object_id: str


SENSOR_DESCRIPTIONS: tuple[EmbiSensorEntityDescription, ...] = (
    EmbiSensorEntityDescription(
        key=SENSOR_ACTIVE_PLAYERS,
        object_id="emby_active_players",
        name="Emby Active Players",
        icon="mdi:cast-connected",
    ),
    EmbiSensorEntityDescription(
        key=SENSOR_MOVIE_COUNT,
        object_id="emby_movie_count",
        name="Emby Movie Count",
        icon="mdi:movie-open",
    ),
    EmbiSensorEntityDescription(
        key=SENSOR_TV_SERIES_COUNT,
        object_id="emby_tv_series_count",
        name="Emby TV Series Count",
        icon="mdi:television-classic",
    ),
    EmbiSensorEntityDescription(
        key=SENSOR_TV_EPISODE_COUNT,
        object_id="emby_tv_episode_count",
        name="Emby TV Episode Count",
        icon="mdi:television-play",
    ),
    EmbiSensorEntityDescription(
        key=SENSOR_ALBUM_COUNT,
        object_id="emby_album_count",
        name="Emby Album Count",
        icon="mdi:album",
    ),
    EmbiSensorEntityDescription(
        key=SENSOR_SONG_COUNT,
        object_id="emby_song_count",
        name="Emby Song Count",
        icon="mdi:music-note",
    ),
    EmbiSensorEntityDescription(
        key=SENSOR_USERS_WATCHING,
        object_id="emby_users_watching",
        name="Active Emby Users",
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

    async_prepare_sensor_registry_identities(
        hass,
        entry,
        (description.key for description in descriptions),
    )

    async def library_data() -> dict[str, int]:
        try:
            return await runtime.api_client.async_get_library_counts(enabled)
        except EmbyAuthError as err:
            raise ConfigEntryAuthFailed from err
        except EmbyApiError as err:
            raise UpdateFailed("Unable to update Emby library counts") from err

    async def watching_data() -> dict[str, int]:
        try:
            return await runtime.api_client.async_get_watching_users()
        except EmbyAuthError as err:
            raise ConfigEntryAuthFailed from err
        except EmbyApiError as err:
            raise UpdateFailed("Unable to update Emby viewers") from err

    # Independent endpoints have independent availability and retry behavior.
    groups = (
        (
            "library",
            [
                item
                for item in descriptions
                if item.key not in {SENSOR_USERS_WATCHING, SENSOR_ACTIVE_PLAYERS}
            ],
            library_data,
        ),
        (
            "viewers",
            [item for item in descriptions if item.key == SENSOR_USERS_WATCHING],
            watching_data,
        ),
    )
    entities: list[SensorEntity] = [
        EmbiActivePlayersSensor(runtime.session_client, entry, description)
        for description in descriptions
        if description.key == SENSOR_ACTIVE_PLAYERS
    ]
    for name, selected, update in groups:
        if not selected:
            continue
        coordinator: DataUpdateCoordinator[dict[str, int]] = DataUpdateCoordinator(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{name}_{entry.entry_id}",
            update_method=update,
            update_interval=timedelta(seconds=SENSOR_UPDATE_INTERVAL_SECONDS),
            always_update=False,
        )
        runtime.sensor_coordinators[name] = coordinator
        await coordinator.async_refresh()
        entities.extend(EmbiSensor(coordinator, entry, description) for description in selected)
    async_add_entities(entities)


class EmbiActivePlayersSensor(SensorEntity):
    """Expose the existing session stream without additional network polling."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        stream: EmbySessionStream,
        entry: ConfigEntry,
        description: EmbiSensorEntityDescription,
    ) -> None:
        self._stream = stream
        self._last_value: int | None = stream.active_player_count
        self.entity_description = description
        self._attr_unique_id = sensor_unique_id(entry.entry_id, description.key)
        self._attr_translation_key = description.key
        self._attr_suggested_object_id = description.object_id

    @property
    def available(self) -> bool:
        return self._stream.active_player_count is not None

    @property
    def native_value(self) -> int | None:
        return self._stream.active_player_count

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self._stream.add_snapshot_callback(self._snapshot_changed))

    @callback
    def _snapshot_changed(self, _event: object) -> None:
        value = self._stream.active_player_count
        if value != self._last_value:
            self._last_value = value
            self.async_write_ha_state()


class EmbiSensor(CoordinatorEntity[DataUpdateCoordinator[dict[str, int]]], SensorEntity):
    """A numeric statistic supplied by the local Emby server."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, int]],
        entry: ConfigEntry,
        description: EmbiSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = sensor_unique_id(entry.entry_id, description.key)
        self._attr_translation_key = description.key
        self._attr_suggested_object_id = description.object_id

    @property
    def native_value(self) -> int | None:
        """Return the last successfully fetched value."""
        data = self.coordinator.data
        return data.get(self.entity_description.key) if data is not None else None
