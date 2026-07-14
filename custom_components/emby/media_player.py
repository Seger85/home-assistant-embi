from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_SSL, DEVICE_DEFAULT_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util
from pyemby import EmbyServer

from .const import (
    CLIENT_MODE_ALL,
    CONF_ALLOWED_DEVICE_IDS,
    CONF_CLIENT_MODE,
    CONF_IGNORED_PLAYER_KEYS,
    CONF_IGNORED_REPORTED_DEVICE_IDS,
)
from .helpers import reported_device_id_for_player_key, should_expose_device
from .models import EmbiRuntimeData

MEDIA_TYPE_TRAILER = "trailer"
SUPPORT_EMBY = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.SEEK
    | MediaPlayerEntityFeature.PLAY
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EMBi media-player entities from a config entry."""
    emby = EmbyServer(
        entry.data[CONF_HOST],
        entry.data[CONF_API_KEY],
        entry.data[CONF_PORT],
        entry.data[CONF_SSL],
        hass.loop,
    )
    runtime: EmbiRuntimeData = entry.runtime_data
    runtime.pyemby = emby

    active_entities: dict[str, EmbyDevice] = {}
    inactive_entities: dict[str, EmbyDevice] = {}

    def allowed(device_id: str) -> bool:
        device = emby.devices[device_id]
        return should_expose_device(
            device_id=device_id,
            reported_device_id=reported_device_id_for_player_key(runtime.devices, device_id),
            state=getattr(device, "state", None),
            mode=entry.options.get(CONF_CLIENT_MODE, CLIENT_MODE_ALL),
            allowed_ids=entry.options.get(CONF_ALLOWED_DEVICE_IDS, []),
            ignored_player_keys=entry.options.get(CONF_IGNORED_PLAYER_KEYS, []),
            ignored_reported_device_ids=entry.options.get(CONF_IGNORED_REPORTED_DEVICE_IDS, []),
        )

    @callback
    def device_update_callback(data: Any) -> None:
        new_entities: list[EmbyDevice] = []
        for device_id in list(emby.devices):
            if not allowed(device_id):
                if device_id in active_entities:
                    entity = active_entities.pop(device_id)
                    inactive_entities[device_id] = entity
                    entity.set_available(False)
                continue

            if device_id not in active_entities and device_id not in inactive_entities:
                entity = EmbyDevice(emby, device_id)
                active_entities[device_id] = entity
                new_entities.append(entity)
            elif device_id in inactive_entities:
                entity = inactive_entities.pop(device_id)
                active_entities[device_id] = entity
                entity.set_available(True)

        if new_entities:
            async_add_entities(new_entities)

    @callback
    def device_removal_callback(device_id: str) -> None:
        if device_id in active_entities:
            entity = active_entities.pop(device_id)
            inactive_entities[device_id] = entity
            entity.set_available(False)

    emby.add_new_devices_callback(device_update_callback)
    emby.add_stale_devices_callback(device_removal_callback)
    emby.start()


class EmbyDevice(MediaPlayerEntity):
    """Representation of one Emby client."""

    _attr_should_poll = False

    def __init__(self, emby: Any, device_id: str) -> None:
        self.emby = emby
        self.device_id = device_id
        self.device = self.emby.devices[self.device_id]
        self.media_status_last_position: float | None = None
        self.media_status_received = None
        self._attr_unique_id = device_id

    async def async_added_to_hass(self) -> None:
        """Register the pyemby update callback."""
        await super().async_added_to_hass()
        self.emby.add_update_callback(self.async_update_callback, self.device_id)

    @callback
    def async_update_callback(self, msg: Any) -> None:
        """Write the latest pyemby state to Home Assistant."""
        if self.device.media_position:
            if self.device.media_position != self.media_status_last_position:
                self.media_status_last_position = self.device.media_position
                self.media_status_received = dt_util.utcnow()
        elif not self.device.is_nowplaying:
            self.media_status_last_position = None
            self.media_status_received = None
        self.async_write_ha_state()

    def set_available(self, value: bool) -> None:
        """Set entity availability and publish the state."""
        self._attr_available = value
        if self.hass is not None:
            self.async_write_ha_state()

    @property
    def supports_remote_control(self) -> bool:
        return bool(self.device.supports_remote_control)

    @property
    def name(self) -> str:
        device_name = getattr(self.device, "name", None)
        return f"Emby {device_name}" if device_name else DEVICE_DEFAULT_NAME

    @property
    def state(self) -> MediaPlayerState | None:
        mapping = {
            "Paused": MediaPlayerState.PAUSED,
            "Playing": MediaPlayerState.PLAYING,
            "Idle": MediaPlayerState.IDLE,
            "Off": MediaPlayerState.OFF,
        }
        return mapping.get(self.device.state)

    @property
    def app_name(self) -> str | None:
        return self.device.username

    @property
    def media_content_id(self) -> str | None:
        return self.device.media_id

    @property
    def media_content_type(self) -> MediaType | str | None:
        mapping = {
            "Episode": MediaType.TVSHOW,
            "Movie": MediaType.MOVIE,
            "Trailer": MEDIA_TYPE_TRAILER,
            "Music": MediaType.MUSIC,
            "Video": MediaType.VIDEO,
            "Audio": MediaType.MUSIC,
            "TvChannel": MediaType.CHANNEL,
        }
        return mapping.get(self.device.media_type)

    @property
    def media_duration(self) -> float | None:
        return self.device.media_runtime

    @property
    def media_position(self) -> float | None:
        return self.media_status_last_position

    @property
    def media_position_updated_at(self):
        return self.media_status_received

    @property
    def media_image_url(self) -> str | None:
        return self.device.media_image_url

    @property
    def media_title(self) -> str | None:
        return self.device.media_title

    @property
    def media_season(self) -> str | None:
        return self.device.media_season

    @property
    def media_series_title(self) -> str | None:
        return self.device.media_series_title

    @property
    def media_episode(self) -> str | None:
        return self.device.media_episode

    @property
    def media_album_name(self) -> str | None:
        return self.device.media_album_name

    @property
    def media_artist(self) -> str | None:
        return self.device.media_artist

    @property
    def media_album_artist(self) -> str | None:
        return self.device.media_album_artist

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        if self.supports_remote_control:
            return SUPPORT_EMBY
        return MediaPlayerEntityFeature(0)

    async def async_media_play(self) -> None:
        await self.device.media_play()

    async def async_media_pause(self) -> None:
        await self.device.media_pause()

    async def async_media_stop(self) -> None:
        await self.device.media_stop()

    async def async_media_next_track(self) -> None:
        await self.device.media_next()

    async def async_media_previous_track(self) -> None:
        await self.device.media_previous()

    async def async_media_seek(self, position: float) -> None:
        await self.device.media_seek(position)
