"""State transitions around external deletion; stale plans never grant permission."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from test_maintenance_runtime import record, setup_runtime

from custom_components.emby.api import EmbyApiError, EmbyAuthError
from custom_components.emby.entry_lifecycle import async_unload_entry
from custom_components.emby.maintenance_common import _async_save_state
from custom_components.emby.maintenance_cycle_execute import _async_execute_cleanup
from custom_components.emby.models import EmbiRuntimeData
from custom_components.emby.session_state import (
    INACTIVE,
    UNKNOWN,
    aggregate_activity,
    player_activity,
    validate_sessions,
)


def session(index=1, *, paused=False):
    return {
        "Id": f"s-{index}",
        "DeviceId": f"client-{index}",
        "Client": "App",
        "NowPlayingItem": {"Id": "film"},
        "PlayState": {"IsPaused": paused},
    }


async def run(hass, entry, *, mode="automatic"):
    return await _async_execute_cleanup(
        hass, entry, mode=mode, age_days=90, remove_ha_entities=True
    )


@pytest.mark.parametrize(
    "states", [("unavailable", "Playing"), ("Playing", "Idle"), ("idle", "paused")]
)
def test_active_observation_always_wins(states):
    assert aggregate_activity(states) in {"playing", "paused"}


@pytest.mark.parametrize("item", [{}, {"Id": "film"}])
def test_incomplete_playback_is_not_inactivity(item):
    data = session()
    data["NowPlayingItem"] = item
    data.pop("PlayState")
    assert player_activity([data], "client-1.App") == UNKNOWN


def test_multiple_sessions_and_similar_ids_use_exact_identity():
    idle = {"DeviceId": "client-1", "Client": "App"}
    active = session()
    assert player_activity([active, idle], "client-1.App") == "playing"
    assert player_activity([idle, active], "client-1.App") == "playing"
    assert player_activity([active], "client-10.App") == INACTIVE
    with pytest.raises(ValueError):
        validate_sessions([{"Client": "App"}])


@pytest.mark.asyncio
async def test_active_session_protects_even_without_ha_entity():
    hass, entry, api, _ = setup_runtime([record(1, old=True)])
    api.sessions = [session()]
    report, reload_needed = await run(hass, entry)
    assert api.delete_calls == []
    assert report.skipped_revalidation == 1
    assert not reload_needed


@pytest.mark.asyncio
async def test_playback_start_between_two_deletions_protects_second_player():
    hass, entry, api, _ = setup_runtime([record(1, old=True), record(2, old=True)])
    original = api.async_delete_device

    async def delete(record_id):
        await original(record_id)
        api.sessions = [session(2)]

    api.async_delete_device = delete
    report, _ = await run(hass, entry)
    assert api.delete_calls == ["history-1"]
    assert report.server_deleted == 1
    assert report.skipped_revalidation == 1


@pytest.mark.asyncio
async def test_recent_activity_after_planning_protects_record():
    hass, entry, api, _ = setup_runtime([record(1, old=True)])
    original = api.async_get_devices

    async def devices():
        result = await original()
        if api.get_calls > 1:
            from dataclasses import replace
            from datetime import UTC, datetime

            return [replace(result[0], last_activity_date=datetime.now(UTC).isoformat())]
        return result

    api.async_get_devices = devices
    report, _ = await run(hass, entry)
    assert not api.delete_calls
    assert report.skipped_revalidation == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error", [EmbyApiError("offline"), EmbyAuthError("auth"), ValueError("bad JSON")]
)
async def test_session_failure_stops_series_without_deletion(error):
    hass, entry, api, _ = setup_runtime([record(1, old=True)])
    api.async_get_sessions = AsyncMock(side_effect=error)
    report, reload_needed = await run(hass, entry)
    assert report.status == "failed"
    assert report.next_run_at is not None
    assert not api.delete_calls
    assert not reload_needed


@pytest.mark.asyncio
async def test_missing_expected_store_cannot_be_healed_by_an_ordinary_save():
    hass, entry, api, store = setup_runtime([record(1, old=True)])
    entry.runtime_data.maintenance_recovery_required = True
    entry.runtime_data.maintenance_storage_available = False
    assert not await _async_save_state(hass, entry)
    await run(hass, entry)
    assert store.save_calls == 0
    assert not api.delete_calls


@pytest.mark.asyncio
async def test_manual_run_keeps_automatic_deadline():
    hass, entry, _, _ = setup_runtime([])
    deadline = "2027-01-02T10:00:00+00:00"
    entry.runtime_data.maintenance_state.report.next_run_at = deadline
    report, _ = await run(hass, entry, mode="manual")
    assert report.next_run_at == deadline
    assert entry.runtime_data.maintenance_state.automatic_next_run_at == deadline


@pytest.mark.asyncio
async def test_successful_unload_cancels_maintenance_before_external_effect():
    hass, entry, api, _ = setup_runtime([record(1, old=True)])
    entered = asyncio.Event()

    async def sessions():
        entered.set()
        await asyncio.Event().wait()

    api.async_get_sessions = sessions
    hass.config_entries = SimpleNamespace(async_unload_platforms=AsyncMock(return_value=True))
    task = asyncio.create_task(run(hass, entry))
    await entered.wait()
    assert await async_unload_entry(hass, entry)
    assert task.cancelled()
    assert not api.delete_calls
    assert not entry.runtime_data.maintenance_tasks


@pytest.mark.asyncio
async def test_old_generation_never_writes_into_new_generation():
    hass, entry, api, store = setup_runtime([record(1, old=True)])
    old = entry.runtime_data

    async def sessions():
        entry.runtime_data = EmbiRuntimeData(api_client=api)
        return []

    api.async_get_sessions = sessions
    report, _ = await run(hass, entry)
    assert report.status == "interrupted"
    assert not api.delete_calls
    assert store.save_calls == 2
    assert entry.runtime_data.maintenance_state.report.status == "idle"
    assert not old.maintenance_tasks


@pytest.mark.asyncio
async def test_uncertain_delete_stops_remaining_batch_without_replay():
    from custom_components.emby.api import EmbyDeleteUncertain

    hass, entry, api, _ = setup_runtime([record(1, old=True), record(2, old=True)])
    api.async_delete_device = AsyncMock(side_effect=EmbyDeleteUncertain("uncertain"))
    report, _ = await run(hass, entry)
    api.async_delete_device.assert_awaited_once_with("history-1")
    assert not report.result_counts_complete
    assert report.last_error == "delete_result_uncertain"
    assert report.server_deleted == 0
