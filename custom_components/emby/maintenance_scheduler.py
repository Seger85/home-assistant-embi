from __future__ import annotations

from datetime import datetime

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util

from .const import (
    AUTO_CLEANUP_INITIAL_DELAY_SECONDS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_CLEANUP_ENABLED,
)
from .maintenance_common import _async_save_state, _parse_utc, _utc_iso
from .maintenance_cycle import async_run_automatic_cleanup
from .models import EmbiRuntimeData
from .scheduling import resolve_scheduled_run


async def async_schedule_automatic_cleanup(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Schedule the persistent absolute automatic cleanup time."""
    runtime: EmbiRuntimeData = entry.runtime_data
    if runtime.cancel_auto_cleanup is not None:
        runtime.cancel_auto_cleanup()
        runtime.cancel_auto_cleanup = None
    runtime.auto_cleanup_scheduled = False

    if not (
        runtime.maintenance_storage_available
        and entry.options.get(CONF_SERVER_CLEANUP_ENABLED, False)
        and entry.options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)
    ):
        return

    now = dt_util.utcnow()
    decision = resolve_scheduled_run(
        now=now,
        persisted_next_run=_parse_utc(runtime.maintenance_state.report.next_run_at),
        grace_seconds=AUTO_CLEANUP_INITIAL_DELAY_SECONDS,
    )
    next_run = decision.run_at
    if decision.catch_up:
        runtime.maintenance_state.report.next_run_at = _utc_iso(next_run)
        if not await _async_save_state(hass, entry):
            return

    async def _async_scheduled_run(_now: datetime) -> None:
        runtime.cancel_auto_cleanup = None
        runtime.auto_cleanup_scheduled = False
        if not (
            entry.state is ConfigEntryState.LOADED
            and entry.options.get(CONF_SERVER_CLEANUP_ENABLED, False)
            and entry.options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)
            and runtime.maintenance_storage_available
        ):
            return
        reload_needed = await async_run_automatic_cleanup(hass, entry)
        if reload_needed and entry.state is ConfigEntryState.LOADED:
            await hass.config_entries.async_reload(entry.entry_id)
            return
        if entry.state is ConfigEntryState.LOADED and not runtime.cleanup_lock.locked():
            await async_schedule_automatic_cleanup(hass, entry)

    runtime.cancel_auto_cleanup = async_track_point_in_utc_time(
        hass,
        _async_scheduled_run,
        next_run,
    )
    runtime.auto_cleanup_scheduled = True


async def async_setup_automatic_cleanup(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Restore or create the persistent absolute automatic cleanup schedule."""
    await async_schedule_automatic_cleanup(hass, entry)
