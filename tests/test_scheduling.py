from __future__ import annotations

from datetime import UTC, datetime, timedelta

from custom_components.emby.scheduling import (
    next_regular_run,
    parse_utc,
    resolve_scheduled_run,
    utc_iso,
)


def test_future_persisted_time_survives_reload_and_restart() -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    future = now + timedelta(hours=10)
    resolved, catchup = resolve_scheduled_run(now=now, stored_next_run=utc_iso(future))
    assert resolved == future
    assert catchup is False


def test_missing_invalid_and_overdue_times_get_one_grace_period() -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    expected = now + timedelta(seconds=120)
    for stored in (None, "invalid", utc_iso(now - timedelta(seconds=1))):
        resolved, catchup = resolve_scheduled_run(now=now, stored_next_run=stored)
        assert resolved == expected
        assert catchup is True


def test_next_regular_time_is_24_hours_after_completion() -> None:
    completed = datetime(2026, 7, 14, 14, 47, 17, tzinfo=UTC)
    assert next_regular_run(completed) == completed + timedelta(hours=24)


def test_stored_naive_time_is_normalized_to_utc() -> None:
    parsed = parse_utc("2026-07-15T12:00:00")
    assert parsed == datetime(2026, 7, 15, 12, 0, tzinfo=UTC)


def test_utc_interval_is_stable_across_dst_transition() -> None:
    from zoneinfo import ZoneInfo

    berlin = ZoneInfo("Europe/Berlin")
    completed = datetime(2026, 10, 24, 23, 30, tzinfo=UTC)
    following = next_regular_run(completed)
    assert following - completed == timedelta(hours=24)
    assert completed.astimezone(berlin).utcoffset() != following.astimezone(berlin).utcoffset()
