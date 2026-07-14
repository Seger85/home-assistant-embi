from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.emby.api import EmbyApiError, EmbyDeviceRecord
from custom_components.emby.cleanup import (
    async_delete_device_records,
    plan_device_cleanup,
    removable_player_keys,
)


class FakeDeleteClient:
    def __init__(self, failing_ids: set[str] | None = None) -> None:
        self.failing_ids = failing_ids or set()
        self.calls: list[str] = []

    async def async_delete_device(self, record_id: str) -> None:
        self.calls.append(record_id)
        if record_id in self.failing_ids:
            raise EmbyApiError("delete denied")


def _record(
    record_id: str,
    *,
    client_id: str | None = None,
    app_name: str = "Emby App",
    activity: datetime | None = None,
) -> EmbyDeviceRecord:
    return EmbyDeviceRecord.from_api(
        {
            "Id": record_id,
            "ReportedDeviceId": client_id or f"client-{record_id}",
            "Name": f"Device {record_id}",
            "AppName": app_name,
            "DateLastActivity": activity.isoformat().replace("+00:00", "Z") if activity else None,
        }
    )


@pytest.mark.asyncio
async def test_batch_cleanup_keeps_processing_after_failure() -> None:
    client = FakeDeleteClient({"2"})
    records = [_record("1"), _record("2"), _record("3")]

    result = await async_delete_device_records(client, records)

    assert client.calls == ["1", "2", "3"]
    assert [record.record_id for record in result.succeeded] == ["1", "3"]
    assert [record.record_id for record in result.failed] == ["2"]


@pytest.mark.asyncio
async def test_batch_cleanup_can_return_all_successful() -> None:
    client = FakeDeleteClient()
    records = [_record("1"), _record("2")]

    result = await async_delete_device_records(client, records)

    assert result.failed == ()
    assert [record.record_id for record in result.succeeded] == ["1", "2"]


@pytest.mark.asyncio
async def test_batch_cleanup_has_no_per_run_deletion_cap() -> None:
    client = FakeDeleteClient()
    records = [_record(str(index)) for index in range(250)]

    result = await async_delete_device_records(client, records)

    assert len(client.calls) == 250
    assert len(result.succeeded) == 250
    assert result.failed == ()


def test_age_plan_uses_default_style_cutoff_and_skips_active_or_unknown() -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    expired = _record("old", activity=now - timedelta(days=366))
    recent = _record("recent", activity=now - timedelta(days=364))
    active = _record("active", activity=now - timedelta(days=500))
    unknown = _record("unknown")

    plan = plan_device_cleanup(
        [expired, recent, active, unknown],
        now=now,
        age_days=365,
        active_player_keys=[active.player_key],
    )

    assert plan.candidates == (expired,)
    assert plan.skipped_recent == (recent,)
    assert plan.skipped_active == (active,)
    assert plan.skipped_without_activity == (unknown,)


def test_age_plan_does_not_limit_number_of_candidates() -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    records = [
        _record(str(index), activity=now - timedelta(days=800 + index)) for index in range(300)
    ]

    plan = plan_device_cleanup(records, now=now, age_days=365)

    assert len(plan.candidates) == 300


def test_registry_key_is_removed_only_after_last_server_record_disappears() -> None:
    old = _record(
        "old",
        client_id="client-1",
        app_name="Emby Windows",
        activity=datetime(2024, 1, 1, tzinfo=UTC),
    )
    duplicate = _record(
        "new",
        client_id="client-1",
        app_name="Emby Windows",
        activity=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert removable_player_keys([old], [duplicate]) == ()
    assert removable_player_keys([old, duplicate], []) == (old.player_key,)


def test_active_player_key_is_never_queued_for_registry_removal() -> None:
    record = _record(
        "old",
        client_id="client-1",
        app_name="Emby Windows",
        activity=datetime(2024, 1, 1, tzinfo=UTC),
    )

    assert (
        removable_player_keys(
            [record],
            [],
            active_player_keys=[record.player_key],
        )
        == ()
    )
