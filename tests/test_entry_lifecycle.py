from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.emby.entry_lifecycle import async_migrate_entry, async_unload_entry
from custom_components.emby.models import EmbiRuntimeData


class FakeConfigEntries:
    def __init__(self) -> None:
        self.updated: list[dict] = []
        self.unload_result = True

    def async_update_entry(self, entry, **kwargs) -> None:
        self.updated.append(kwargs)
        for key, value in kwargs.items():
            setattr(entry, key, value)

    async def async_unload_platforms(self, entry, platforms):
        return self.unload_result


class FakeHass:
    def __init__(self) -> None:
        self.config_entries = FakeConfigEntries()


class FakePyEmby:
    def __init__(self) -> None:
        self.stop_calls = 0

    async def stop(self) -> None:
        self.stop_calls += 1


@pytest.mark.asyncio
async def test_config_entry_version_migration_is_idempotent() -> None:
    hass = FakeHass()
    entry = SimpleNamespace(version=2, minor_version=0)
    assert await async_migrate_entry(hass, entry) is True
    assert hass.config_entries.updated == [{"version": 3, "minor_version": 1}]

    hass.config_entries.updated.clear()
    assert await async_migrate_entry(hass, entry) is True
    assert hass.config_entries.updated == []


@pytest.mark.asyncio
async def test_unload_cancels_scheduler_and_stops_pyemby_once() -> None:
    hass = FakeHass()
    cancelled = 0

    def cancel() -> None:
        nonlocal cancelled
        cancelled += 1

    pyemby = FakePyEmby()
    runtime = EmbiRuntimeData(api_client=object(), pyemby=pyemby)
    runtime.cancel_auto_cleanup = cancel
    runtime.auto_cleanup_scheduled = True
    entry = SimpleNamespace(runtime_data=runtime)

    assert await async_unload_entry(hass, entry) is True
    assert cancelled == 1
    assert runtime.cancel_auto_cleanup is None
    assert runtime.auto_cleanup_scheduled is False
    assert pyemby.stop_calls == 1


@pytest.mark.asyncio
async def test_failed_platform_unload_keeps_runtime_running() -> None:
    hass = FakeHass()
    hass.config_entries.unload_result = False
    pyemby = FakePyEmby()
    runtime = EmbiRuntimeData(api_client=object(), pyemby=pyemby)
    runtime.cancel_auto_cleanup = lambda: None
    entry = SimpleNamespace(runtime_data=runtime)

    assert await async_unload_entry(hass, entry) is False
    assert runtime.cancel_auto_cleanup is not None
    assert pyemby.stop_calls == 0
