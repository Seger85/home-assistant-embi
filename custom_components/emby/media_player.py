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
    DEVICE_DEFAULT_NAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .api import EmbyApiError
from .const import CONF_GLOBAL_PLAYER_MODE, PLAYER_MODE_PERSISTENT
from .models import EmbiRuntimeData
from .options_model import should_expose_player
from .player_context import CLIENT_CLASS_TECHNICAL, classify_client
from .player_identity import player_unique_id
from .player_reconciliation import async_reconcile_player_visibility
from .session_state import INACTIVE, player_activity
from .session_stream import EmbySessionStream

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
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EMBi media-player entities from a config entry."""
    runtime: EmbiRuntimeData = entry.runtime_data
    emby = runtime.session_client or EmbySessionStream(runtime.api_client, hass, entry)
    runtime.session_client = emby

    active_entities: dict[str, EmbyDevice] = {}
    inactive_entities: dict[str, EmbyDevice] = {}
    visibility_removals: set[str] = set()
    hidden_reconciled: set[str] = set()

    def allowed(device_id: str) -> bool:
        device = emby.devices[device_id]
        records = [record for record in runtime.devices if record.player_key == device_id]
        latest = max(
            records,
            key=lambda record: (
                record.last_activity_datetime.timestamp()
                if record.last_activity_datetime
                else float("-inf")
            ),
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

    async def _async_enforce_visibility(
        device_id: str,
        entity: EmbyDevice | None,
    ) -> None:
        """Remove one disallowed player even during a fresh platform reload."""
        removed_from_platform = False
        try:
            if entity is not None:
                device = emby.devices.get(device_id)
                state = str(getattr(device, "state", "")).casefold()
                if state in _ACTIVE_STATES:
                    return
                try:
                    sessions = await runtime.api_client.async_get_sessions()
                except EmbyApiError:
                    return
                if player_activity(sessions, device_id) != INACTIVE or not runtime.is_current(
                    entry
                ):
                    return
                if str(getattr(device, "state", "")).casefold() in _ACTIVE_STATES:
                    return
                if entity.hass is not None:
                    await entity.async_remove(force_remove=True)
                removed_from_platform = True
                active_entities.pop(device_id, None)
                inactive_entities.pop(device_id, None)

            result = await async_reconcile_player_visibility(
                hass,
                entry,
                requested_keys=(device_id,),
            )
            if result.status == "completed":
                hidden_reconciled.add(device_id)
        except Exception:
            _LOGGER.exception(
                "EMBi failed to enforce hidden player %s after a runtime update",
                device_id,
            )
        finally:
            if removed_from_platform:
                active_entities.pop(device_id, None)
                inactive_entities.pop(device_id, None)
            visibility_removals.discard(device_id)
            if runtime.is_current(entry) and allowed(device_id):
                device_update_callback(None)

    @callback
    def device_update_callback(data: Any) -> None:
        if not runtime.is_current(entry):
            return
        new_entities: list[EmbyDevice] = []
        for device_id in list(emby.devices):
            if not allowed(device_id):
                entity = active_entities.get(device_id) or inactive_entities.get(device_id)
                if device_id not in visibility_removals and device_id not in hidden_reconciled:
                    visibility_removals.add(device_id)
                    entry.async_create_background_task(
                        hass,
                        _async_enforce_visibility(device_id, entity),
                        "Enforce hidden EMBi player",
                    )
                continue

            hidden_reconciled.discard(device_id)
            if device_id in visibility_removals or not getattr(
                emby.devices[device_id], "is_active", True
            ):
                continue
            if device_id not in active_entities and device_id not in inactive_entities:
                entity = EmbyDevice(
                    emby,
                    device_id,
                    unique_id=player_unique_id(er.async_get(hass), entry.entry_id, device_id),
                )
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

    def __init__(self, emby: Any, device_id: str, *, unique_id: str | None = None) -> None:
        self.emby = emby
        self.device_id = device_id
        self.device = self.emby.devices[self.device_id]
        self.media_status_last_position: float | None = None
        self.media_status_received = None
        self._attr_unique_id = unique_id or device_id
        self._last_media_id: str | None = None
        self._last_playback_state: str | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        unsubscribe = self.emby.add_update_callback(self.async_update_callback, self.device_id)
        self.async_on_remove(unsubscribe)
        self.async_update_callback(None)

    @callback
    def async_update_callback(self, msg: Any) -> None:
        if self.device.is_nowplaying:
            # Zero is a valid seek/start position; a new item starts a new clock.
            if (
                self.device.media_position != self.media_status_last_position
                or self.device.media_id != self._last_media_id
                or self.device.state != self._last_playback_state
            ):
                self.media_status_last_position = self.device.media_position
                self.media_status_received = (
                    dt_util.utcnow() if self.device.media_position is not None else None
                )
        else:
            self.media_status_last_position = None
            self.media_status_received = None
        self._last_media_id = self.device.media_id
        self._last_playback_state = self.device.state
        self.async_write_ha_state()

    def set_available(self, value: bool) -> None:
        self._attr_available = value
        if self.hass is not None:
            self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return bool(self.device.is_active)

    async def _async_fetch_image(self, url: str) -> tuple[bytes | None, str | None]:
        # Home Assistant caches and proxies this image; the token stays in headers.
        return await self.device.api.async_get_image(url)

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

    async def _command(self, method: str, *args: Any) -> None:
        try:
            await getattr(self.device, method)(*args)
        except EmbyApiError as err:
            raise HomeAssistantError(
                translation_domain="emby", translation_key="command_failed"
            ) from err

    async def async_media_play(self) -> None:
        await self._command("media_play")

    async def async_media_pause(self) -> None:
        await self._command("media_pause")

    async def async_media_stop(self) -> None:
        await self._command("media_stop")

    async def async_media_next_track(self) -> None:
        await self._command("media_next")

    async def async_media_previous_track(self) -> None:
        await self._command("media_previous")

    async def async_media_seek(self, position: float) -> None:
        await self._command("media_seek", position)
