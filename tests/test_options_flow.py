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
        self.config = SimpleNamespace(language="de", time_zone="Europe/Berlin")
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


def setup_flow(options: dict | None = None):
    store = FakeStore()
    runtime = EmbiRuntimeData(
        api_client=FakeApi([device()]),
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


@pytest.mark.asyncio
async def test_root_navigation_and_dirty_review(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, _entry, _store, _hass = setup_flow()
    clean = await flow.async_step_init()
    assert clean["menu_options"] == ["ha_players", "server_cleanup"]
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    dirty = await flow.async_step_init()
    assert dirty["menu_options"] == ["ha_players", "server_cleanup", "review_changes"]


@pytest.mark.asyncio
async def test_player_page_changes_only_draft(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, entry, store, hass = setup_flow()
    original = dict(entry.options)
    result = await flow.async_step_ha_players(
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
async def test_back_preserves_draft(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, entry, store, hass = setup_flow()
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    result = await flow.async_step_back_to_init()
    assert result["type"] == "menu"
    assert flow._draft_options[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_ACTIVE_ONLY
    assert entry.options[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_PERSISTENT
    assert hass.config_entries.updates == []
    assert hass.config_entries.reloads == []
    assert store.saved == []


@pytest.mark.asyncio
async def test_apply_writes_and_reloads_once(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, entry, store, hass = setup_flow()
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    result = await flow.async_step_apply_changes()
    assert result["type"] == "abort"
    assert result["reason"] == "apply_complete"
    assert len(hass.config_entries.updates) == 1
    assert hass.config_entries.reloads == [entry.entry_id]
    assert store.saved == []


@pytest.mark.asyncio
async def test_unchanged_apply_stays_inline(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, _entry, store, hass = setup_flow()
    result = await flow.async_step_apply_changes()
    assert result["type"] == "form"
    assert result["step_id"] == "review_changes"
    assert "keine ungespeicherten Änderungen" in result["description_placeholders"]["error"]
    assert hass.config_entries.updates == []
    assert hass.config_entries.reloads == []
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
    assert hass.config_entries.reloads == []


@pytest.mark.asyncio
async def test_auto_cleanup_change_resets_deadline_on_apply(monkeypatch) -> None:
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
async def test_cleanup_values_survive_unrelated_apply(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    options = default_options_090()
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
async def test_dirty_draft_blocks_player_action_inline(monkeypatch) -> None:
    patch_catalog(monkeypatch)
    flow, _entry, _store, _hass = setup_flow()
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    result = await flow.async_step_manage_ha_players()
    assert result["type"] == "form"
    assert result["errors"] == {"base": "unsaved_changes"}
    assert flow._draft_options[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_ACTIVE_ONLY


@pytest.mark.asyncio
async def test_update_listener_reloads_once() -> None:
    _flow, entry, _store, hass = setup_flow()
    await async_update_listener(hass, entry)
    assert hass.config_entries.reloads == [entry.entry_id]


def _realistic_player_fixture():
    from custom_components.emby.player_context import build_player_catalog, catalog_stats

    records: list[EmbyDeviceRecord] = []
    registry_entries = []
    apps = ["Emby TV", "Emby for iOS", "Emby Web", "Emby for Android"]
    for index in range(69):
        player_index = index % 31
        app = apps[player_index % len(apps)]
        data = {
            "Id": f"history-{index:02d}",
            "ReportedDeviceId": f"device-{player_index:02d}",
            "Name": f"Room {player_index:02d}",
            "AppName": app,
            "LastUserName": f"User {player_index % 8}",
            "DateLastActivity": f"2026-07-{(index % 15) + 1:02d}T12:00:00Z",
            "SupportsPlayback": True,
        }
        records.append(EmbyDeviceRecord.from_api(data))
    for player_index in range(31):
        app = apps[player_index % len(apps)]
        key = f"device-{player_index:02d}.{app}"
        registry_entries.append(
            SimpleNamespace(
                domain="media_player",
                platform="emby",
                config_entry_id="entry",
                unique_id=key,
                entity_id=f"media_player.emby_{player_index:02d}",
                name=f"HA Player {player_index:02d}",
                original_name=f"Emby {player_index:02d}",
                disabled_by=None,
                hidden_by=None,
            )
        )

    class FixtureStates:
        def get(self, entity_id):
            return SimpleNamespace(state="idle") if entity_id else None

    players = build_player_catalog(
        records,
        registry_entries=registry_entries,
        states=FixtureStates(),
        entry_id="entry",
        options=default_options_090(),
    )
    return records, players, catalog_stats(players, server_history_records=len(records))


def _assert_form_serializable(result) -> None:
    import json

    assert result["type"] == "form"
    serialized = []
    for validator in result["data_schema"].schema.values():
        serializer = getattr(validator, "serialize", None)
        if serializer is not None:
            serialized.append(serializer())
    json.dumps(serialized)


@pytest.mark.asyncio
async def test_realistic_root_player_form_is_frontend_serializable(monkeypatch) -> None:
    records, players, fixture_stats = _realistic_player_fixture()

    async def catalog(_flow):
        return players, fixture_stats

    monkeypatch.setattr("custom_components.emby.options_flow.fresh_catalog", catalog)
    monkeypatch.setattr("custom_components.emby.options_devices.fresh_catalog", catalog)
    monkeypatch.setattr("custom_components.emby.options_ha_cleanup.fresh_catalog", catalog)
    flow, _entry, _store, _hass = setup_flow()
    flow._runtime.api_client = FakeApi(records)

    result = await flow.async_step_ha_players()
    assert result["step_id"] == "ha_players"
    assert result["errors"] == {}
    _assert_form_serializable(result)


@pytest.mark.asyncio
async def test_reachable_forms_serialize_and_never_expose_legacy_back_toggle(monkeypatch) -> None:
    from custom_components.emby.const import CONF_BACK
    from custom_components.emby.player_context import group_player_catalog

    records, players, fixture_stats = _realistic_player_fixture()

    async def catalog(_flow):
        return players, fixture_stats

    monkeypatch.setattr("custom_components.emby.options_flow.fresh_catalog", catalog)
    monkeypatch.setattr("custom_components.emby.options_devices.fresh_catalog", catalog)
    monkeypatch.setattr("custom_components.emby.options_ha_cleanup.fresh_catalog", catalog)
    flow, _entry, _store, _hass = setup_flow()
    flow._runtime.api_client = FakeApi(records)
    flow._selected_group = next(iter(group_player_catalog(players)))

    results = [
        await flow.async_step_ha_players(),
        await flow.async_step_player_group(),
        await flow.async_step_player_exceptions(),
        await flow.async_step_player_details(),
        await flow.async_step_server_cleanup(),
        await flow.async_step_automatic_cleanup(),
        await flow.async_step_server_history_check(),
        await flow.async_step_last_cleanup_run(),
        await flow.async_step_manage_ha_players(),
        await flow.async_step_restore_ha_players(),
        await flow.async_step_review_changes(),
    ]
    for result in results:
        _assert_form_serializable(result)
        keys = {str(getattr(marker, "schema", marker)) for marker in result["data_schema"].schema}
        assert CONF_BACK not in keys


@pytest.mark.asyncio
async def test_form_back_action_preserves_complete_draft(monkeypatch) -> None:
    from custom_components.emby.const import CONF_FLOW_ACTION, FLOW_ACTION_BACK

    patch_catalog(monkeypatch)
    flow, entry, store, hass = setup_flow()
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    result = await flow.async_step_ha_players({CONF_FLOW_ACTION: FLOW_ACTION_BACK})

    assert result["type"] == "menu"
    assert flow._draft_options[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_ACTIVE_ONLY
    assert entry.options[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_PERSISTENT
    assert hass.config_entries.updates == []
    assert hass.config_entries.reloads == []
    assert store.saved == []


@pytest.mark.asyncio
async def test_last_cleanup_run_uses_local_readable_values(monkeypatch) -> None:
    from custom_components.emby.models import CleanupRunReport

    patch_catalog(monkeypatch)
    flow, _entry, _store, _hass = setup_flow()
    flow._runtime.maintenance_state.report = CleanupRunReport(
        mode="manual",
        completed_at="2026-07-17T18:00:00+00:00",
        age_threshold_days=180,
        server_deleted=4,
        server_failed=1,
        skipped_active=2,
        next_run_at=None,
    )
    result = await flow.async_step_last_cleanup_run()
    placeholders = result["description_placeholders"]
    assert placeholders["run_at"] == "17.07.2026 20:00"
    assert placeholders["mode"] == "Manuell"
    assert placeholders["age"] == "180 Tage"
    assert placeholders["next_run"] == "Kein Lauf geplant"
    _assert_form_serializable(result)
