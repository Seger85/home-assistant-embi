from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .const import MAINTENANCE_STORE_KEY_PREFIX, MAINTENANCE_STORE_VERSION
from .models import MaintenanceState


class StoreBackend(Protocol):
    """Minimal Home Assistant Store interface used by EMBi."""

    async def async_load(self) -> dict[str, Any] | None:
        """Load stored data."""

    async def async_save(self, data: dict[str, Any]) -> None:
        """Persist data."""


@dataclass(frozen=True, slots=True)
class StoreLoadResult:
    """Resolved store state plus whether first-use initialization is required."""

    state: MaintenanceState
    needs_initial_save: bool


def resolve_store_load(
    data: dict[str, Any] | None,
    *,
    initialized_marker: bool,
) -> StoreLoadResult:
    """Distinguish a new store from an unexpectedly missing or corrupt store."""
    if data is None:
        if initialized_marker:
            raise ValueError("maintenance_store_missing_after_initialization")
        return StoreLoadResult(MaintenanceState(), True)
    return StoreLoadResult(MaintenanceState.from_dict(data), False)


class EmbiMaintenanceStore:
    """Versioned persistent maintenance state for one config entry."""

    def __init__(self, backend: StoreBackend) -> None:
        self._backend = backend

    @classmethod
    def create(cls, hass: Any, entry_id: str) -> EmbiMaintenanceStore:
        """Create a store using Home Assistant's official storage API."""
        from homeassistant.helpers.storage import Store

        backend = Store(
            hass,
            MAINTENANCE_STORE_VERSION,
            f"{MAINTENANCE_STORE_KEY_PREFIX}.{entry_id}",
            private=True,
            atomic_writes=True,
        )
        return cls(backend)

    async def async_load_data(self) -> dict[str, Any] | None:
        """Load the unwrapped Store payload for fail-safe classification."""
        return await self._backend.async_load()

    async def async_load(self) -> MaintenanceState:
        """Load an existing state; missing data resolves to an empty state."""
        return MaintenanceState.from_dict(await self.async_load_data())

    async def async_save(self, state: MaintenanceState) -> None:
        """Persist the complete state immediately."""
        await self._backend.async_save(state.as_dict())
