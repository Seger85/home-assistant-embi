from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.emby.entry_lifecycle import async_update_listener
from custom_components.emby.models import EmbiRuntimeData


class ConfigEntries:
    def __init__(self) -> None:
        self.reloads: list[str] = []

    async def async_reload(self, entry_id: str) -> None:
        self.reloads.append(entry_id)


class Hass:
    def __init__(self) -> None:
        self.config_entries = ConfigEntries()
        self.data = {}


@pytest.mark.asyncio
async def test_runtime_managed_write_suppresses_listener_reload() -> None:
    hass = Hass()
    runtime = EmbiRuntimeData(api_client=object())
    runtime.suppress_update_listener = True
    entry = SimpleNamespace(entry_id="entry", runtime_data=runtime)

    await async_update_listener(hass, entry)

    assert hass.config_entries.reloads == []


@pytest.mark.asyncio
async def test_external_write_still_reloads_once() -> None:
    hass = Hass()
    runtime = EmbiRuntimeData(api_client=object())
    entry = SimpleNamespace(entry_id="entry", runtime_data=runtime)

    await async_update_listener(hass, entry)

    assert hass.config_entries.reloads == ["entry"]
