from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

from .api import EmbyApiClient, EmbyDeviceRecord
from .const import FOLLOW_UP_IDLE, RUN_STATUS_IDLE


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
    follow_up_status: str = FOLLOW_UP_IDLE
    next_run_at: str | None = None

    @property
    def registry_entities_protected(self) -> int:
        """Return the aggregate count of deliberately protected registry identities."""
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
        """Return a JSON-serializable, identity-free representation."""
        data = asdict(self)
        data["registry_entities_protected"] = self.registry_entities_protected
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> CleanupRunReport:
        """Build a report from a tolerant stored representation."""
        if not isinstance(data, Mapping):
            return cls()
        fields = cls.__dataclass_fields__
        values = {key: data[key] for key in fields if key in data}
        return cls(**values)


@dataclass(slots=True)
class MaintenanceState:
    """Persistent maintenance state for one config entry."""

    report: CleanupRunReport = field(default_factory=CleanupRunReport)
    initial_run_completed: bool = False

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "report": self.report.as_dict(),
            "initial_run_completed": self.initial_run_completed,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> MaintenanceState:
        """Build state from a tolerant stored representation."""
        if not isinstance(data, Mapping):
            return cls()
        return cls(
            report=CleanupRunReport.from_dict(data.get("report")),
            initial_run_completed=bool(data.get("initial_run_completed", False)),
        )


@dataclass(slots=True)
class EmbiRuntimeData:
    """Runtime data for one EMBi config entry."""

    api_client: EmbyApiClient
    devices: list[EmbyDeviceRecord] = field(default_factory=list)
    pyemby: Any | None = None
    cleanup_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    maintenance_store: Any | None = None
    maintenance_state: MaintenanceState = field(default_factory=MaintenanceState)
    maintenance_storage_available: bool = True
    auto_cleanup_scheduled: bool = False
    cancel_auto_cleanup: Callable[[], None] | None = None
