"""Tests against genuine Home Assistant, without the lightweight tests/ stubs."""

from __future__ import annotations

import sys
from pathlib import Path
from types import MappingProxyType

import pytest
import pytest_asyncio
from homeassistant.auth import auth_manager_from_config
from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import frame

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest_asyncio.fixture
async def hass(tmp_path, monkeypatch):
    # Keep tests independent of host adapter enumeration / multicast permissions.
    import aiohttp

    def resolver(_hass):
        result = aiohttp.ThreadedResolver()
        result.real_close = result.close
        return result

    monkeypatch.setattr("homeassistant.helpers.aiohttp_client._async_make_resolver", resolver)
    monkeypatch.setattr("ifaddr.get_adapters", lambda: [])
    instance = HomeAssistant(str(tmp_path))
    instance.config.time_zone = "UTC"
    instance.config.language = "de"
    frame.async_setup(instance)
    dr.async_setup(instance)
    instance.config_entries = ConfigEntries(instance, {})
    await instance.config_entries.async_initialize()
    await dr.async_load(instance, load_empty=True)
    await er.async_load(instance, load_empty=True)
    instance.auth = await auth_manager_from_config(instance, [], [])
    yield instance
    await instance.async_stop(force=True)


@pytest.fixture
def entry_factory():
    return make_entry


@pytest.fixture
def entry():
    return make_entry()


def make_entry(*, data=None, options=None, unique_id="test-server"):
    return ConfigEntry(
        version=4,
        minor_version=2,
        domain="emby",
        title="EMBi",
        data=data or {"host": "127.0.0.1", "port": 8096, "api_key": "test-secret", "ssl": False},
        options=options or {},
        source="user",
        unique_id=unique_id,
        discovery_keys=MappingProxyType({}),
        subentries_data=None,
    )
