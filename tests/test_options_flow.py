from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.const import (
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_GLOBAL_PLAYER_MODE,
    CONF_ONLY_DURING_PLAYBACK,
    CONF_SEARCH_QUERY,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_AGE_DAYS,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    PLAYER_MODE_ACTIVE_ONLY,
    PLAYER_MODE_PERSISTENT,
)
from custom_components.emby.entry_lifecycle import async_update_listener
from custom_components.emby.models import EmbiRuntimeData, MaintenanceState
from custom_components.emby.options_flow import EmbyOptionsFlow
from custom_components.emby.options_model import default_options_090


class FakeApi:
    def __init__(self, devices: list[EmbyDeviceRecord]) -> None:
        self.devices = devices

    async def async_get_devices(self) -> list[EmbyDeviceRecord]:
        return list(self.devices)


class FakeStore:
    def __init__(self) -> None:
        self.saved: list[MaintenanceState] = []

    async def async_save(self, state: MaintenanceState) -> None:
        self.saved.append(state)


class FakeConfigEntries:
    def __init__(self) -> None:
        self.updates: list[dict] = []
        self.reloads: list[str] = []
        self.entry = None

    def async_update_entry(self, entry, **kwargs) -> None:
        self.updates.append(kwargs)
        if "options" in kwargs:
            entry.options = dict(kwargs["options"])

    async def async_reload(self, entry_id: str) -> bool:
        self.reloads.append(entry_id)
        return True

    def async_get_entry(self, entry_id: str):
        return self.entry if self.entry and self.entry.entry_id == entry_id else None


class FakeHass:
    def __init__(self) -> None:
        self.config = SimpleNamespace(language="de")
        self.config_entries = FakeConfigEntries()
        self.data = {}
        self.states = SimpleNamespace(get=lambda _entity_id: None)
        self.registry = SimpleNamespace(
            entities={},
            async_get=lambda _entity_id: None,
            async_update_entity=lambda _entity_id, **_kwargs: None,
        )

    async def async_block_till_done(self) -> None:
        return None


@dataclass
class FakeEntry:
    options: dict
    runtime_data: EmbiRuntimeData
    entry_id: str = "entry"
    version: int = 4
    minor_version: int = 0


def device() -> EmbyDeviceRecord:
    return EmbyDeviceRecord.from_api(
        {
            "Id": "history-1",
            "ReportedDeviceId": "client.with.dot",
            "Name": "Living room",
            "AppName": "Emby App",
            "LastUserName": "Alex",
            "SupportsPlayback": True,
        }
    )


def default_options() -> dict:
    return default_options_090()


def setup_flow(
    options: dict | None = None,
) -> tuple[EmbyOptionsFlow, FakeEntry, FakeStore, FakeHass]:
    store = FakeStore()
    runtime = EmbiRuntimeData(
        api_client=FakeApi([device()]),
        maintenance_store=store,
        maintenance_state=MaintenanceState(),
    )
    entry = FakeEntry(options or default_options(), runtime)
    hass = FakeHass()
    hass.config_entries.entry = entry
    flow = EmbyOptionsFlow(entry)
    flow.hass = hass
    return flow, entry, store, hass


def stats() -> SimpleNamespace:
    return SimpleNamespace(
        server_history_records=1,
        ha_players=1,
        protected_playback=0,
        removable_from_ha=1,
        known_users=1,
    )


async def empty_catalog(_flow):
    return [], stats()


def patch_catalog(monkeypatch) -> None:
    monkeypatch.setattr("custom_components.emby.options_flow.fresh_catalog", empty_catalog)
    monkeypatch.setattr("custom_components.emby.options_devices.fresh_catalog", empty_catalog)
    monkeypatch.setattr("custom_components.emby.options_cleanup.fresh_catalog", empty_catalog)
    monkeypatch.setattr("custom_components.emby.options_ha_cleanup.fresh_catalog", empty_catalog)


@pytest.mark.asyncio
async def test_root_contains_only_devices_cleanup_and_review_when_dirty(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, _entry, _store, _hass = setup_flow()

    clean = await flow.async_step_init()
    assert clean["type"] == "menu"
    assert clean["menu_options"] == ["devices_players", "cleanup"]

    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    dirty = await flow.async_step_init()
    assert dirty["menu_options"] == ["devices_players", "cleanup", "review_changes"]


@pytest.mark.asyncio
async def test_devices_page_updates_only_the_in_memory_draft(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, entry, store, hass = setup_flow()
    original = dict(entry.options)

    result = await flow.async_step_devices_players(
        {
            CONF_ONLY_DURING_PLAYBACK: True,
            CONF_AUTO_SHOW_NEW_PLAYERS: False,
            CONF_TECHNICAL_ACCESS_VISIBILITY: True,
            CONF_SEARCH_QUERY: "Alex",
        }
    )

    assert result["type"] == "menu"
    assert flow._draft_options[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_ACTIVE_ONLY
    assert flow._draft_options[CONF_AUTO_SHOW_NEW_PLAYERS] is False
    assert flow._draft_options[CONF_TECHNICAL_ACCESS_VISIBILITY] is True
    assert entry.options == original
    assert hass.config_entries.updates == []
    assert hass.config_entries.reloads == []
    assert store.saved == []


@pytest.mark.asyncio
async def test_apply_writes_once_and_reloads_once_without_confirmation_toggle(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, entry, store, hass = setup_flow()
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY

    result = await flow.async_step_apply_changes()

    assert result["type"] == "abort"
    assert result["reason"] == "apply_complete"
    assert len(hass.config_entries.updates) == 1
    assert entry.options[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_ACTIVE_ONLY
    assert hass.config_entries.reloads == [entry.entry_id]
    assert store.saved == []


@pytest.mark.asyncio
async def test_unchanged_apply_aborts_without_write_or_reload(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, _entry, store, hass = setup_flow()
    result = await flow.async_step_apply_changes()
    assert result == {"type": "abort", "reason": "no_changes"}
    assert hass.config_entries.updates == []
    assert hass.config_entries.reloads == []
    assert store.saved == []


@pytest.mark.asyncio
async def test_discard_restores_original_without_write_or_reload(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, entry, store, hass = setup_flow()
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY

    result = await flow.async_step_discard_changes()

    assert result["type"] == "menu"
    assert flow._draft_options == entry.options
    assert flow._dirty is False
    assert hass.config_entries.updates == []
    assert hass.config_entries.reloads == []
    assert store.saved == []


@pytest.mark.asyncio
async def test_closing_flow_with_dirty_draft_has_no_side_effects() -> None:
    flow, entry, store, hass = setup_flow()
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    assert flow._dirty is True
    del flow
    assert entry.options[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_PERSISTENT
    assert hass.config_entries.updates == []
    assert hass.config_entries.reloads == []
    assert store.saved == []


@pytest.mark.asyncio
async def test_enabling_automatic_cleanup_resets_deadline_before_apply(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, entry, store, hass = setup_flow()
    flow._runtime.maintenance_state.initial_run_completed = True
    flow._runtime.maintenance_state.report.next_run_at = "2026-07-16T12:00:00+00:00"
    flow._draft_options[CONF_SERVER_AUTO_CLEANUP_ENABLED] = True

    result = await flow.async_step_apply_changes()

    assert result["reason"] == "apply_complete"
    assert len(store.saved) == 1
    assert store.saved[0].initial_run_completed is False
    assert store.saved[0].report.next_run_at is None
    assert entry.options[CONF_SERVER_AUTO_CLEANUP_ENABLED] is True
    assert hass.config_entries.reloads == [entry.entry_id]


@pytest.mark.asyncio
async def test_exact_cleanup_values_survive_unrelated_draft_apply(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    options = default_options()
    options[CONF_SERVER_CLEANUP_AGE_DAYS] = 364
    options[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS] = 365
    options[CONF_SERVER_AUTO_CLEANUP_ENABLED] = True
    options[CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES] = True
    flow, entry, _store, _hass = setup_flow(options)
    flow._draft_options[CONF_AUTO_SHOW_NEW_PLAYERS] = False

    await flow.async_step_apply_changes()

    assert entry.options[CONF_SERVER_CLEANUP_AGE_DAYS] == 364
    assert entry.options[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS] == 365
    assert entry.options[CONF_SERVER_AUTO_CLEANUP_ENABLED] is True
    assert entry.options[CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES] is True


@pytest.mark.asyncio
async def test_dirty_draft_blocks_destructive_entry_points(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, _entry, _store, _hass = setup_flow()
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY

    assert await flow.async_step_manage_ha_players() == {
        "type": "abort",
        "reason": "unsaved_changes",
    }
    assert await flow.async_step_server_history_check() == {
        "type": "abort",
        "reason": "unsaved_changes",
    }


@pytest.mark.asyncio
async def test_update_listener_performs_exactly_one_reload() -> None:
    _flow, entry, _store, hass = setup_flow()
    await async_update_listener(hass, entry)
    assert hass.config_entries.reloads == [entry.entry_id]
