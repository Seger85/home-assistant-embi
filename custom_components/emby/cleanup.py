from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from .api import EmbyApiError, EmbyDeviceRecord


class DeviceDeleteClient(Protocol):
    """Protocol implemented by the EMBi REST client."""

    async def async_delete_device(self, record_id: str) -> None:
        """Delete one server-side device-history record."""


@dataclass(frozen=True, slots=True)
class DeviceCleanupResult:
    """Result of a batch device-history cleanup."""

    succeeded: tuple[EmbyDeviceRecord, ...]
    failed: tuple[EmbyDeviceRecord, ...]


async def async_delete_device_records(
    client: DeviceDeleteClient, records: Iterable[EmbyDeviceRecord]
) -> DeviceCleanupResult:
    """Delete records independently so one failure does not abort the batch."""
    succeeded: list[EmbyDeviceRecord] = []
    failed: list[EmbyDeviceRecord] = []

    for record in records:
        try:
            await client.async_delete_device(record.record_id)
        except EmbyApiError:
            failed.append(record)
        else:
            succeeded.append(record)

    return DeviceCleanupResult(tuple(succeeded), tuple(failed))
