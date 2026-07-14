from __future__ import annotations

import logging

from custom_components.emby.models import CleanupRunReport
from custom_components.emby.reporting import log_level_for_report, notification_required


def test_logging_and_notification_policy() -> None:
    for status in ("completed", "idle"):
        report = CleanupRunReport(status=status)
        assert log_level_for_report(report) == logging.INFO
        assert notification_required(report) is False
    report = CleanupRunReport(status="partial_failure")
    assert log_level_for_report(report) == logging.WARNING
    assert notification_required(report) is True
    report = CleanupRunReport(status="interrupted")
    assert log_level_for_report(report) == logging.WARNING
    assert notification_required(report) is True
    report = CleanupRunReport(status="failed")
    assert log_level_for_report(report) == logging.ERROR
    assert notification_required(report) is True
