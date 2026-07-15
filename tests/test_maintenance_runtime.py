from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from homeassistant.config_entries import ConfigEntryState

from custom_components.emby.api import EmbyApiError, EmbyDeviceRecord
from custom_components.emby.const import (
    RUN_MODE_AUTOMATIC,
    RUN_STATUS_COMPLETED,
    RUN_STATUS_FAILED,
    RUN_STATUS_INTERRUPTED,
    RUN_STATUS_REGISTRY_PENDING,
)
from custom_components.emby.maintenance_cycle_execute import _async_execute_cleanup
from custom_components.emby.maintenance_registry_apply import async_apply_pending_registry_cleanup
from custom_components.emby.models import CleanupRunReport, EmbiRuntimeData, MaintenanceState


class FakeRegistry:
    def __init__(self) -> None:
        self.entities = {}
        self.removed: list[str] = []

    def async_get(self, entity_id: str):
        return self.entities.get(entity_id)

    def async_remove(self, entity_id: str) -> None:
        self.entities.pop(entity_id, None)
        self.removed.append(entity_id)


class FakeStates:
    def get(self, entity_id: str):
        return None


class FakeHass:
    def __init__(self) -> None:
        self.data = {}
        self.registry = FakeRegistry()
        self.states = FakeStates()
        self.notifications: list[tuple] = []


class FakeStore:
    def __init__(self, *, fail_on_saves: set[int] | None = None) -> None:
        self.fail_on_saves = fail_on_saves or set()
        self.save_calls = 0
        self.saved: list[dict] = []

    async def async_save(self, state: MaintenanceState) -> None:
        self.save_calls += 1
        if self.save_calls in self.fail_on_saves:
            raise OSError("store write failed")
        self.saved.append(state.as_dict())


class FakeApi:
    def __init__(self, devices: list[EmbyDeviceRecord], failing_deletes=()) -> None:
        self.devices = list(devices)
        self.failing_deletes = set(failing_deletes)
        self.delete_calls: list[str] = []
        self.get_calls = 0

    async def async_get_devices(self) -> list[EmbyDeviceRecord]:
        self.get_calls += 1
        return list(self.devices)

    async def async_delete_device(self, record_id: str) -> None:
        self.delete_calls.append(record_id)
        if record_id in self.failing_deletes:
            raise EmbyApiError("delete failed")
        self.devices = [item for item in self.devices if item.record_id != record_id]


@dataclass
class FakeEntry:
    runtime_data: EmbiRuntimeData
    options: dict
    entry_id: str = "entry-target"
    state: ConfigEntryState = ConfigEntryState.LOADED


def record(index: int, *, old: bool) -> EmbyDeviceRecord:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    activity = now - timedelta(days=500 if old else 10)
    return EmbyDeviceRecord.from_api(
        {
            "Id": f"history-{index}",
            "ReportedDeviceId": f"client-{index}",
            "Name": f"Device {index}",
            "AppName": "App",
            "DateLastActivity": activity.isoformat(),
        }
    )


def setup_runtime(devices, *, fail_on_saves=None, failing_deletes=()):
    hass = FakeHass()
    store = FakeStore(fail_on_saves=fail_on_saves)
    api = FakeApi(list(devices), failing_deletes=failing_deletes)
    runtime = EmbiRuntimeData(
        api_client=api,
        devices=list(devices),
        cleanup_lock=asyncio.Lock(),
        maintenance_store=store,
        maintenance_state=MaintenanceState(),
    )
    entry = FakeEntry(runtime, options={})
    return hass, entry, api, store


@pytest.mark.asyncio
async def test_complete_74_to_69_cleanup_and_registry_missing_contract(monkeypatch) -> None:
    old = [record(index, old=True) for index in range(5)]
    recent = [record(index + 5, old=False) for index in range(69)]
    hass, entry, api, _store = setup_runtime([*old, *recent])
    monkeypatch.setattr(
        "custom_components.emby.maintenance_cycle_execute.dt_util.utcnow",
        lambda: datetime(2026, 7, 14, 12, 0, tzinfo=UTC),
    )
    report, reload_needed = await _async_execute_cleanup(
        hass,
        entry,
        mode=RUN_MODE_AUTOMATIC,
        age_days=364,
        remove_ha_entities=True,
    )
    assert reload_needed is True
    assert report.status == RUN_STATUS_REGISTRY_PENDING
    assert report.server_candidates == 5
    assert report.server_deleted == 5
    assert report.server_failed == 0
    assert len(api.devices) == 69
    assert report.registry_keys_queued == 5

    result = await async_apply_pending_registry_cleanup(hass, entry, api.devices)
    assert result.queued == 5
    assert result.matched == 0
    assert result.removed == 0
    assert result.missing == 5
    assert report.status == RUN_STATUS_COMPLETED


@pytest.mark.asyncio
async def test_store_failure_before_delete_blocks_all_destructive_calls(monkeypatch) -> None:
    devices = [record(1, old=True)]
    hass, entry, api, _store = setup_runtime(devices, fail_on_saves={2})
    monkeypatch.setattr(
        "custom_components.emby.maintenance_cycle_execute.dt_util.utcnow",
        lambda: datetime(2026, 7, 14, 12, 0, tzinfo=UTC),
    )
    report, reload_needed = await _async_execute_cleanup(
        hass,
        entry,
        mode=RUN_MODE_AUTOMATIC,
        age_days=365,
        remove_ha_entities=True,
    )
    assert reload_needed is False
    assert report.status == RUN_STATUS_FAILED
    assert report.last_error == "storage_unavailable_before_delete"
    assert api.delete_calls == []


@pytest.mark.asyncio
async def test_store_failure_after_server_delete_reports_counts_and_skips_registry(
    monkeypatch,
) -> None:
    devices = [record(1, old=True), record(2, old=True)]
    hass, entry, api, _store = setup_runtime(devices, fail_on_saves={3})
    monkeypatch.setattr(
        "custom_components.emby.maintenance_cycle_execute.dt_util.utcnow",
        lambda: datetime(2026, 7, 14, 12, 0, tzinfo=UTC),
    )
    report, reload_needed = await _async_execute_cleanup(
        hass,
        entry,
        mode=RUN_MODE_AUTOMATIC,
        age_days=365,
        remove_ha_entities=True,
    )
    assert reload_needed is False
    assert report.status == RUN_STATUS_INTERRUPTED
    assert report.last_error == "storage_failed_after_server_delete"
    assert report.server_deleted == 2
    assert report.result_counts_complete is False
    assert len(api.delete_calls) == 2
    assert not hass.data.get("emby_pending_registry_cleanup")


@pytest.mark.asyncio
async def test_individual_delete_failure_does_not_stop_remaining_candidates(monkeypatch) -> None:
    devices = [record(index, old=True) for index in range(3)]
    hass, entry, api, _store = setup_runtime(devices, failing_deletes={"history-1"})
    monkeypatch.setattr(
        "custom_components.emby.maintenance_cycle_execute.dt_util.utcnow",
        lambda: datetime(2026, 7, 14, 12, 0, tzinfo=UTC),
    )
    report, _ = await _async_execute_cleanup(
        hass,
        entry,
        mode=RUN_MODE_AUTOMATIC,
        age_days=365,
        remove_ha_entities=False,
    )
    assert api.delete_calls == ["history-0", "history-1", "history-2"]
    assert report.server_deleted == 2
    assert report.server_failed == 1


@pytest.mark.asyncio
async def test_shared_lock_blocks_parallel_manual_or_automatic_series() -> None:
    hass, entry, api, _store = setup_runtime([record(1, old=True)])
    await entry.runtime_data.cleanup_lock.acquire()
    try:
        report, reload_needed = await _async_execute_cleanup(
            hass,
            entry,
            mode=RUN_MODE_AUTOMATIC,
            age_days=365,
            remove_ha_entities=False,
        )
    finally:
        entry.runtime_data.cleanup_lock.release()
    assert reload_needed is False
    assert report.status == "idle"
    assert api.get_calls == 0
    assert api.delete_calls == []


@pytest.mark.asyncio
async def test_restart_with_registry_pending_never_resumes_unsafe_remove() -> None:
    hass, entry, _api, store = setup_runtime([])
    entry.runtime_data.maintenance_state.report = CleanupRunReport(
        status=RUN_STATUS_REGISTRY_PENDING,
        mode=RUN_MODE_AUTOMATIC,
        registry_keys_queued=5,
        follow_up_status="pending",
    )
    result = await async_apply_pending_registry_cleanup(hass, entry, [])
    report = entry.runtime_data.maintenance_state.report
    assert result.removed == 0
    assert hass.registry.removed == []
    assert report.status == RUN_STATUS_INTERRUPTED
    assert report.last_error == "registry_followup_interrupted"
    assert store.save_calls == 1
