from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.emby.api import EmbyApiError, EmbyDeviceRecord
from custom_components.emby.cleanup import (
    async_delete_device_records,
    plan_device_cleanup,
    plan_registry_followup,
)


class FakeDeleteClient:
    def __init__(self, failing_ids: set[str] | None = None) -> None:
        self.failing_ids = failing_ids or set()
        self.calls: list[str] = []

    async def async_delete_device(self, record_id: str) -> None:
        self.calls.append(record_id)
        if record_id in self.failing_ids:
            raise EmbyApiError("delete denied")


def record(
    record_id: str,
    *,
    client_id: str | None = None,
    app_name: str = "Emby App",
    activity: datetime | None = None,
    raw_activity: str | None = None,
) -> EmbyDeviceRecord:
    return EmbyDeviceRecord.from_api(
        {
            "Id": record_id,
            "ReportedDeviceId": client_id or f"client-{record_id}",
            "Name": f"Device {record_id}",
            "AppName": app_name,
            "DateLastActivity": raw_activity
            if raw_activity is not None
            else activity.isoformat().replace("+00:00", "Z")
            if activity
            else None,
        }
    )


@pytest.mark.asyncio
async def test_batch_cleanup_continues_after_individual_failure_and_has_no_cap() -> None:
    records = [record(str(index)) for index in range(250)]
    client = FakeDeleteClient({"2"})
    result = await async_delete_device_records(client, records)
    assert len(client.calls) == 250
    assert [item.record_id for item in result.failed] == ["2"]
    assert len(result.succeeded) == 249


def test_age_contract_exact_cutoff_is_protected_and_older_is_candidate() -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    exact = record("exact", activity=now - timedelta(days=365))
    older = record("older", activity=now - timedelta(days=365, microseconds=1))
    active = record("active", activity=now - timedelta(days=500))
    unknown = record("unknown")
    invalid = record("invalid", raw_activity="not-a-date")
    plan = plan_device_cleanup(
        [exact, older, active, unknown, invalid],
        now=now,
        age_days=365,
        active_player_keys=[active.player_key],
    )
    assert plan.candidates == (older,)
    assert plan.skipped_recent == (exact,)
    assert plan.skipped_active == (active,)
    assert plan.skipped_without_activity == (unknown, invalid)


def test_custom_364_and_large_uncapped_plan() -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    records = [
        record(str(index), activity=now - timedelta(days=365 + index)) for index in range(300)
    ]
    plan = plan_device_cleanup(records, now=now, age_days=364)
    assert len(plan.candidates) == 300


def test_registry_followup_separates_active_remaining_and_eligible() -> None:
    eligible = record("1", client_id="one", app_name="App")
    active = record("2", client_id="two", app_name="App")
    remaining = record("3", client_id="three", app_name="App")
    plan = plan_registry_followup(
        [eligible, active, remaining],
        [record("4", client_id="three", app_name="App")],
        active_player_keys=[active.player_key],
    )
    assert plan.eligible_keys == (eligible.player_key,)
    assert plan.protected_active_keys == (active.player_key,)
    assert plan.protected_remaining_history_keys == (remaining.player_key,)
