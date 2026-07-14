from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from .api import EmbyApiClient, EmbyDeviceRecord


@dataclass(slots=True)
class EmbiRuntimeData:
    """Runtime data for one EMBi config entry."""

    api_client: EmbyApiClient
    devices: list[EmbyDeviceRecord] = field(default_factory=list)
    pyemby: Any | None = None
    cleanup_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    auto_cleanup_scheduled: bool = False
    last_auto_cleanup_at: str | None = None
    last_auto_cleanup_candidate_count: int = 0
    last_auto_cleanup_success_count: int = 0
    last_auto_cleanup_failed_count: int = 0
    last_auto_cleanup_skipped_active_count: int = 0
    last_auto_cleanup_skipped_without_activity_count: int = 0
    last_auto_cleanup_registry_queue_count: int = 0
    last_auto_cleanup_error: str | None = None
