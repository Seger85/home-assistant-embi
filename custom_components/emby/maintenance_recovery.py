"""Explicit recovery of maintenance persistence, independent of media playback."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_MAINTENANCE_STORE_INITIALIZED
from .maintenance_common import _dismiss_failure, _next_regular_run, _utc_iso
from .maintenance_scheduler import async_schedule_automatic_cleanup
from .models import CleanupRunReport, EmbiRuntimeData, MaintenanceState


async def async_recover_maintenance(
    hass: HomeAssistant, entry: ConfigEntry, *, reset: bool
) -> bool:
    """Retry trusted storage or create a new journal only after explicit confirmation."""
    runtime: EmbiRuntimeData = entry.runtime_data
    if not runtime.is_current(entry) or runtime.cleanup_lock.locked():
        return False
    async with runtime.cleanup_lock:
        try:
            state = None if reset else await runtime.maintenance_store.async_load()
            if not reset and state is None:
                return False
            deadline = _next_regular_run()
            if reset:
                state = MaintenanceState(
                    initial_run_completed=True,
                    automatic_next_run_at=deadline,
                    report=CleanupRunReport(next_run_at=deadline),
                )
            elif state.report.status in {"running", "server_completed", "registry_pending"}:
                state.report.status = "interrupted"
                state.report.follow_up_status = "interrupted"
                state.report.result_counts_complete = False
                state.report.last_error = "cleanup_interrupted_before_completion"
                state.report.completed_at = _utc_iso()
                state.report.next_run_at = deadline
                state.automatic_next_run_at = deadline
            if not runtime.is_current(entry):
                return False
            await runtime.maintenance_store.async_save(state)
        except Exception:
            return False
        if not runtime.is_current(entry):
            return False
        runtime.maintenance_state = state
        runtime.maintenance_storage_available = True
        runtime.maintenance_recovery_required = False
        options = dict(entry.options)
        options[CONF_MAINTENANCE_STORE_INITIALIZED] = True
        runtime.suppress_update_listener = True
        try:
            hass.config_entries.async_update_entry(entry, options=options)
        finally:
            runtime.suppress_update_listener = False
    _dismiss_failure(hass, entry)
    await async_schedule_automatic_cleanup(hass, entry)
    return True
