from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True, slots=True)
class ScheduledRunDecision:
    """Resolved absolute run time and whether a grace catch-up was required."""

    run_at: datetime
    catch_up: bool


def normalize_utc(value: datetime) -> datetime:
    """Return an aware UTC datetime."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def parse_utc(value: str | None) -> datetime | None:
    """Parse one stored ISO datetime as UTC."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return normalize_utc(parsed)


def utc_iso(value: datetime) -> str:
    """Serialize one datetime in normalized UTC form."""
    return normalize_utc(value).isoformat()


def next_regular_run(completed_at: datetime, *, interval_hours: int = 24) -> datetime:
    """Return the absolute next run after a completed attempt."""
    return normalize_utc(completed_at) + timedelta(hours=interval_hours)


def resolve_scheduled_run(
    *,
    now: datetime,
    persisted_next_run: datetime | str | None,
    grace_seconds: int = 120,
) -> ScheduledRunDecision:
    """Resolve the persistent schedule without moving a valid future deadline.

    Missing, invalid, or overdue values receive one grace-period catch-up. A
    future persisted deadline survives reloads and restarts unchanged.
    """
    normalized_now = normalize_utc(now)
    if isinstance(persisted_next_run, datetime):
        stored = normalize_utc(persisted_next_run)
    else:
        stored = parse_utc(persisted_next_run)
    if stored is not None and stored > normalized_now:
        return ScheduledRunDecision(stored, False)
    return ScheduledRunDecision(
        normalized_now + timedelta(seconds=max(0, int(grace_seconds))),
        True,
    )
