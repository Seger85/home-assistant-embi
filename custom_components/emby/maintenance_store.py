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
class StoreLoadDecision:
    """Fail-safe interpretation of a Store load result."""

    state: MaintenanceState
    storage_available: bool
    initialize_store: bool


def resolve_store_load(
    loaded: MaintenanceState | None,
    *,
    store_expected: bool,
    legacy_initial_run_completed: bool,
) -> StoreLoadDecision:
    """Distinguish first initialization from an unexpectedly missing Store.

    Home Assistant returns ``None`` for both a new Store and a Store it had to
    quarantine after corruption. A hidden config-entry marker records whether
    EMBi has successfully initialized the Store before. If that marker exists,
    a missing load result is treated as unsafe and automatic cleanup stays off.
    """
    if loaded is None and store_expected:
        return StoreLoadDecision(MaintenanceState(), False, False)

    state = loaded or MaintenanceState()
    if legacy_initial_run_completed:
        state.initial_run_completed = True
    return StoreLoadDecision(
        state=state,
        storage_available=True,
        initialize_store=loaded is None,
    )


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

    async def async_load(self) -> MaintenanceState | None:
        """Load the stored state without hiding a missing/corrupt result."""
        data = await self._backend.async_load()
        return MaintenanceState.from_dict(data) if data is not None else None

    async def async_save(self, state: MaintenanceState) -> None:
        """Persist the complete state immediately."""
        await self._backend.async_save(state.as_dict())
