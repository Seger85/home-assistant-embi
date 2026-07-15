from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

from .api import EmbyApiClient, EmbyDeviceRecord
from .const import FOLLOW_UP_IDLE, MAINTENANCE_STORE_VERSION, RUN_STATUS_IDLE


@dataclass(slots=True)
class CleanupRunReport:
    """Privacy-safe result of one manual or automatic cleanup run."""

    status: str = RUN_STATUS_IDLE
    mode: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    age_threshold_days: int | None = None
    server_candidates: int = 0
    server_deleted: int = 0
    server_failed: int = 0
    skipped_active: int = 0
    skipped_without_activity: int = 0
    registry_keys_queued: int = 0
    registry_entities_matched: int = 0
    registry_entities_removed: int = 0
    registry_entities_missing: int = 0
    registry_entities_protected_active: int = 0
    registry_entities_protected_remaining_history: int = 0
    registry_entities_wrong_entry: int = 0
    registry_entities_wrong_platform: int = 0
    registry_entities_wrong_unique_id: int = 0
    registry_entities_state_still_present: int = 0
    registry_entities_revalidation_ambiguous: int = 0
    last_error: str | None = None
    result_counts_complete: bool = True
    follow_up_status: str = FOLLOW_UP_IDLE
    next_run_at: str | None = None

    @property
    def registry_entities_protected(self) -> int:
        return sum(
            (
                self.registry_entities_protected_active,
                self.registry_entities_protected_remaining_history,
                self.registry_entities_wrong_entry,
                self.registry_entities_wrong_platform,
                self.registry_entities_wrong_unique_id,
                self.registry_entities_state_still_present,
                self.registry_entities_revalidation_ambiguous,
            )
        )

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["registry_entities_protected"] = self.registry_entities_protected
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CleanupRunReport:
        if not isinstance(data, Mapping):
            raise ValueError("maintenance report must be a mapping")
        fields = cls.__dataclass_fields__
        values = {key: data[key] for key in fields if key in data}
        string_fields = {
            "status",
            "mode",
            "started_at",
            "completed_at",
            "last_error",
            "follow_up_status",
            "next_run_at",
        }
        integer_fields = {
            "age_threshold_days",
            "server_candidates",
            "server_deleted",
            "server_failed",
            "skipped_active",
            "skipped_without_activity",
            "registry_keys_queued",
            "registry_entities_matched",
            "registry_entities_removed",
            "registry_entities_missing",
            "registry_entities_protected_active",
            "registry_entities_protected_remaining_history",
            "registry_entities_wrong_entry",
            "registry_entities_wrong_platform",
            "registry_entities_wrong_unique_id",
            "registry_entities_state_still_present",
            "registry_entities_revalidation_ambiguous",
        }
        for key in string_fields & values.keys():
            if values[key] is not None and not isinstance(values[key], str):
                raise ValueError(f"maintenance report field {key} must be text or null")
        for key in integer_fields & values.keys():
            if values[key] is not None and (
                not isinstance(values[key], int) or isinstance(values[key], bool) or values[key] < 0
            ):
                raise ValueError(f"maintenance report field {key} must be a non-negative integer")
        if "result_counts_complete" in values and not isinstance(
            values["result_counts_complete"], bool
        ):
            raise ValueError("result_counts_complete must be boolean")
        return cls(**values)


@dataclass(slots=True)
class MaintenanceState:
    report: CleanupRunReport = field(default_factory=CleanupRunReport)
    initial_run_completed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": MAINTENANCE_STORE_VERSION,
            "report": self.report.as_dict(),
            "initial_run_completed": self.initial_run_completed,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MaintenanceState:
        if not isinstance(data, Mapping):
            raise ValueError("maintenance state must be a mapping")
        if data.get("schema_version") != MAINTENANCE_STORE_VERSION:
            raise ValueError("unsupported maintenance Store schema version")
        initial = data.get("initial_run_completed", False)
        if not isinstance(initial, bool):
            raise ValueError("initial_run_completed must be boolean")
        return cls(
            report=CleanupRunReport.from_dict(data.get("report", {})),
            initial_run_completed=initial,
        )


@dataclass(slots=True, frozen=True)
class PendingRegistryTarget:
    player_key: str
    entity_id: str | None
    ambiguous: bool = False


@dataclass(slots=True, frozen=True)
class RegistryCleanupResult:
    queued: int = 0
    matched: int = 0
    removed: int = 0
    missing: int = 0
    protected_remaining_history: int = 0
    wrong_entry: int = 0
    wrong_platform: int = 0
    wrong_unique_id: int = 0
    state_still_present: int = 0
    revalidation_ambiguous: int = 0


@dataclass(slots=True)
class EmbiRuntimeData:
    api_client: EmbyApiClient
    devices: list[EmbyDeviceRecord] = field(default_factory=list)
    pyemby: Any | None = None
    cleanup_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    maintenance_store: Any | None = None
    maintenance_state: MaintenanceState = field(default_factory=MaintenanceState)
    maintenance_storage_available: bool = True
    auto_cleanup_scheduled: bool = False
    cancel_auto_cleanup: Callable[[], None] | None = None
