from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientSession, web
from homeassistant.helpers.entity_platform import EntityPlatform

from custom_components.emby.api import EmbyApiClient, EmbyApiError
from custom_components.emby.media_player import EmbyDevice
from custom_components.emby.session_stream import EmbySessionStream


def session(*, paused=False, position=20):
    return {
        "Id": "session",
        "DeviceId": "client",
        "Client": "App",
        "DeviceName": "TV",
        "SupportsRemoteControl": True,
        "NowPlayingItem": {
            "Id": "film",
            "Name": "Film",
            "RunTimeTicks": 600_000_000,
            "ImageTags": {"Primary": "image-tag"},
        },
        "PlayState": {"IsPaused": paused, "PositionTicks": position * 10_000_000},
    }


@pytest.mark.asyncio
async def test_idle_to_playing_calls_visibility_and_duplicate_sessions_are_order_independent(
    hass, entry
):
    stream = EmbySessionStream(AsyncMock(), hass, entry)
    changes = []
    stream.add_new_devices_callback(lambda _: changes.append(True))
    idle = {"Id": "idle", "DeviceId": "client", "Client": "App"}
    stream.update_device_list([idle])
    assert stream.devices["client.App"].state == "Idle"
    stream.update_device_list([session(), idle])
    assert len(changes) == 2
    assert stream.devices["client.App"].state == "Playing"
    stream.update_device_list([idle, session()])
    assert len(changes) == 2
    assert stream.devices["client.App"].session["Id"] == "session"
    stream.update_device_list([])
    assert not stream.devices["client.App"].is_active
    stream.update_device_list([session(paused=True)])
    assert stream.devices["client.App"].state == "Paused"


@pytest.mark.asyncio
async def test_entity_listener_zero_seek_new_item_and_image_token(hass, entry):
    api = EmbyApiClient(AsyncMock(), "127.0.0.1", 8096, "test-secret", False)
    stream = EmbySessionStream(api, hass, entry)
    stream.update_device_list([session()])
    player = EmbyDevice(stream, "client.App")
    player.platform = EntityPlatform(
        hass=hass,
        logger=logging.getLogger(__name__),
        domain="media_player",
        platform_name="emby",
        platform=None,
        scan_interval=timedelta(seconds=30),
        entity_namespace=None,
    )
    player.hass = hass
    player.entity_id = "media_player.emby_tv"
    await player.async_internal_added_to_hass()
    await player.async_added_to_hass()
    assert player.media_position == 20
    assert "test-secret" not in player.media_image_url
    stream.update_device_list([session(position=0)])
    assert player.media_position == 0
    assert player.media_position_updated_at is not None
    stream.update_device_list([])
    assert not player.available
    assert player.media_position is None
    await player.async_remove()
    assert stream._update_callbacks == {}


@pytest.mark.asyncio
async def test_real_http_websocket_auth_commands_and_stop(hass, entry, aiohttp_server):
    received = []
    pushed = asyncio.Event()
    socket_closed = asyncio.Event()

    async def sessions(request):
        assert request.headers["X-Emby-Token"] == "test-secret"
        assert "api_key" not in request.query
        return web.json_response([session()])

    async def socket(request):
        assert request.headers["X-Emby-Token"] == "test-secret"
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        received.append(await ws.receive_json())
        await ws.send_json({"MessageType": "Sessions", "Data": [session(paused=True)]})
        pushed.set()
        async for _ in ws:
            pass
        socket_closed.set()
        return ws

    async def command(request):
        received.append((request.match_info["command"], dict(request.query)))
        return web.Response(status=204)

    app = web.Application()
    app.router.add_get("/Sessions", sessions)
    app.router.add_get("/embywebsocket", socket)
    app.router.add_post("/Sessions/session/Playing/{command}", command)
    server = await aiohttp_server(app)
    async with ClientSession() as client:
        api = EmbyApiClient(client, server.host, server.port, "test-secret", False)
        stream = EmbySessionStream(api, hass, entry)
        updated = asyncio.Event()
        stream.add_new_devices_callback(
            lambda _: updated.set() if stream.devices["client.App"].state == "Paused" else None
        )
        stream.start()
        await asyncio.wait_for(updated.wait(), 2)
        assert received[0] == {"MessageType": "SessionsStart", "Data": "0,1500"}
        await stream.devices["client.App"].media_seek(0)
        assert received[-1] == ("Seek", {"SeekPositionTicks": "0"})
        await stream.stop()
        await asyncio.wait_for(socket_closed.wait(), 2)
        assert not client.closed  # The transport never closes HA's shared session.
        assert not entry._background_tasks


@pytest.mark.asyncio
async def test_initial_failure_retries_and_stop_cancels_retry(hass, entry, monkeypatch):
    api = AsyncMock()
    api.async_get_sessions.side_effect = [EmbyApiError("offline"), [session()]]
    stream = EmbySessionStream(api, hass, entry)
    monkeypatch.setattr("custom_components.emby.session_stream.RECONNECT_SECONDS", 0.01)
    reached = asyncio.Event()

    async def socket():
        reached.set()
        await asyncio.Event().wait()

    stream._socket = socket
    stream.start()
    await asyncio.wait_for(reached.wait(), 2)
    assert stream.available
    assert api.async_get_sessions.await_count == 2
    await stream.stop()
    assert not stream.available
    assert not entry._background_tasks
