from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.const import (
    AGE_PRESET_365,
    CLIENT_MODE_ALL,
    CLIENT_MODE_ALLOWLIST,
    CONF_AGE_PRESET,
    CONF_ALLOWED_DEVICE_IDS,
    CONF_CLIENT_MODE,
    CONF_CONFIRM_APPLY,
    CONF_CONFIRM_AUTO_CLEANUP,
    CONF_CONFIRM_DISCARD,
    CONF_IGNORED_PLAYER_KEYS,
    CONF_IGNORED_REPORTED_DEVICE_IDS,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_AGE_DAYS,
    CONF_SERVER_CLEANUP_ENABLED,
    CONF_UNRESOLVED_IGNORED_IDS,
)
from custom_components.emby.entry_lifecycle import async_update_listener
from custom_components.emby.models import EmbiRuntimeData, MaintenanceState
from custom_components.emby.options_flow import EmbyOptionsFlow


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


class FakeHass:
    def __init__(self) -> None:
        self.config = SimpleNamespace(language="de")
        self.reloads: list[str] = []
        self.config_entries = SimpleNamespace(async_reload=self.async_reload)

    async def async_reload(self, entry_id: str) -> None:
        self.reloads.append(entry_id)


@dataclass
class FakeEntry:
    options: dict
    runtime_data: EmbiRuntimeData
    entry_id: str = "entry"


def device() -> EmbyDeviceRecord:
    return EmbyDeviceRecord.from_api(
        {
            "Id": "history-1",
            "ReportedDeviceId": "client.with.dot",
            "Name": "Living room",
            "AppName": "Emby App",
        }
    )


def default_options() -> dict:
    return {
        CONF_CLIENT_MODE: CLIENT_MODE_ALL,
        CONF_ALLOWED_DEVICE_IDS: [],
        CONF_IGNORED_PLAYER_KEYS: [],
        CONF_IGNORED_REPORTED_DEVICE_IDS: [],
        CONF_UNRESOLVED_IGNORED_IDS: [],
        CONF_SERVER_CLEANUP_ENABLED: True,
        CONF_SERVER_CLEANUP_AGE_DAYS: 365,
        CONF_SERVER_AUTO_CLEANUP_ENABLED: False,
        CONF_SERVER_AUTO_CLEANUP_AGE_DAYS: 365,
        CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES: False,
    }


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
    flow = EmbyOptionsFlow(entry)
    flow.hass = hass
    return flow, entry, store, hass


@pytest.mark.asyncio
async def test_multiple_subpages_change_only_draft_and_return_to_main_menu() -> None:
    flow, entry, store, hass = setup_flow()
    original = dict(entry.options)
    player_key = device().player_key

    result = await flow.async_step_clients(
        {
            CONF_CLIENT_MODE: CLIENT_MODE_ALLOWLIST,
            CONF_ALLOWED_DEVICE_IDS: [player_key],
            CONF_IGNORED_PLAYER_KEYS: [],
            CONF_IGNORED_REPORTED_DEVICE_IDS: [],
            CONF_UNRESOLVED_IGNORED_IDS: [],
        }
    )

    assert result["type"] == "menu"
    assert flow._draft_options[CONF_CLIENT_MODE] == CLIENT_MODE_ALLOWLIST
    assert flow._draft_options[CONF_ALLOWED_DEVICE_IDS] == [player_key]
    assert entry.options == original
    assert store.saved == []
    assert hass.reloads == []
    assert "Ungespeicherte Änderungen" in result["description_placeholders"]["draft_summary"]
    assert "ha_cleanup" not in result["menu_options"]
    assert "server_cleanup" not in result["menu_options"]


@pytest.mark.asyncio
async def test_apply_writes_complete_draft_once_and_flow_does_not_reload_directly() -> None:
    flow, entry, store, hass = setup_flow()
    flow._draft_options[CONF_CLIENT_MODE] = CLIENT_MODE_ALLOWLIST
    flow._draft_options[CONF_ALLOWED_DEVICE_IDS] = [device().player_key]
    calls: list[dict] = []

    def create_entry(**kwargs):
        calls.append(kwargs)
        return {"type": "create_entry", **kwargs}

    flow.async_create_entry = create_entry
    result = await flow.async_step_apply({CONF_CONFIRM_APPLY: True})

    assert result["type"] == "create_entry"
    assert len(calls) == 1
    assert calls[0]["data"][CONF_CLIENT_MODE] == CLIENT_MODE_ALLOWLIST
    assert entry.options[CONF_CLIENT_MODE] == CLIENT_MODE_ALL
    assert store.saved == []
    assert hass.reloads == []


@pytest.mark.asyncio
async def test_unchanged_apply_aborts_without_store_write_or_reload() -> None:
    flow, _entry, store, hass = setup_flow()
    result = await flow.async_step_apply({CONF_CONFIRM_APPLY: True})
    assert result == {"type": "abort", "reason": "no_changes"}
    assert store.saved == []
    assert hass.reloads == []


@pytest.mark.asyncio
async def test_discard_restores_original_without_write_or_reload() -> None:
    flow, entry, store, hass = setup_flow()
    flow._draft_options[CONF_CLIENT_MODE] = CLIENT_MODE_ALLOWLIST
    result = await flow.async_step_discard({CONF_CONFIRM_DISCARD: True})

    assert result["type"] == "menu"
    assert flow._draft_options == entry.options
    assert flow._dirty is False
    assert store.saved == []
    assert hass.reloads == []


@pytest.mark.asyncio
async def test_closing_flow_with_dirty_draft_has_no_side_effects() -> None:
    flow, entry, store, hass = setup_flow()
    flow._draft_options[CONF_CLIENT_MODE] = CLIENT_MODE_ALLOWLIST
    assert flow._dirty is True
    del flow
    assert entry.options[CONF_CLIENT_MODE] == CLIENT_MODE_ALL
    assert store.saved == []
    assert hass.reloads == []


@pytest.mark.asyncio
async def test_automatic_cleanup_requires_warning_switch_and_stays_draft_until_apply() -> None:
    flow, entry, store, hass = setup_flow()
    result = await flow.async_step_server_auto_cleanup_settings(
        {
            CONF_AGE_PRESET: AGE_PRESET_365,
            CONF_SERVER_AUTO_CLEANUP_ENABLED: True,
            CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES: False,
        }
    )
    assert result["type"] == "form"
    assert result["step_id"] == "server_auto_cleanup_confirm"
    assert (
        CONF_SERVER_AUTO_CLEANUP_ENABLED not in entry.options
        or not entry.options[CONF_SERVER_AUTO_CLEANUP_ENABLED]
    )
    assert store.saved == []

    rejected = await flow.async_step_server_auto_cleanup_confirm({CONF_CONFIRM_AUTO_CLEANUP: False})
    assert rejected["errors"] == {"base": "confirmation_required"}
    assert flow._draft_options[CONF_SERVER_AUTO_CLEANUP_ENABLED] is False

    accepted = await flow.async_step_server_auto_cleanup_confirm({CONF_CONFIRM_AUTO_CLEANUP: True})
    assert accepted["type"] == "menu"
    assert flow._draft_options[CONF_SERVER_AUTO_CLEANUP_ENABLED] is True
    assert entry.options[CONF_SERVER_AUTO_CLEANUP_ENABLED] is False
    assert store.saved == []
    assert hass.reloads == []


@pytest.mark.asyncio
async def test_auto_enable_apply_resets_persistent_deadline_before_options_commit() -> None:
    flow, _entry, store, _hass = setup_flow()
    flow._runtime.maintenance_state.initial_run_completed = True
    flow._runtime.maintenance_state.report.next_run_at = "2026-07-16T12:00:00+00:00"
    flow._draft_options[CONF_SERVER_AUTO_CLEANUP_ENABLED] = True

    result = await flow.async_step_apply({CONF_CONFIRM_APPLY: True})

    assert result["type"] == "create_entry"
    assert len(store.saved) == 1
    assert store.saved[0].initial_run_completed is False
    assert store.saved[0].report.next_run_at is None


@pytest.mark.asyncio
async def test_dirty_draft_blocks_both_destructive_entry_points() -> None:
    flow, _entry, _store, _hass = setup_flow()
    flow._draft_options[CONF_CLIENT_MODE] = CLIENT_MODE_ALLOWLIST
    assert await flow.async_step_ha_cleanup() == {
        "type": "abort",
        "reason": "unsaved_changes",
    }
    assert await flow.async_step_server_cleanup() == {
        "type": "abort",
        "reason": "unsaved_changes",
    }


@pytest.mark.asyncio
async def test_update_listener_performs_exactly_one_reload() -> None:
    _flow, entry, _store, hass = setup_flow()
    await async_update_listener(hass, entry)
    assert hass.reloads == [entry.entry_id]
