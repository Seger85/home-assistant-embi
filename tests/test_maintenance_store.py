from __future__ import annotations

import pytest

from custom_components.emby.const import MAINTENANCE_STORE_VERSION
from custom_components.emby.maintenance_store import EmbiMaintenanceStore, resolve_store_load
from custom_components.emby.models import CleanupRunReport, MaintenanceState


class FakeBackend:
    def __init__(self, data=None, *, fail_load: bool = False, fail_save: bool = False) -> None:
        self.data = data
        self.fail_load = fail_load
        self.fail_save = fail_save
        self.saved = None

    async def async_load(self):
        if self.fail_load:
            raise OSError("read failed")
        return self.data

    async def async_save(self, data):
        if self.fail_save:
            raise OSError("write failed")
        self.saved = data


@pytest.mark.asyncio
async def test_empty_store_initializes_once_and_preserves_rc3_completion_marker() -> None:
    store = EmbiMaintenanceStore(FakeBackend())
    loaded = await store.async_load()
    decision = resolve_store_load(
        loaded,
        store_expected=False,
        legacy_initial_run_completed=True,
    )
    assert decision.initialize_store is True
    assert decision.storage_available is True
    assert decision.state.initial_run_completed is True


@pytest.mark.asyncio
async def test_missing_expected_store_fails_closed() -> None:
    loaded = await EmbiMaintenanceStore(FakeBackend()).async_load()
    decision = resolve_store_load(
        loaded,
        store_expected=True,
        legacy_initial_run_completed=True,
    )
    assert decision.storage_available is False
    assert decision.initialize_store is False
    assert decision.state == MaintenanceState()


@pytest.mark.asyncio
async def test_store_round_trip_contains_schema_version_and_scheduler() -> None:
    original = MaintenanceState(
        report=CleanupRunReport(
            status="completed",
            mode="automatic",
            server_candidates=5,
            server_deleted=5,
            registry_keys_queued=5,
            registry_entities_missing=5,
            next_run_at="2026-07-15T14:47:17+00:00",
        ),
        initial_run_completed=True,
    )
    backend = FakeBackend()
    store = EmbiMaintenanceStore(backend)
    await store.async_save(original)
    assert backend.saved["schema_version"] == MAINTENANCE_STORE_VERSION
    restored = await EmbiMaintenanceStore(FakeBackend(backend.saved)).async_load()
    assert restored == original


@pytest.mark.asyncio
async def test_corrupt_or_wrong_schema_store_raises_for_fail_safe_setup() -> None:
    for damaged in (
        {},
        {"schema_version": 999, "report": {}},
        {"schema_version": MAINTENANCE_STORE_VERSION, "report": "broken"},
        {
            "schema_version": MAINTENANCE_STORE_VERSION,
            "report": {"server_deleted": -1},
        },
    ):
        with pytest.raises(ValueError):
            await EmbiMaintenanceStore(FakeBackend(damaged)).async_load()


@pytest.mark.asyncio
async def test_backend_read_and_write_errors_propagate() -> None:
    with pytest.raises(OSError):
        await EmbiMaintenanceStore(FakeBackend(fail_load=True)).async_load()
    with pytest.raises(OSError):
        await EmbiMaintenanceStore(FakeBackend(fail_save=True)).async_save(MaintenanceState())


def test_persistent_state_contains_no_private_identity_fields() -> None:
    text = repr(MaintenanceState(report=CleanupRunReport(server_deleted=5)).as_dict())
    for forbidden in ("record_id", "reported_device_id", "player_key", "api_key", "user_name"):
        assert forbidden not in text
