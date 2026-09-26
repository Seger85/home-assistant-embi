from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientSession, web

from custom_components.emby.api import (
    EmbyApiClient,
    EmbyApiError,
    EmbyAuthError,
    EmbyDeleteUncertain,
)


def client():
    return EmbyApiClient(AsyncMock(), "localhost", 8096, "secret", False)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"Items": {}},
        {"Items": [{"Name": "missing id"}]},
        ["invalid"],
        [{"Id": "a"}, {"Id": "a"}],
    ],
)
async def test_bad_device_inventory_cannot_become_an_empty_success(payload):
    api = client()
    api._request = AsyncMock(return_value=payload)
    with pytest.raises(EmbyApiError):
        await api.async_get_devices()


@pytest.mark.asyncio
async def test_selective_counts_do_not_require_disabled_sensor_fields():
    api = client()
    api._request = AsyncMock(return_value={"MovieCount": 0})
    assert await api.async_get_library_counts({"movie_count"}) == {"movie_count": 0}
    api._request.assert_awaited_once_with("GET", "/Items/Counts")
    api._request.reset_mock()
    assert await api.async_get_library_counts(set()) == {}
    api._request.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [True, -1, 1.5, None, "many"])
async def test_invalid_counts_are_not_coerced_into_plausible_numbers(value):
    api = client()
    api._request = AsyncMock(return_value={"MovieCount": value})
    with pytest.raises(EmbyApiError):
        await api.async_get_library_counts({"movie_count"})


@pytest.mark.asyncio
async def test_viewers_are_unique_users_and_incomplete_data_is_not_zero():
    api = client()
    base = {
        "DeviceId": "device",
        "Client": "App",
        "UserId": "user",
        "NowPlayingItem": {"Id": "film"},
        "PlayState": {"IsPaused": False},
    }
    api.async_get_sessions = AsyncMock(
        return_value=[
            base,
            {**base, "DeviceId": "other"},
            {**base, "UserId": "paused", "PlayState": {"IsPaused": True}},
        ]
    )
    assert await api.async_get_watching_users() == {"users_watching": 1}
    api.async_get_sessions.return_value = [{**base, "PlayState": {}}]
    with pytest.raises(EmbyApiError):
        await api.async_get_watching_users()
    api.async_get_sessions.return_value = []
    assert await api.async_get_watching_users() == {"users_watching": 0}


@pytest.mark.asyncio
async def test_invalid_json_auth_rejection_and_uncertain_delete(aiohttp_server):
    status = 200

    async def response(request):
        return web.Response(text="{invalid-json", content_type="application/json", status=status)

    app = web.Application()
    app.router.add_route("*", "/{path:.*}", response)
    server = await aiohttp_server(app)
    async with ClientSession() as session:
        api = EmbyApiClient(session, server.host, server.port, "private-token", False)
        with pytest.raises(EmbyApiError, match="invalid data"):
            await api.async_get_devices()
        status = 401
        with pytest.raises(EmbyAuthError):
            await api.async_get_sessions()
        status = 500
        with pytest.raises(EmbyDeleteUncertain):
            await api.async_delete_device("record")
        status = 404
        with pytest.raises(EmbyApiError) as error:
            await api.async_delete_device("record")
        assert not isinstance(error.value, EmbyDeleteUncertain)
        assert "private-token" not in str(error.value)
