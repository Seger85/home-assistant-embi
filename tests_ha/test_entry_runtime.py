"""Exercise the entry/platform lifecycle through Home Assistant's real manager."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from aiohttp import web
from homeassistant import loader
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from custom_components.emby.const import CONF_ENABLED_SENSORS


@pytest.mark.asyncio
async def test_setup_reload_unload_and_sensor_endpoint_independence(
    hass, entry_factory, aiohttp_server
):
    snapshots = [{"Id": "session", "DeviceId": "tv", "Client": "App", "DeviceName": "TV"}]
    calls = {"counts": 0, "sessions": 0}
    counts_ok = True

    async def info(request):
        return web.json_response({"Id": "test-server", "ServerName": "Test"})

    async def devices(request):
        return web.json_response(
            {"Items": [{"Id": "history", "ReportedDeviceId": "tv", "AppName": "App", "Name": "TV"}]}
        )

    async def counts(request):
        calls["counts"] += 1
        return web.json_response({"MovieCount": 7}) if counts_ok else web.Response(status=503)

    async def sessions(request):
        calls["sessions"] += 1
        return web.json_response(snapshots)

    async def socket(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        await ws.receive_json()
        await ws.send_json({"MessageType": "Sessions", "Data": snapshots})
        async for _ in ws:
            pass
        return ws

    app = web.Application()
    app.router.add_get("/System/Info", info)
    app.router.add_get("/Devices", devices)
    app.router.add_get("/Items/Counts", counts)
    app.router.add_get("/Sessions", sessions)
    app.router.add_get("/embywebsocket", socket)
    server = await aiohttp_server(app)
    (Path(hass.config.config_dir) / "custom_components").symlink_to(
        Path(__file__).parents[1] / "custom_components", target_is_directory=True
    )
    loader.async_setup(hass)
    assert await async_setup_component(hass, "network", {})
    entry = entry_factory(
        data={"host": server.host, "port": server.port, "api_key": "test-secret", "ssl": False},
        options={CONF_ENABLED_SENSORS: ["movie_count", "users_watching"]},
    )
    await hass.config_entries.async_add(entry)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    runtime = entry.runtime_data
    for _ in range(20):
        if runtime.session_client.available:
            break
        await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.emby_movie_count").state == "7"
    assert hass.states.get("sensor.emby_users_watching").state == "0"
    registry = er.async_get(hass)
    player_id = registry.async_get_entity_id("media_player", "emby", f"{entry.entry_id}::tv.App")
    assert player_id is not None
    original_registry_id = registry.async_get(player_id).id
    counts_ok = False
    await runtime.sensor_coordinators["library"].async_refresh()
    await runtime.sensor_coordinators["viewers"].async_refresh()
    assert hass.states.get("sensor.emby_movie_count").state == "unavailable"
    assert hass.states.get("sensor.emby_users_watching").state == "0"
    counts_ok = True
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert not runtime.session_client._task
    assert entry.runtime_data is not runtime
    assert registry.async_get(player_id).id == original_registry_id
    latest_runtime = entry.runtime_data
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert not entry._background_tasks
    assert not latest_runtime.auto_cleanup_scheduled
    assert not hasattr(entry, "runtime_data")
