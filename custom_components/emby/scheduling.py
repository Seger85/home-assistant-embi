from __future__ import annotations

from datetime import UTC, datetime, timedelta


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
    except ValueError:
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
    stored_next_run: str | None,
    grace_seconds: int = 120,
) -> tuple[datetime, bool]:
    """Resolve the next absolute run and whether it is a catch-up/initial grace run.

    A future persisted value is preserved exactly. A missing, invalid, or overdue
    value is scheduled once after the grace period instead of running during setup.
    """
    normalized_now = normalize_utc(now)
    stored = parse_utc(stored_next_run)
    if stored is not None and stored > normalized_now:
        return stored, False
    return normalized_now + timedelta(seconds=grace_seconds), True
