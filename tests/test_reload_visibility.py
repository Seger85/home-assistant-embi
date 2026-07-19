from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.emby import entry_setup, media_player
from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.const import (
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_REGISTRY_RECONCILIATION_FAILURES,
    CONF_REGISTRY_RECONCILIATION_VERSION,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    REGISTRY_RECONCILIATION_VERSION,
)
from custom_components.emby.models import EmbiRuntimeData
from custom_components.emby.options_model import default_options
from custom_components.emby.player_actions import PlayerActionItem, PlayerActionResult


class FakeConfigEntries:
    def __init__(self) -> None:
        self.updates: list[dict] = []

    def async_update_entry(self, entry, **kwargs) -> None:
        self.updates.append(kwargs)
        if "options" in kwargs:
            entry.options = dict(kwargs["options"])


class FakeHass:
    def __init__(self) -> None:
        self.loop = asyncio.get_running_loop()
        self.config_entries = FakeConfigEntries()
        self.tasks: list[object] = []

    def async_create_task(self, coro, name=None):
        self.tasks.append(coro)
        return SimpleNamespace(name=name)


def reconciliation_result(
    *,
    protected: tuple[PlayerActionItem, ...] = (),
    failed: tuple[PlayerActionItem, ...] = (),
) -> PlayerActionResult:
    return PlayerActionResult("reconcile", 0, (), protected, failed)


@pytest.mark.asyncio
async def test_visibility_is_enforced_on_three_reloads_after_migration(monkeypatch) -> None:
    hass = FakeHass()
    options = default_options()
    options[CONF_REGISTRY_RECONCILIATION_VERSION] = REGISTRY_RECONCILIATION_VERSION
    options[CONF_REGISTRY_RECONCILIATION_FAILURES] = 0
    entry = SimpleNamespace(options=dict(options))
    reconcile = AsyncMock(return_value=reconciliation_result())
    monkeypatch.setattr(entry_setup, "async_reconcile_player_visibility", reconcile)

    for _ in range(3):
        result = await entry_setup._async_enforce_player_visibility(
            hass,
            entry,
            dict(options),
        )
        assert result is not None
        assert result.status == "completed"

    assert reconcile.await_count == 3
    assert hass.config_entries.updates == []


@pytest.mark.asyncio
async def test_migration_marker_does_not_gate_recurring_visibility(monkeypatch) -> None:
    hass = FakeHass()
    options = default_options()
    options[CONF_REGISTRY_RECONCILIATION_VERSION] = 0
    entry = SimpleNamespace(options=dict(options))
    reconcile = AsyncMock(return_value=reconciliation_result())
    monkeypatch.setattr(entry_setup, "async_reconcile_player_visibility", reconcile)

    await entry_setup._async_enforce_player_visibility(hass, entry, options)
    assert options[CONF_REGISTRY_RECONCILIATION_VERSION] == REGISTRY_RECONCILIATION_VERSION
    assert options[CONF_REGISTRY_RECONCILIATION_FAILURES] == 0
    assert len(hass.config_entries.updates) == 1

    hass.config_entries.updates.clear()
    await entry_setup._async_enforce_player_visibility(hass, entry, options)
    assert reconcile.await_count == 2
    assert hass.config_entries.updates == []


@pytest.mark.asyncio
async def test_playback_protection_does_not_disable_future_enforcement(monkeypatch) -> None:
    hass = FakeHass()
    options = default_options()
    options[CONF_REGISTRY_RECONCILIATION_VERSION] = REGISTRY_RECONCILIATION_VERSION
    entry = SimpleNamespace(options=dict(options))
    protected = (
        PlayerActionItem(
            "media_player.technical",
            "technical.Home Assistant",
            "Technical · Home Assistant",
            "protected",
            "paused",
        ),
    )
    reconcile = AsyncMock(
        side_effect=[
            reconciliation_result(protected=protected),
            reconciliation_result(),
        ]
    )
    monkeypatch.setattr(entry_setup, "async_reconcile_player_visibility", reconcile)

    first = await entry_setup._async_enforce_player_visibility(hass, entry, dict(options))
    second = await entry_setup._async_enforce_player_visibility(hass, entry, dict(options))

    assert first is not None and first.protected == protected
    assert second is not None and second.status == "completed"
    assert reconcile.await_count == 2
    assert hass.config_entries.updates == []


class FakeEmbyServer:
    instance = None

    def __init__(self, *_args, **_kwargs) -> None:
        type(self).instance = self
        self.devices: dict[str, object] = {}
        self.new_callback = None
        self.stale_callback = None

    def add_new_devices_callback(self, callback) -> None:
        self.new_callback = callback

    def add_stale_devices_callback(self, callback) -> None:
        self.stale_callback = callback

    def start(self) -> None:
        return None

    def add_update_callback(self, *_args) -> None:
        return None


def technical_record() -> EmbyDeviceRecord:
    return EmbyDeviceRecord.from_api(
        {
            "Id": "technical-record",
            "ReportedDeviceId": "technical-device",
            "Name": "Gerryflix Server",
            "AppName": "Home Assistant",
            "ClientType": "integration",
            "SupportsPlayback": False,
        }
    )


def fake_device(state: str):
    return SimpleNamespace(
        state=state,
        name="Gerryflix Server",
        username="Home Assistant",
        supports_remote_control=False,
        media_position=None,
        is_nowplaying=False,
        media_id=None,
        media_type=None,
        media_runtime=None,
        media_image_url=None,
        media_title=None,
        media_season=None,
        media_series_title=None,
        media_episode=None,
        media_album_name=None,
        media_artist=None,
        media_album_artist=None,
    )


def media_entry(*, technical_visible: bool, hidden: bool = False):
    record = technical_record()
    options = default_options()
    options[CONF_TECHNICAL_ACCESS_VISIBILITY] = technical_visible
    if hidden:
        options[CONF_HIDDEN_EXACT_PLAYERS] = [record.player_key]
    runtime = EmbiRuntimeData(
        api_client=SimpleNamespace(_request=AsyncMock(return_value=[])),
        devices=[record],
    )
    entry = SimpleNamespace(
        data={"host": "server", "api_key": "secret", "port": 8096, "ssl": False},
        options=options,
        runtime_data=runtime,
    )
    return entry, record


@pytest.mark.asyncio
async def test_fresh_platform_setup_reconciles_hidden_registry_key_without_local_entity(
    monkeypatch,
) -> None:
    hass = FakeHass()
    entry, record = media_entry(technical_visible=False)
    reconcile = AsyncMock(return_value=reconciliation_result())
    monkeypatch.setattr(media_player, "EmbyServer", FakeEmbyServer)
    monkeypatch.setattr(media_player, "async_reconcile_player_visibility", reconcile)
    added: list[object] = []

    await media_player.async_setup_entry(hass, entry, added.extend)
    emby = FakeEmbyServer.instance
    assert emby is not None and emby.new_callback is not None
    emby.devices[record.player_key] = fake_device("Idle")
    emby.new_callback({})

    assert added == []
    assert len(hass.tasks) == 1
    await hass.tasks.pop()
    reconcile.assert_awaited_once_with(
        hass,
        entry,
        requested_keys=(record.player_key,),
    )


@pytest.mark.asyncio
async def test_master_on_restores_same_unique_id_without_reconciliation(monkeypatch) -> None:
    hass = FakeHass()
    entry, record = media_entry(technical_visible=True)
    reconcile = AsyncMock(return_value=reconciliation_result())
    monkeypatch.setattr(media_player, "EmbyServer", FakeEmbyServer)
    monkeypatch.setattr(media_player, "async_reconcile_player_visibility", reconcile)
    added: list[object] = []

    await media_player.async_setup_entry(hass, entry, added.extend)
    emby = FakeEmbyServer.instance
    assert emby is not None and emby.new_callback is not None
    emby.devices[record.player_key] = fake_device("Idle")
    emby.new_callback({})

    assert len(added) == 1
    assert added[0].unique_id == record.player_key
    assert hass.tasks == []
    reconcile.assert_not_awaited()


@pytest.mark.asyncio
async def test_master_on_exact_exception_remains_removed(monkeypatch) -> None:
    hass = FakeHass()
    entry, record = media_entry(technical_visible=True, hidden=True)
    reconcile = AsyncMock(return_value=reconciliation_result())
    monkeypatch.setattr(media_player, "EmbyServer", FakeEmbyServer)
    monkeypatch.setattr(media_player, "async_reconcile_player_visibility", reconcile)
    added: list[object] = []

    await media_player.async_setup_entry(hass, entry, added.extend)
    emby = FakeEmbyServer.instance
    assert emby is not None and emby.new_callback is not None
    emby.devices[record.player_key] = fake_device("Idle")
    emby.new_callback({})

    assert added == []
    await hass.tasks.pop()
    reconcile.assert_awaited_once_with(
        hass,
        entry,
        requested_keys=(record.player_key,),
    )


@pytest.mark.asyncio
async def test_paused_technical_player_is_protected_then_removed_after_idle(monkeypatch) -> None:
    hass = FakeHass()
    entry, record = media_entry(technical_visible=False)
    reconcile = AsyncMock(return_value=reconciliation_result())
    monkeypatch.setattr(media_player, "EmbyServer", FakeEmbyServer)
    monkeypatch.setattr(media_player, "async_reconcile_player_visibility", reconcile)
    added: list[object] = []

    await media_player.async_setup_entry(hass, entry, added.extend)
    emby = FakeEmbyServer.instance
    assert emby is not None and emby.new_callback is not None
    emby.devices[record.player_key] = fake_device("Paused")
    emby.new_callback({})

    assert len(added) == 1
    assert hass.tasks == []
    reconcile.assert_not_awaited()

    emby.devices[record.player_key].state = "Idle"
    emby.new_callback({})
    assert len(hass.tasks) == 1
    await hass.tasks.pop()
    reconcile.assert_awaited_once_with(
        hass,
        entry,
        requested_keys=(record.player_key,),
    )
