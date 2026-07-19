from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
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
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util
from pyemby import EmbyServer

from .const import CONF_GLOBAL_PLAYER_MODE, PLAYER_MODE_PERSISTENT
from .models import EmbiRuntimeData
from .options_model import should_expose_player
from .player_context import CLIENT_CLASS_TECHNICAL, classify_client
from .player_reconciliation import async_reconcile_player_visibility

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
_ACTIVE_STATES = {"playing", "paused"}


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
    visibility_removals: set[str] = set()

    def allowed(device_id: str) -> bool:
        device = emby.devices[device_id]
        records = [record for record in runtime.devices if record.player_key == device_id]
        latest = max(
            records,
            key=lambda record: record.last_activity_datetime is not None,
            default=None,
        )
        client_class, _ = classify_client(
            records,
            runtime_state=str(getattr(device, "state", "")).casefold() or None,
        )
        users = {
            user
            for record in records
            for user in (*record.user_names, record.last_user_name)
            if user
        }
        return should_expose_player(
            player_key=device_id,
            reported_device_id=latest.reported_device_id if latest else None,
            state=getattr(device, "state", None),
            options={
                CONF_GLOBAL_PLAYER_MODE: entry.options.get(
                    CONF_GLOBAL_PLAYER_MODE,
                    PLAYER_MODE_PERSISTENT,
                ),
                **dict(entry.options),
            },
            technical_access=client_class == CLIENT_CLASS_TECHNICAL,
            users=users,
        )

    async def _unknown_has_active_session(device_id: str) -> bool | None:
        try:
            sessions = await runtime.api_client._request("GET", "/Sessions")
        except Exception:
            return None
        if not isinstance(sessions, list):
            return None
        for session in sessions:
            if not isinstance(session, dict):
                return None
            reported = str(session.get("DeviceId") or "")
            if reported and reported.casefold() not in device_id.casefold():
                continue
            if not isinstance(session.get("NowPlayingItem"), dict):
                continue
            play_state = session.get("PlayState")
            if not isinstance(play_state, dict) or not isinstance(
                play_state.get("IsPaused"), bool
            ):
                return None
            return True
        return False

    async def _async_reconcile_for_visibility(device_id: str) -> None:
        """Reconcile an exact disallowed key even without a local entity object."""
        try:
            await async_reconcile_player_visibility(
                hass,
                entry,
                requested_keys=(device_id,),
            )
        except Exception:
            _LOGGER.exception(
                "EMBi failed to reconcile hidden player %s after a runtime update",
                device_id,
            )
        finally:
            visibility_removals.discard(device_id)

    async def _async_remove_for_visibility(device_id: str, entity: EmbyDevice) -> None:
        """Remove one disallowed entity only after current playback validation."""
        removed = False
        try:
            device = emby.devices.get(device_id)
            state = str(getattr(device, "state", "")).casefold()
            if state in _ACTIVE_STATES:
                return
            if state not in {"idle", "off", "standby", "unavailable"}:
                active_session = await _unknown_has_active_session(device_id)
                if active_session is not False:
                    return
            if entity.hass is not None:
                await entity.async_remove(force_remove=True)
            removed = True
            await async_reconcile_player_visibility(
                hass,
                entry,
                requested_keys=(device_id,),
            )
        except Exception:
            _LOGGER.exception(
                "EMBi failed to remove hidden player %s after a runtime update",
                device_id,
            )
        finally:
            if removed:
                active_entities.pop(device_id, None)
                inactive_entities.pop(device_id, None)
            visibility_removals.discard(device_id)

    @callback
    def device_update_callback(data: Any) -> None:
        new_entities: list[EmbyDevice] = []
        for device_id in list(emby.devices):
            if not allowed(device_id):
                if device_id not in visibility_removals:
                    visibility_removals.add(device_id)
                    entity = active_entities.get(device_id) or inactive_entities.get(
                        device_id
                    )
                    task = (
                        _async_remove_for_visibility(device_id, entity)
                        if entity is not None
                        else _async_reconcile_for_visibility(device_id)
                    )
                    hass.async_create_task(task, "Reconcile hidden EMBi player")
                continue

            if device_id in visibility_removals:
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
        await super().async_added_to_hass()
        self.emby.add_update_callback(self.async_update_callback, self.device_id)

    @callback
    def async_update_callback(self, msg: Any) -> None:
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
