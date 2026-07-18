from __future__ import annotations

from collections.abc import Iterable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_ENABLED,
    DEFAULT_REMOVE_HA_ENTITIES,
    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
    RUN_MODE_AUTOMATIC,
    RUN_MODE_MANUAL,
    RUN_STATUS_REGISTRY_PENDING,
)
from .maintenance_cycle_execute import _async_execute_cleanup
from .models import CleanupRunReport


async def async_run_manual_cleanup(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    selected_record_ids: Iterable[str],
    age_days: int,
    remove_ha_entities: bool,
    ignore_age: bool = False,
) -> tuple[CleanupRunReport, bool]:
    """Run a revalidated manual cleanup."""
    return await _async_execute_cleanup(
        hass,
        entry,
        mode=RUN_MODE_MANUAL,
        age_days=age_days,
        remove_ha_entities=remove_ha_entities,
        selected_record_ids={str(value) for value in selected_record_ids},
        ignore_age=ignore_age,
    )


async def async_run_automatic_cleanup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Run one automatic cleanup cycle and return whether a reload is required."""
    if not (
        entry.options.get(CONF_SERVER_CLEANUP_ENABLED, False)
        and entry.options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)
    ):
        return False
    report, reload_needed = await _async_execute_cleanup(
        hass,
        entry,
        mode=RUN_MODE_AUTOMATIC,
        age_days=int(
            entry.options.get(
                CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
                DEFAULT_SERVER_CLEANUP_AGE_DAYS,
            )
        ),
        remove_ha_entities=bool(
            entry.options.get(
                CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
                DEFAULT_REMOVE_HA_ENTITIES,
            )
        ),
    )
    return reload_needed and report.status == RUN_STATUS_REGISTRY_PENDING
