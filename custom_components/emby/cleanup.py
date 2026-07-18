from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from .api import EmbyApiError, EmbyDeviceRecord


class DeviceDeleteClient(Protocol):
    """Protocol implemented by the EMBi REST client."""

    async def async_delete_device(self, record_id: str) -> None:
        """Delete one server-side device-history record."""


@dataclass(frozen=True, slots=True)
class DeviceCleanupPlan:
    """Age-filtered, safety-checked cleanup candidates."""

    candidates: tuple[EmbyDeviceRecord, ...]
    skipped_active: tuple[EmbyDeviceRecord, ...]
    skipped_recent: tuple[EmbyDeviceRecord, ...]
    skipped_without_activity: tuple[EmbyDeviceRecord, ...]


@dataclass(frozen=True, slots=True)
class DeviceCleanupResult:
    """Result of a batch device-history cleanup."""

    succeeded: tuple[EmbyDeviceRecord, ...]
    failed: tuple[EmbyDeviceRecord, ...]


@dataclass(frozen=True, slots=True)
class RegistryFollowupPlan:
    """Transient exact player identities for registry follow-up."""

    eligible_keys: tuple[str, ...]
    protected_active_keys: tuple[str, ...]
    protected_remaining_history_keys: tuple[str, ...]


def plan_device_cleanup(
    records: Iterable[EmbyDeviceRecord],
    *,
    now: datetime,
    age_days: int,
    active_player_keys: Iterable[str] = (),
    ignore_age: bool = False,
) -> DeviceCleanupPlan:
    """Return all expired records without applying any per-run deletion cap."""
    normalized_now = now if now.tzinfo is not None else now.replace(tzinfo=UTC)
    cutoff = normalized_now.astimezone(UTC) - timedelta(days=max(1, int(age_days)))
    active = {str(value) for value in active_player_keys}

    candidates: list[EmbyDeviceRecord] = []
    skipped_active: list[EmbyDeviceRecord] = []
    skipped_recent: list[EmbyDeviceRecord] = []
    skipped_without_activity: list[EmbyDeviceRecord] = []

    for record in records:
        activity = record.last_activity_datetime
        if activity is None:
            skipped_without_activity.append(record)
        elif record.player_key in active:
            skipped_active.append(record)
        elif ignore_age or activity < cutoff:
            candidates.append(record)
        else:
            skipped_recent.append(record)

    return DeviceCleanupPlan(
        candidates=tuple(candidates),
        skipped_active=tuple(skipped_active),
        skipped_recent=tuple(skipped_recent),
        skipped_without_activity=tuple(skipped_without_activity),
    )


def plan_registry_followup(
    succeeded: Iterable[EmbyDeviceRecord],
    remaining_records: Iterable[EmbyDeviceRecord],
    *,
    active_player_keys: Iterable[str] = (),
) -> RegistryFollowupPlan:
    """Separate eligible, active, and remaining-history player identities."""
    successful_keys = {record.player_key for record in succeeded}
    remaining_keys = {record.player_key for record in remaining_records}
    active = {str(value) for value in active_player_keys}
    protected_active = successful_keys & active
    protected_remaining = (successful_keys & remaining_keys) - protected_active
    eligible = successful_keys - protected_active - protected_remaining
    return RegistryFollowupPlan(
        eligible_keys=tuple(sorted(eligible)),
        protected_active_keys=tuple(sorted(protected_active)),
        protected_remaining_history_keys=tuple(sorted(protected_remaining)),
    )


async def async_delete_device_records(
    client: DeviceDeleteClient, records: Iterable[EmbyDeviceRecord]
) -> DeviceCleanupResult:
    """Delete every supplied record independently; there is deliberately no run cap."""
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
