from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .api import EmbyApiClient, EmbyDeviceRecord


@dataclass(slots=True)
class EmbiRuntimeData:
    """Runtime data for one EMBi config entry."""

    api_client: EmbyApiClient
    devices: list[EmbyDeviceRecord] = field(default_factory=list)
    pyemby: Any | None = None
