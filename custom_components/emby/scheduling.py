from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class ScheduleDecision:
    """Resolved absolute schedule decision."""

    run_at: datetime
    catch_up: bool


def resolve_scheduled_run(
    *,
    now: datetime,
    persisted_next_run: datetime | None,
    grace_seconds: int,
) -> ScheduleDecision:
    """Preserve future absolute times and grace missing or overdue runs once."""
    if persisted_next_run is not None and persisted_next_run > now:
        return ScheduleDecision(run_at=persisted_next_run, catch_up=False)
    return ScheduleDecision(
        run_at=now + timedelta(seconds=max(1, int(grace_seconds))),
        catch_up=True,
    )
