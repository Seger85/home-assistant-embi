from __future__ import annotations

import pytest

from custom_components.emby.api import EmbyApiError, EmbyDeviceRecord
from custom_components.emby.cleanup import async_delete_device_records


class FakeDeleteClient:
    def __init__(self, failing_ids: set[str] | None = None) -> None:
        self.failing_ids = failing_ids or set()
        self.calls: list[str] = []

    async def async_delete_device(self, record_id: str) -> None:
        self.calls.append(record_id)
        if record_id in self.failing_ids:
            raise EmbyApiError("delete denied")


def _record(record_id: str) -> EmbyDeviceRecord:
    return EmbyDeviceRecord.from_api(
        {
            "Id": record_id,
            "ReportedDeviceId": f"client-{record_id}",
            "Name": f"Device {record_id}",
            "AppName": "Emby App",
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
