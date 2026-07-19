from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.const import (
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_DELETE_DEVICE_RECORD_IDS,
    CONF_FLOW_ACTION,
    CONF_GLOBAL_PLAYER_MODE,
    CONF_ONLY_DURING_PLAYBACK,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    PLAYER_MODE_ACTIVE_ONLY,
    PLAYER_MODE_PERSISTENT,
)
from custom_components.emby.entry_lifecycle import async_update_listener
from custom_components.emby.models import CleanupRunReport, EmbiRuntimeData, MaintenanceState
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


class FakeStates:
    def __init__(self, values: dict[str, str] | None = None) -> None:
        self.values = values or {}

    def get(self, entity_id: str):
        value = self.values.get(entity_id)
        return SimpleNamespace(state=value) if value is not None else None


class FakeRegistry:
    def __init__(self) -> None:
        self.entities = {}

    def async_get(self, entity_id: str):
        return self.entities.get(entity_id)

    def async_update_entity(self, entity_id: str, **kwargs) -> None:
        return None


class FakeHass:
    def __init__(self) -> None:
        self.config = SimpleNamespace(language="de", time_zone="Europe/Berlin")
        self.config_entries = FakeConfigEntries()
        self.data = {}
        self.notifications = []
        self.states = FakeStates()
        self.registry = FakeRegistry()

    async def async_block_till_done(self) -> None:
        return None

    def async_create_task(self, coro, name=None):
        coro.close()
        return SimpleNamespace(name=name)


@dataclass
class FakeEntry:
    options: dict
    runtime_data: EmbiRuntimeData
    entry_id: str = "entry"
    version: int = 4
    minor_version: int = 0


def device(
    record_id: str = "history-1",
    *,
    reported_id: str = "client.with.dot",
    name: str = "Living room",
    app: str = "Emby App",
    activity: str = "2026-01-01T12:00:00Z",
) -> EmbyDeviceRecord:
    return EmbyDeviceRecord.from_api(
        {
            "Id": record_id,
            "ReportedDeviceId": reported_id,
            "Name": name,
            "AppName": app,
            "LastUserName": "Alex",
            "DateLastActivity": activity,
            "SupportsPlayback": True,
        }
    )


def setup_flow(options: dict | None = None, devices: list[EmbyDeviceRecord] | None = None):
    store = FakeStore()
    runtime = EmbiRuntimeData(
        api_client=FakeApi(devices or [device()]),
        maintenance_store=store,
        maintenance_state=MaintenanceState(),
    )
    entry = FakeEntry(options or default_options_090(), runtime)
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
        server_missing=0,
    )


async def empty_catalog(_flow):
    return [], stats()


def patch_catalog(monkeypatch) -> None:
    monkeypatch.setattr("custom_components.emby.options_flow.fresh_catalog", empty_catalog)
    monkeypatch.setattr("custom_components.emby.options_devices.fresh_catalog", empty_catalog)
    monkeypatch.setattr("custom_components.emby.options_ha_cleanup.fresh_catalog", empty_catalog)


def schema_keys(result) -> set[str]:
    return {str(getattr(marker, "schema", marker)) for marker in result["data_schema"].schema}


@pytest.mark.asyncio
async def test_root_navigation_and_dirty_review(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, _entry, _store, _hass = setup_flow()
    clean = await flow.async_step_init()
    assert clean["menu_options"] == [
        "ha_players",
        "sensors",
        "automatic_cleanup",
        "server_history_check",
    ]
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    dirty = await flow.async_step_init()
    assert dirty["menu_options"] == [
        "ha_players",
        "sensors",
        "automatic_cleanup",
        "server_history_check",
        "review_changes",
    ]


@pytest.mark.asyncio
async def test_player_page_contains_only_global_switches_and_group(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, _entry, _store, _hass = setup_flow()
    result = await flow.async_step_ha_players()
    assert schema_keys(result) == {
        CONF_ONLY_DURING_PLAYBACK,
        CONF_AUTO_SHOW_NEW_PLAYERS,
        CONF_TECHNICAL_ACCESS_VISIBILITY,
    }


@pytest.mark.asyncio
async def test_player_page_submit_changes_only_draft(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, entry, store, hass = setup_flow()
    original = dict(entry.options)
    result = await flow.async_step_ha_players(
        {
            CONF_ONLY_DURING_PLAYBACK: True,
            CONF_AUTO_SHOW_NEW_PLAYERS: False,
            CONF_TECHNICAL_ACCESS_VISIBILITY: True,
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
async def test_automatic_cleanup_submit_is_draft_only_and_returns_root(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, entry, store, hass = setup_flow()
    original = dict(entry.options)
    result = await flow.async_step_automatic_cleanup(
        {
            CONF_SERVER_AUTO_CLEANUP_ENABLED: True,
            "automatic_age_preset": "preset_180",
            CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES: True,
        }
    )
    assert result["type"] == "menu"
    assert flow._draft_options[CONF_SERVER_AUTO_CLEANUP_ENABLED] is True
    assert flow._draft_options[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS] == 180
    assert flow._draft_options[CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES] is True
    assert entry.options == original
    assert hass.config_entries.updates == []
    assert store.saved == []


@pytest.mark.asyncio
async def test_automatic_cleanup_shows_last_and_next_run(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, _entry, _store, _hass = setup_flow()
    flow._runtime.maintenance_state.report = CleanupRunReport(
        mode="automatic",
        completed_at="2026-07-17T18:00:00+00:00",
        age_threshold_days=180,
        server_deleted=4,
        server_failed=1,
        skipped_active=2,
        next_run_at="2026-07-18T18:00:00+00:00",
    )
    result = await flow.async_step_automatic_cleanup()
    placeholders = result["description_placeholders"]
    assert placeholders["run_at"] == "17.07.2026 20:00"
    assert placeholders["mode"] == "Automatisch"
    assert placeholders["age"] == "180 Tage"
    assert placeholders["deleted"] == "4"
    assert placeholders["failed"] == "1"
    assert placeholders["next_run"] == "18.07.2026 20:00"
    assert CONF_FLOW_ACTION not in schema_keys(result)


@pytest.mark.asyncio
async def test_manual_cleanup_is_all_safe_without_age_or_scope(monkeypatch) -> None:
    old = device("old", name="Old", activity="2024-01-01T00:00:00Z")
    new = device("new", name="New", activity="2026-07-18T00:00:00Z")
    flow, entry, _store, _hass = setup_flow(devices=[new, old])
    monkeypatch.setattr(
        "custom_components.emby.options_cleanup.active_player_keys", lambda *_: set()
    )
    automatic_age = entry.options[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS]
    result = await flow.async_step_server_history_check()
    keys = schema_keys(result)
    assert CONF_DELETE_DEVICE_RECORD_IDS in keys
    assert CONF_FLOW_ACTION in keys
    assert "manual_cleanup_scope" not in keys
    assert "manual_age_preset" not in keys
    assert flow._draft_options[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS] == automatic_age
    select = next(
        validator
        for marker, validator in result["data_schema"].schema.items()
        if str(getattr(marker, "schema", marker)) == CONF_DELETE_DEVICE_RECORD_IDS
    )
    labels = [item["label"] for item in select.config.options]
    assert labels[0].startswith("Old")
    assert labels[1].startswith("New")


@pytest.mark.asyncio
async def test_manual_cleanup_execute_removes_exact_ha_match_after_server_delete(
    monkeypatch,
) -> None:
    flow, entry, _store, _hass = setup_flow()
    flow._pending_cleanup_records = {"history-1": device()}
    flow._pending_cleanup_age_days = entry.options[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS]
    flow._pending_cleanup_ignore_age = True
    captured = {}

    async def run(*_args, **kwargs):
        captured.update(kwargs)
        return CleanupRunReport(server_deleted=1), False

    monkeypatch.setattr("custom_components.emby.options_cleanup.async_run_manual_cleanup", run)
    result = await flow.async_step_execute_server_deletion()
    assert result["type"] == "abort"
    assert captured["ignore_age"] is True
    assert captured["remove_ha_entities"] is True
    assert entry.options[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS] == 365


@pytest.mark.asyncio
async def test_apply_closes_immediately_and_schedules_finalize(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, _entry, store, hass = setup_flow()
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    scheduled = []
    hass.async_create_task = lambda coro, name: scheduled.append((coro, name))
    result = await flow.async_step_apply_changes()
    assert result["type"] == "abort"
    assert result["reason"] == "apply_complete"
    assert len(hass.config_entries.updates) == 1
    assert hass.config_entries.reloads == []
    assert len(scheduled) == 1
    assert flow._runtime.suppress_update_listener is True
    scheduled[0][0].close()
    assert store.saved == []


@pytest.mark.asyncio
async def test_discard_and_close_have_no_side_effects(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, entry, store, hass = setup_flow()
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    result = await flow.async_step_discard_changes()
    assert result["type"] == "menu"
    assert flow._draft_options == entry.options
    assert hass.config_entries.updates == []
    assert hass.config_entries.reloads == []
    assert store.saved == []
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    del flow
    assert entry.options[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_PERSISTENT
    assert hass.config_entries.updates == []


@pytest.mark.asyncio
async def test_update_listener_reloads_once() -> None:
    _flow, entry, _store, hass = setup_flow()
    await async_update_listener(hass, entry)
    assert hass.config_entries.reloads == [entry.entry_id]
