from __future__ import annotations

import logging

from .const import (
    RUN_STATUS_FAILED,
    RUN_STATUS_INTERRUPTED,
    RUN_STATUS_PARTIAL_FAILURE,
)
from .models import CleanupRunReport


def log_level_for_report(report: CleanupRunReport) -> int:
    """Return the required log level for a terminal cleanup report."""
    if report.status == RUN_STATUS_FAILED:
        return logging.ERROR
    if report.status in {RUN_STATUS_PARTIAL_FAILURE, RUN_STATUS_INTERRUPTED}:
        return logging.WARNING
    return logging.INFO


def notification_required(report: CleanupRunReport) -> bool:
    """Return whether a terminal report requires a persistent notification."""
    return report.status in {
        RUN_STATUS_FAILED,
        RUN_STATUS_PARTIAL_FAILURE,
        RUN_STATUS_INTERRUPTED,
    }
