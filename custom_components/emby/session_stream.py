"""Emby session stream using Home Assistant's shared HTTP session and task lifecycle."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote, urlencode

from aiohttp import ClientError, WSMsgType

from .api import EmbyApiClient, EmbyApiError, EmbyAuthError
from .session_state import (
    ACTIVE,
    aggregate_activity,
    session_activity,
    session_key,
    validate_sessions,
)

_LOGGER = logging.getLogger(__name__)
RECONNECT_SECONDS = 15
REFRESH_SECONDS = 30


def _notify(listeners: Any, value: Any) -> None:
    """One failed entity callback must not stop other entities or reconnection."""
    for callback in tuple(listeners):
        try:
            callback(value)
        except Exception:
            _LOGGER.exception("EMBi session listener failed")


def _seconds(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return max(0, int(value)) / 10_000_000
    except (ValueError, TypeError, OverflowError):
        return None


class SessionDevice:
    """Stable client identity with deterministic selection among concurrent sessions."""

    def __init__(self, api: EmbyApiClient) -> None:
        self.api = api
        self.session: dict[str, Any] = {}
        self.activity = "unknown"
        self.is_active = False

    def update(self, sessions: list[dict[str, Any]]) -> None:
        self.activity = aggregate_activity(session_activity(item) for item in sessions)
        # Prefer a playing session, then paused, then idle; active sessions never
        # lose to a later idle session in the server's response ordering.
        rank = {"playing": 0, "paused": 1, "unknown": 2, "non_playing": 3}
        self.session = min(
            sessions,
            key=lambda item: (
                rank[session_activity(item)],
                not bool(item.get("SupportsRemoteControl")),
                str(item.get("Id", "")),
            ),
        )
        self.is_active = True

    @property
    def state(self) -> str:
        if not self.is_active:
            return "Unavailable"
        return {"playing": "Playing", "paused": "Paused", "non_playing": "Idle"}.get(
            self.activity, "Unknown"
        )

    @property
    def is_nowplaying(self) -> bool:
        return self.is_active and self.activity in ACTIVE

    @property
    def item(self) -> dict[str, Any]:
        value = self.session.get("NowPlayingItem")
        return value if isinstance(value, dict) else {}

    @property
    def play_state(self) -> dict[str, Any]:
        value = self.session.get("PlayState")
        return value if isinstance(value, dict) else {}

    @property
    def name(self) -> str | None:
        return self.session.get("DeviceName")

    @property
    def username(self) -> str | None:
        return self.session.get("UserName")

    @property
    def supports_remote_control(self) -> bool:
        return (
            self.is_active
            and self.session.get("SupportsRemoteControl") is True
            and bool(self.session.get("Id"))
        )

    @property
    def media_id(self) -> str | None:
        return self.item.get("Id")

    @property
    def media_type(self) -> str | None:
        return self.item.get("Type")

    @property
    def media_title(self) -> str | None:
        return self.item.get("Name")

    @property
    def media_runtime(self) -> float | None:
        return _seconds(self.item.get("RunTimeTicks"))

    @property
    def media_position(self) -> float | None:
        position = _seconds(self.play_state.get("PositionTicks"))
        duration = self.media_runtime
        return (
            min(position, duration) if position is not None and duration is not None else position
        )

    @property
    def media_season(self) -> int | None:
        return self.item.get("ParentIndexNumber")

    @property
    def media_episode(self) -> int | None:
        return self.item.get("IndexNumber")

    @property
    def media_series_title(self) -> str | None:
        return self.item.get("SeriesName")

    @property
    def media_album_name(self) -> str | None:
        return self.item.get("Album")

    @property
    def media_artist(self) -> str | None:
        artists = self.item.get("Artists")
        return (
            ", ".join(item for item in artists if isinstance(item, str))
            if isinstance(artists, list)
            else None
        )

    @property
    def media_album_artist(self) -> str | None:
        return self.item.get("AlbumArtist")

    @property
    def media_image_url(self) -> str | None:
        if not self.is_nowplaying or not self.media_id:
            return None
        tags = self.item.get("ImageTags")
        tags = tags if isinstance(tags, dict) else {}
        for kind in ("Thumb", "Primary"):
            tag = tags.get(kind)
            item_id: Any = self.media_id
            if not tag:
                tag = self.item.get(f"{kind}ImageTag")
                item_id = self.item.get(f"{kind}ItemId") or self.item.get(f"{kind}ImageItemId")
            if tag and item_id:
                query = urlencode({"width": 500, "tag": tag})
                return f"{self.api.base_url}/Items/{quote(str(item_id), safe='')}/Images/{kind}?{query}"
        return None

    async def command(self, command: str, position: float | None = None) -> None:
        if not self.supports_remote_control:
            raise EmbyApiError("The player is currently unavailable for remote control")
        session_id = quote(str(self.session["Id"]), safe="")
        params = (
            {} if position is None else {"SeekPositionTicks": int(max(0, position) * 10_000_000)}
        )
        await self.api._request("POST", f"/Sessions/{session_id}/Playing/{command}", params=params)

    async def media_play(self) -> None:
        await self.command("Unpause")

    async def media_pause(self) -> None:
        await self.command("Pause")

    async def media_stop(self) -> None:
        await self.command("Stop")

    async def media_next(self) -> None:
        await self.command("NextTrack")

    async def media_previous(self) -> None:
        await self.command("PreviousTrack")

    async def media_seek(self, position: float) -> None:
        await self.command("Seek", position)


class EmbySessionStream:
    """One cancellable worker: push updates with bounded REST fallback and retries."""

    def __init__(self, api: EmbyApiClient, hass: Any, entry: Any) -> None:
        self.api = api
        self.hass = hass
        self.entry = entry
        self.devices: dict[str, SessionDevice] = {}
        self.available = False
        self.last_success_at: str | None = None
        self.transport = "starting"
        self._last_success_monotonic = 0.0
        self._task: asyncio.Task | None = None
        self._device_callbacks: list[Callable] = []
        self._stale_callbacks: list[Callable] = []
        self._update_callbacks: dict[str, list[Callable]] = {}
        self._snapshot_callbacks: list[Callable] = []

    @property
    def active_player_count(self) -> int | None:
        """Count unique playing/paused clients, or report incomplete knowledge."""
        if not self.available:
            return None
        current = [device for device in self.devices.values() if device.is_active]
        if any(device.activity == "unknown" for device in current):
            return None
        return sum(device.activity in ACTIVE for device in current)

    def add_snapshot_callback(self, callback: Callable) -> Callable[[], None]:
        """Subscribe to complete snapshots, including empty and unavailable ones."""
        self._snapshot_callbacks.append(callback)

        def unsubscribe() -> None:
            if callback in self._snapshot_callbacks:
                self._snapshot_callbacks.remove(callback)

        return unsubscribe

    def add_new_devices_callback(self, callback: Callable) -> None:
        """Reevaluate visibility on every changed snapshot, including idle → playing."""
        self._device_callbacks.append(callback)

    def add_stale_devices_callback(self, callback: Callable) -> None:
        self._stale_callbacks.append(callback)

    def add_update_callback(self, callback: Callable, key: str) -> Callable[[], None]:
        listeners = self._update_callbacks.setdefault(key, [])
        listeners.append(callback)

        def unsubscribe() -> None:
            if callback in listeners:
                listeners.remove(callback)
            if not listeners:
                self._update_callbacks.pop(key, None)

        return unsubscribe

    def update_device_list(self, data: Any) -> None:
        sessions = validate_sessions(data)
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in sessions:
            key = session_key(item)
            if key is not None and item.get("DeviceId") != f"embi-{self.entry.entry_id}":
                grouped.setdefault(key, []).append(item)
        changed = set()
        for key, items in grouped.items():
            device = self.devices.setdefault(key, SessionDevice(self.api))
            before = (device.session, device.activity, device.is_active)
            device.update(items)
            if before != (device.session, device.activity, device.is_active):
                changed.add(key)
        for key, device in self.devices.items():
            if key not in grouped and device.is_active:
                device.is_active = False
                changed.add(key)
                _notify(self._stale_callbacks, key)
        self.available = True
        self.last_success_at = datetime.now(UTC).isoformat()
        self._last_success_monotonic = asyncio.get_running_loop().time()
        if changed:
            _notify(self._device_callbacks, None)
        for key in changed:
            _notify(self._update_callbacks.get(key, ()), key)
        _notify(self._snapshot_callbacks, None)

    def _unavailable(self) -> None:
        self.available = False
        for key, device in self.devices.items():
            if device.is_active:
                device.is_active = False
                _notify(self._stale_callbacks, key)
                _notify(self._update_callbacks.get(key, ()), key)
        _notify(self._snapshot_callbacks, None)

    async def _refresh(self) -> None:
        self.update_device_list(await self.api.async_get_sessions())

    async def _socket(self) -> None:
        socket = None
        try:
            async with asyncio.timeout(15):
                socket = await self.api._session.ws_connect(
                    f"{self.api.base_url}/embywebsocket",
                    headers=self.api._headers,
                    params={"DeviceId": f"embi-{self.entry.entry_id}"},
                    heartbeat=15,
                )
            await socket.send_json({"MessageType": "SessionsStart", "Data": "0,1500"})
            self.transport = "websocket"
            while True:
                remaining = REFRESH_SECONDS - (
                    asyncio.get_running_loop().time() - self._last_success_monotonic
                )
                if remaining <= 0:
                    await self._refresh()
                    continue
                try:
                    async with asyncio.timeout(remaining):
                        message = await socket.receive()
                except TimeoutError:
                    await self._refresh()
                    continue
                if message.type == WSMsgType.TEXT:
                    payload = message.json()
                    if not isinstance(payload, dict):
                        raise ValueError("Invalid websocket message")
                    if payload.get("MessageType") == "Sessions":
                        self.update_device_list(payload.get("Data"))
                elif message.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.ERROR):
                    raise EmbyApiError("Session stream disconnected")
        finally:
            if socket is not None:
                await socket.close()

    async def _run(self) -> None:
        try:
            while True:
                try:
                    await self._refresh()
                except EmbyAuthError:
                    self.transport = "authentication_failed"
                    self._unavailable()
                    self.entry.async_start_reauth(self.hass)
                    return
                except (EmbyApiError, ValueError):
                    self.transport = "offline"
                    self._unavailable()
                    await asyncio.sleep(RECONNECT_SECONDS)
                    continue
                try:
                    await self._socket()
                except EmbyAuthError:
                    self.transport = "authentication_failed"
                    self._unavailable()
                    self.entry.async_start_reauth(self.hass)
                    return
                except (ClientError, TimeoutError, EmbyApiError, ValueError, TypeError, OSError):
                    self.transport = "polling"
                    # A fresh REST observation remains valid while push reconnects.
                    # Never log exception text containing request URLs or headers.
                    _LOGGER.debug("Emby push unavailable; retrying with session polling")
                    await asyncio.sleep(RECONNECT_SECONDS)
        finally:
            self._unavailable()

    def start(self) -> None:
        if self._task is None:
            self._task = self.entry.async_create_background_task(
                self.hass, self._run(), "EMBi sessions"
            )

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None
        self._device_callbacks.clear()
        self._stale_callbacks.clear()
        self._update_callbacks.clear()
        self._snapshot_callbacks.clear()
