from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from homeassistant.config_entries import ConfigEntryState

from custom_components.emby.const import (
    CONF_MAINTENANCE_STORE_INITIALIZED,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_CLEANUP_ENABLED,
)
from custom_components.emby.maintenance_scheduler import (
    async_schedule_automatic_cleanup,
)
from custom_components.emby.models import EmbiRuntimeData, MaintenanceState
from custom_components.emby.scheduling import utc_iso


class FakeStore:
    def __init__(self, state: MaintenanceState) -> None:
        self.state = state
        self.saves = 0

    async def async_load(self):
        return self.state

    async def async_save(self, state):
        self.state = state
        self.saves += 1


class FakeHass:
    def __init__(self) -> None:
        self.data = {}
        self.notifications = []
        self.config_entries = SimpleNamespace(async_reload=self.async_reload)
        self.reloads = 0

    async def async_reload(self, entry_id):
        self.reloads += 1


class FakeEntry:
    def __init__(self, runtime, *, state=ConfigEntryState.LOADED):
        self.entry_id = "entry"
        self.runtime_data = runtime
        self.state = state
        self.options = {
            CONF_SERVER_CLEANUP_ENABLED: True,
            CONF_SERVER_AUTO_CLEANUP_ENABLED: True,
            CONF_MAINTENANCE_STORE_INITIALIZED: True,
        }


def setup(*, state=ConfigEntryState.LOADED, maintenance_state=None):
    persisted = maintenance_state or MaintenanceState()
    store = FakeStore(persisted)
    runtime = EmbiRuntimeData(
        api_client=object(),
        cleanup_lock=asyncio.Lock(),
        maintenance_store=store,
        maintenance_state=persisted,
    )
    return FakeHass(), FakeEntry(runtime, state=state), store


@pytest.mark.asyncio
async def test_rc3_migration_schedules_once_after_120_seconds_and_persists(
    monkeypatch,
) -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    state = MaintenanceState(initial_run_completed=True)
    hass, entry, store = setup(
        state=ConfigEntryState.SETUP_IN_PROGRESS,
        maintenance_state=state,
    )
    scheduled = []

    def track(_hass, callback, point):
        scheduled.append((callback, point))
        return lambda: None

    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.dt_util.utcnow", lambda: now
    )
    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.async_track_point_in_utc_time",
        track,
    )
    await async_schedule_automatic_cleanup(hass, entry)
    assert len(scheduled) == 1
    assert scheduled[0][1] == now + timedelta(seconds=120)
    assert entry.runtime_data.maintenance_state.report.next_run_at == utc_iso(
        scheduled[0][1]
    )
    assert entry.runtime_data.auto_cleanup_scheduled is True
    assert store.saves == 1


@pytest.mark.asyncio
async def test_setup_registration_waits_for_loaded_then_executes_once(
    monkeypatch,
) -> None:
    clock = [datetime(2026, 7, 14, 12, 0, tzinfo=UTC)]
    hass, entry, _store = setup(state=ConfigEntryState.SETUP_IN_PROGRESS)
    callbacks = []
    points = []
    runs = 0

    def track(_hass, callback, point):
        callbacks.append(callback)
        points.append(point)
        return lambda: None

    async def run(_hass, _entry):
        nonlocal runs
        runs += 1
        return False

    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.dt_util.utcnow", lambda: clock[0]
    )
    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.async_track_point_in_utc_time",
        track,
    )
    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.async_run_automatic_cleanup", run
    )

    await async_schedule_automatic_cleanup(hass, entry)
    assert len(callbacks) == 1
    assert runs == 0

    clock[0] = points[0]
    await callbacks[0](clock[0])
    assert runs == 0
    assert len(callbacks) == 2

    entry.state = ConfigEntryState.LOADED
    clock[0] = points[1]
    await callbacks[1](clock[0])
    assert runs == 1


@pytest.mark.asyncio
async def test_deactivation_during_grace_prevents_run(monkeypatch) -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    hass, entry, _store = setup()
    scheduled = []
    runs = 0

    def track(_hass, callback, point):
        scheduled.append(callback)
        return lambda: None

    async def run(_hass, _entry):
        nonlocal runs
        runs += 1
        return False

    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.dt_util.utcnow", lambda: now
    )
    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.async_track_point_in_utc_time",
        track,
    )
    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.async_run_automatic_cleanup", run
    )
    await async_schedule_automatic_cleanup(hass, entry)
    entry.options[CONF_SERVER_AUTO_CLEANUP_ENABLED] = False
    await scheduled[0](now + timedelta(seconds=120))
    assert runs == 0


@pytest.mark.asyncio
async def test_reload_preserves_future_absolute_deadline_and_cancels_duplicate(
    monkeypatch,
) -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    future = now + timedelta(hours=8)
    hass, entry, store = setup()
    entry.runtime_data.maintenance_state.report.next_run_at = utc_iso(future)
    scheduled = []
    cancelled = 0

    def track(_hass, callback, point):
        scheduled.append(point)

        def cancel():
            nonlocal cancelled
            cancelled += 1

        return cancel

    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.dt_util.utcnow", lambda: now
    )
    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.async_track_point_in_utc_time",
        track,
    )
    await async_schedule_automatic_cleanup(hass, entry)
    await async_schedule_automatic_cleanup(hass, entry)
    assert scheduled == [future, future]
    assert cancelled == 1
    assert store.saves == 0


@pytest.mark.asyncio
async def test_restart_preserves_future_deadline_and_stale_callback_cannot_run(
    monkeypatch,
) -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    future = now + timedelta(hours=8)
    state = MaintenanceState()
    state.report.next_run_at = utc_iso(future)
    hass, entry, store = setup(maintenance_state=state)
    callbacks = []
    points = []
    runs = 0

    def track(_hass, callback, point):
        callbacks.append(callback)
        points.append(point)
        return lambda: None

    async def run(_hass, _entry):
        nonlocal runs
        runs += 1
        return False

    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.dt_util.utcnow", lambda: now
    )
    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.async_track_point_in_utc_time",
        track,
    )
    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.async_run_automatic_cleanup", run
    )

    await async_schedule_automatic_cleanup(hass, entry)
    old_runtime = entry.runtime_data
    replacement = EmbiRuntimeData(
        api_client=object(),
        cleanup_lock=asyncio.Lock(),
        maintenance_store=store,
        maintenance_state=state,
    )
    entry.runtime_data = replacement
    await async_schedule_automatic_cleanup(hass, entry)

    assert points == [future, future]
    assert store.saves == 0
    await callbacks[0](future)
    assert runs == 0
    assert old_runtime.auto_cleanup_scheduled is False


@pytest.mark.asyncio
async def test_locked_callback_reschedules_without_starting_second_series(
    monkeypatch,
) -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    hass, entry, _store = setup()
    callbacks = []
    points = []
    runs = 0

    def track(_hass, callback, point):
        callbacks.append(callback)
        points.append(point)
        return lambda: None

    async def run(_hass, _entry):
        nonlocal runs
        runs += 1
        return False

    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.dt_util.utcnow", lambda: now
    )
    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.async_track_point_in_utc_time",
        track,
    )
    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.async_run_automatic_cleanup", run
    )
    await async_schedule_automatic_cleanup(hass, entry)
    await entry.runtime_data.cleanup_lock.acquire()
    try:
        await callbacks[0](now + timedelta(seconds=120))
    finally:
        entry.runtime_data.cleanup_lock.release()
    assert runs == 0
    assert len(points) == 2
    assert points[1] == now + timedelta(seconds=120)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_mode", ["missing", "corrupted"])
async def test_missing_or_corrupted_store_prevents_registration(
    monkeypatch, failure_mode
) -> None:
    hass, entry, _store = setup()
    scheduled = []

    if failure_mode == "missing":
        entry.runtime_data.maintenance_store = None
    else:
        entry.runtime_data.maintenance_storage_available = False

    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.async_track_point_in_utc_time",
        lambda *_args: scheduled.append(True),
    )
    await async_schedule_automatic_cleanup(hass, entry)
    assert scheduled == []
    assert entry.runtime_data.auto_cleanup_scheduled is False


@pytest.mark.asyncio
async def test_unloading_runtime_neither_registers_nor_executes(monkeypatch) -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    hass, entry, _store = setup()
    callbacks = []
    runs = 0

    def track(_hass, callback, _point):
        callbacks.append(callback)
        return lambda: None

    async def run(_hass, _entry):
        nonlocal runs
        runs += 1
        return False

    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.dt_util.utcnow", lambda: now
    )
    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.async_track_point_in_utc_time",
        track,
    )
    monkeypatch.setattr(
        "custom_components.emby.maintenance_scheduler.async_run_automatic_cleanup", run
    )

    await async_schedule_automatic_cleanup(hass, entry)
    entry.runtime_data.unloading = True
    await callbacks[0](now + timedelta(seconds=120))
    assert runs == 0
    assert entry.runtime_data.auto_cleanup_scheduled is False

    await async_schedule_automatic_cleanup(hass, entry)
    assert len(callbacks) == 1
