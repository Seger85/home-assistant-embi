from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.emby import (
    entry_setup,
    media_player,
    player_actions,
    player_reconciliation,
)
from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.const import (
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_REGISTRY_RECONCILIATION_FAILURES,
    CONF_REGISTRY_RECONCILIATION_VERSION,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    REGISTRY_RECONCILIATION_VERSION,
)
from custom_components.emby.options_model import default_options, should_expose_player
from custom_components.emby.player_actions import PlayerActionResult


def _hass():
    return SimpleNamespace(
        config_entries=SimpleNamespace(async_update_entry=Mock()),
        states=SimpleNamespace(get=lambda _entity_id: None),
    )


@pytest.mark.asyncio
async def test_current_marker_still_enforces_visibility_on_three_reloads(monkeypatch) -> None:
    reconcile = AsyncMock(return_value=PlayerActionResult("reconcile", 0, (), (), ()))
    monkeypatch.setattr(entry_setup, "async_reconcile_player_visibility", reconcile)
    hass = _hass()
    entry = SimpleNamespace()
    options = {
        CONF_REGISTRY_RECONCILIATION_VERSION: REGISTRY_RECONCILIATION_VERSION,
        CONF_REGISTRY_RECONCILIATION_FAILURES: 0,
    }
    for _ in range(3):
        await entry_setup._async_enforce_player_visibility(hass, entry, options)
    assert reconcile.await_count == 3
    hass.config_entries.async_update_entry.assert_not_called()


@pytest.mark.asyncio
async def test_setup_unload_setup_equivalent_runs_invariant_again(monkeypatch) -> None:
    reconcile = AsyncMock(return_value=PlayerActionResult("reconcile", 0, (), (), ()))
    monkeypatch.setattr(entry_setup, "async_reconcile_player_visibility", reconcile)
    hass = _hass()
    options = {CONF_REGISTRY_RECONCILIATION_VERSION: REGISTRY_RECONCILIATION_VERSION}
    await entry_setup._async_enforce_player_visibility(hass, SimpleNamespace(), options)
    await entry_setup._async_enforce_player_visibility(hass, SimpleNamespace(), options)
    assert reconcile.await_count == 2


@pytest.mark.asyncio
async def test_migration_marker_does_not_block_protected_runtime_entities(monkeypatch) -> None:
    protected = (SimpleNamespace(),)
    reconcile = AsyncMock(return_value=PlayerActionResult("reconcile", 1, (), protected, ()))
    monkeypatch.setattr(entry_setup, "async_reconcile_player_visibility", reconcile)
    hass = _hass()
    entry = SimpleNamespace()
    options = {
        CONF_REGISTRY_RECONCILIATION_VERSION: 0,
        CONF_REGISTRY_RECONCILIATION_FAILURES: 0,
    }
    await entry_setup._async_enforce_player_visibility(hass, entry, options)
    assert options[CONF_REGISTRY_RECONCILIATION_VERSION] == REGISTRY_RECONCILIATION_VERSION
    assert options[CONF_REGISTRY_RECONCILIATION_FAILURES] == 0


@pytest.mark.asyncio
async def test_empty_reconciliation_still_refreshes_diagnostics(monkeypatch) -> None:
    monkeypatch.setattr(
        player_reconciliation.player_actions,
        "_fresh_catalog",
        AsyncMock(return_value=[]),
    )
    record = AsyncMock()
    monkeypatch.setattr(player_reconciliation, "_async_record_reconciliation", record)
    result = await player_reconciliation.async_reconcile_player_visibility(_hass(), object())
    assert result.requested == 0
    assert result.status == "completed"
    record.assert_awaited_once()


def test_technical_master_and_exact_exception_contract() -> None:
    options = default_options()
    key = "technical.Home Assistant"
    assert not should_expose_player(
        player_key=key,
        reported_device_id="technical",
        state="idle",
        options=options,
        technical_access=True,
    )
    options[CONF_TECHNICAL_ACCESS_VISIBILITY] = True
    assert should_expose_player(
        player_key=key,
        reported_device_id="technical",
        state="idle",
        options=options,
        technical_access=True,
    )
    options[CONF_HIDDEN_EXACT_PLAYERS] = [key]
    assert not should_expose_player(
        player_key=key,
        reported_device_id="technical",
        state="idle",
        options=options,
        technical_access=True,
    )


def test_registry_ownership_is_exact() -> None:
    entry = SimpleNamespace(entry_id="entry")
    owned = SimpleNamespace(
        domain="media_player",
        platform="emby",
        config_entry_id="entry",
        unique_id="technical.Home Assistant",
    )
    foreign = SimpleNamespace(
        domain="media_player",
        platform="emby",
        config_entry_id="other",
        unique_id="technical.Home Assistant",
    )
    assert player_actions._owned_exact(owned, entry, "technical.Home Assistant")
    assert not player_actions._owned_exact(foreign, entry, "technical.Home Assistant")


class FakeEmby:
    def __init__(self, *_args):
        self.devices = {
            "technical.Home Assistant": SimpleNamespace(
                state="Idle",
                name="Home Assistant",
                username=None,
                supports_remote_control=False,
                media_position=None,
                is_nowplaying=False,
            )
        }
        self.new_callback = None
        self.stale_callback = None

    def add_new_devices_callback(self, callback):
        self.new_callback = callback

    def add_stale_devices_callback(self, callback):
        self.stale_callback = callback

    def add_update_callback(self, *_args):
        return None

    def start(self):
        assert self.new_callback is not None
        self.new_callback(None)


def _technical_record() -> EmbyDeviceRecord:
    return EmbyDeviceRecord.from_api(
        {
            "Id": "history-record",
            "ReportedDeviceId": "technical",
            "Name": "Home Assistant",
            "AppName": "Home Assistant",
            "SupportsPlayback": False,
        }
    )


@pytest.mark.asyncio
async def test_fresh_platform_reload_reconciles_disallowed_client_without_local_entity(
    monkeypatch,
) -> None:
    monkeypatch.setattr(media_player, "EmbyServer", FakeEmby)
    reconcile = AsyncMock(return_value=PlayerActionResult("reconcile", 1, (), (), ()))
    monkeypatch.setattr(media_player, "async_reconcile_player_visibility", reconcile)
    tasks = []
    hass = SimpleNamespace(
        loop=object(),
        async_create_task=lambda coro, _name: tasks.append(coro),
    )
    runtime = SimpleNamespace(
        pyemby=None,
        devices=[_technical_record()],
        api_client=SimpleNamespace(_request=AsyncMock(return_value=[])),
    )
    entry = SimpleNamespace(
        data={"host": "host", "api_key": "key", "port": 8096, "ssl": False},
        options={CONF_TECHNICAL_ACCESS_VISIBILITY: False},
        runtime_data=runtime,
    )
    added = []
    await media_player.async_setup_entry(hass, entry, lambda entities: added.extend(entities))
    assert added == []
    assert len(tasks) == 1
    await tasks[0]
    reconcile.assert_awaited_once_with(
        hass,
        entry,
        requested_keys=("technical.Home Assistant",),
    )


@pytest.mark.asyncio
async def test_master_on_restores_same_unique_id(monkeypatch) -> None:
    monkeypatch.setattr(media_player, "EmbyServer", FakeEmby)
    hass = SimpleNamespace(loop=object(), async_create_task=Mock())
    runtime = SimpleNamespace(pyemby=None, devices=[_technical_record()])
    entry = SimpleNamespace(
        data={"host": "host", "api_key": "key", "port": 8096, "ssl": False},
        options={CONF_TECHNICAL_ACCESS_VISIBILITY: True},
        runtime_data=runtime,
    )
    added = []
    await media_player.async_setup_entry(hass, entry, lambda entities: added.extend(entities))
    assert [entity.unique_id for entity in added] == ["technical.Home Assistant"]
    hass.async_create_task.assert_not_called()


@pytest.mark.asyncio
async def test_master_on_exact_exception_stays_removed(monkeypatch) -> None:
    monkeypatch.setattr(media_player, "EmbyServer", FakeEmby)
    reconcile = AsyncMock(return_value=PlayerActionResult("reconcile", 1, (), (), ()))
    monkeypatch.setattr(media_player, "async_reconcile_player_visibility", reconcile)
    tasks = []
    hass = SimpleNamespace(loop=object(), async_create_task=lambda coro, _name: tasks.append(coro))
    runtime = SimpleNamespace(
        pyemby=None,
        devices=[_technical_record()],
        api_client=SimpleNamespace(_request=AsyncMock(return_value=[])),
    )
    entry = SimpleNamespace(
        data={"host": "host", "api_key": "key", "port": 8096, "ssl": False},
        options={
            CONF_TECHNICAL_ACCESS_VISIBILITY: True,
            CONF_HIDDEN_EXACT_PLAYERS: ["technical.Home Assistant"],
        },
        runtime_data=runtime,
    )
    added = []
    await media_player.async_setup_entry(hass, entry, lambda entities: added.extend(entities))
    assert added == []
    assert len(tasks) == 1
    await tasks.pop()
    reconcile.assert_awaited_once_with(
        hass,
        entry,
        requested_keys=("technical.Home Assistant",),
    )


@pytest.mark.asyncio
async def test_paused_technical_player_is_protected_then_reconciled_when_idle(monkeypatch) -> None:
    class PausedFakeEmby(FakeEmby):
        def __init__(self, *_args):
            super().__init__()
            self.devices["technical.Home Assistant"].state = "Paused"

    monkeypatch.setattr(media_player, "EmbyServer", PausedFakeEmby)
    reconcile = AsyncMock(return_value=PlayerActionResult("reconcile", 1, (), (), ()))
    monkeypatch.setattr(media_player, "async_reconcile_player_visibility", reconcile)
    tasks = []
    hass = SimpleNamespace(loop=object(), async_create_task=lambda coro, _name: tasks.append(coro))
    runtime = SimpleNamespace(
        pyemby=None,
        devices=[_technical_record()],
        api_client=SimpleNamespace(_request=AsyncMock(return_value=[])),
    )
    entry = SimpleNamespace(
        data={"host": "host", "api_key": "key", "port": 8096, "ssl": False},
        options={CONF_TECHNICAL_ACCESS_VISIBILITY: False},
        runtime_data=runtime,
    )
    added = []
    await media_player.async_setup_entry(hass, entry, lambda entities: added.extend(entities))
    assert [entity.unique_id for entity in added] == ["technical.Home Assistant"]
    assert tasks == []
    server = runtime.pyemby
    server.devices["technical.Home Assistant"].state = "Idle"
    server.new_callback(None)
    assert len(tasks) == 1
    await tasks.pop()
    reconcile.assert_awaited_once_with(
        hass,
        entry,
        requested_keys=("technical.Home Assistant",),
    )


def test_reconciliation_never_calls_server_history_delete() -> None:
    source = Path(player_reconciliation.__file__).read_text(encoding="utf-8")
    assert "async_delete_device" not in source
    assert '"DELETE"' not in source
