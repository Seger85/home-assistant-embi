from __future__ import annotations

from .const import (
    RUN_STATUS_FAILED,
    RUN_STATUS_INTERRUPTED,
    RUN_STATUS_PARTIAL_FAILURE,
)
from .models import CleanupRunReport


def log_level_for_report(report: CleanupRunReport) -> str:
    """Return the stable severity contract for one completed report."""
    if report.status == RUN_STATUS_FAILED:
        return "error"
    if report.status in {RUN_STATUS_PARTIAL_FAILURE, RUN_STATUS_INTERRUPTED}:
        return "warning"
    return "info"


def notification_required(report: CleanupRunReport) -> bool:
    """Return whether a persistent notification is required."""
    return log_level_for_report(report) in {"warning", "error"}
