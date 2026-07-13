from __future__ import annotations

import logging

from pyemby import EmbyServer
import voluptuous as vol

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA as MEDIA_PLAYER_PLATFORM_SCHEMA,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    DEVICE_DEFAULT_NAME,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util

from .const import (
    CLIENT_MODE_ALL,
    CONF_ALLOWED_DEVICE_IDS,
    CONF_CLIENT_MODE,
    CONF_IGNORED_DEVICE_IDS,
    DATA_PYEMBY,
    DEFAULT_PORT,
    DEFAULT_SSL,
    DEFAULT_SSL_PORT,
    DOMAIN,
)
from .helpers import should_expose_device

_LOGGER = logging.getLogger(__name__)
MEDIA_TYPE_TRAILER = "trailer"
SUPPORT_EMBY = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.SEEK
    | MediaPlayerEntityFeature.PLAY
)

PLATFORM_SCHEMA = MEDIA_PLAYER_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_HOST, default="localhost"): cv.string,
        vol.Optional(CONF_PORT): cv.port,
        vol.Optional(CONF_SSL, default=DEFAULT_SSL): cv.boolean,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Temporarily support legacy YAML for a controlled UI migration."""
    _LOGGER.warning(
        "EMBi is still running from legacy media_player YAML. Remove the Emby YAML "
        "platform after the UI config entry has been verified"
    )
    host = config[CONF_HOST]
    api_key = config[CONF_API_KEY]
    use_ssl = config[CONF_SSL]
    port = config.get(CONF_PORT)
    if port is None:
        port = DEFAULT_SSL_PORT if use_ssl else DEFAULT_PORT

    emby = EmbyServer(host, api_key, port, use_ssl, hass.loop)
    active_entities: dict[str, EmbyDevice] = {}
    inactive_entities: dict[str, EmbyDevice] = {}

    @callback
    def device_update_callback(data):
        new_entities: list[EmbyDevice] = []
        for dev_id, dev in emby.devices.items():
            if dev_id not in active_entities and dev_id not in inactive_entities:
                entity = EmbyDevice(emby, dev_id)
                active_entities[dev_id] = entity
                new_entities.append(entity)
            elif dev_id in inactive_entities and dev.state != "Off":
                entity = inactive_entities.pop(dev_id)
                active_entities[dev_id] = entity
                entity.set_available(True)
        if new_entities:
            async_add_entities(new_entities)

    @callback
    def device_removal_callback(data):
        if data in active_entities:
            entity = active_entities.pop(data)
            inactive_entities[data] = entity
            entity.set_available(False)

    async def stop_emby(event):
        await emby.stop()

    emby.add_new_devices_callback(device_update_callback)
    emby.add_stale_devices_callback(device_removal_callback)
    emby.start()
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_emby)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    emby = EmbyServer(
        entry.data[CONF_HOST],
        entry.data[CONF_API_KEY],
        entry.data[CONF_PORT],
        entry.data[CONF_SSL],
        hass.loop,
    )
    hass.data[DOMAIN][entry.entry_id][DATA_PYEMBY] = emby
    active_entities: dict[str, EmbyDevice] = {}
    inactive_entities: dict[str, EmbyDevice] = {}

    def allowed(dev_id: str) -> bool:
        dev = emby.devices[dev_id]
        return should_expose_device(
            device_id=dev_id,
            state=getattr(dev, "state", None),
            mode=entry.options.get(CONF_CLIENT_MODE, CLIENT_MODE_ALL),
            allowed_ids=entry.options.get(CONF_ALLOWED_DEVICE_IDS, []),
            ignored_ids=entry.options.get(CONF_IGNORED_DEVICE_IDS, []),
        )

    @callback
    def device_update_callback(data):
        new_entities: list[EmbyDevice] = []
        for dev_id in emby.devices:
            if not allowed(dev_id):
                if dev_id in active_entities:
                    entity = active_entities.pop(dev_id)
                    inactive_entities[dev_id] = entity
                    entity.set_available(False)
                continue
            if dev_id not in active_entities and dev_id not in inactive_entities:
                entity = EmbyDevice(emby, dev_id)
                active_entities[dev_id] = entity
                new_entities.append(entity)
            elif dev_id in inactive_entities:
                entity = inactive_entities.pop(dev_id)
                active_entities[dev_id] = entity
                entity.set_available(True)
        if new_entities:
            async_add_entities(new_entities)

    @callback
    def device_removal_callback(data):
        if data in active_entities:
            entity = active_entities.pop(data)
            inactive_entities[data] = entity
            entity.set_available(False)

    emby.add_new_devices_callback(device_update_callback)
    emby.add_stale_devices_callback(device_removal_callback)
    emby.start()


class EmbyDevice(MediaPlayerEntity):
    _attr_should_poll = False

    def __init__(self, emby, device_id: str) -> None:
        self.emby = emby
        self.device_id = device_id
        self.device = self.emby.devices[self.device_id]
        self.media_status_last_position = None
        self.media_status_received = None
        self._attr_unique_id = device_id

    async def async_added_to_hass(self) -> None:
        self.emby.add_update_callback(self.async_update_callback, self.device_id)

    @callback
    def async_update_callback(self, msg):
        if self.device.media_position:
            if self.device.media_position != self.media_status_last_position:
                self.media_status_last_position = self.device.media_position
                self.media_status_received = dt_util.utcnow()
        elif not self.device.is_nowplaying:
            self.media_status_last_position = None
            self.media_status_received = None
        self.async_write_ha_state()

    def set_available(self, value: bool) -> None:
        self._attr_available = value
        if self.hass is not None:
            self.async_write_ha_state()

    @property
    def supports_remote_control(self):
        return self.device.supports_remote_control

    @property
    def name(self):
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
    def app_name(self):
        return self.device.username

    @property
    def media_content_id(self):
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
    def media_duration(self):
        return self.device.media_runtime

    @property
    def media_position(self):
        return self.media_status_last_position

    @property
    def media_position_updated_at(self):
        return self.media_status_received

    @property
    def media_image_url(self):
        return self.device.media_image_url

    @property
    def media_title(self):
        return self.device.media_title

    @property
    def media_season(self):
        return self.device.media_season

    @property
    def media_series_title(self):
        return self.device.media_series_title

    @property
    def media_episode(self):
        return self.device.media_episode

    @property
    def media_album_name(self):
        return self.device.media_album_name

    @property
    def media_artist(self):
        return self.device.media_artist

    @property
    def media_album_artist(self):
        return self.device.media_album_artist

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        return SUPPORT_EMBY if self.supports_remote_control else MediaPlayerEntityFeature(0)

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
