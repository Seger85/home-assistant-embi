from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .api import EmbyApiError
from .const import (
    AUTO_CLEANUP_INITIAL_DELAY_SECONDS,
    AUTO_CLEANUP_INTERVAL_HOURS,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_INITIAL_RUN_COMPLETED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_API_KEY,
    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
    NAME,
    VERSION,
)
from .models import EmbiRuntimeData

TO_REDACT = {CONF_API_KEY, CONF_SERVER_CLEANUP_API_KEY}
DEVICE_FIELDS_TO_REDACT = {
    "record_id",
    "reported_device_id",
    "player_key",
    "name",
    "last_user_name",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return privacy-aware diagnostics for an EMBi config entry."""
    runtime: EmbiRuntimeData = entry.runtime_data
    try:
        devices = await runtime.api_client.async_get_devices()
        device_data = [
            async_redact_data(device.as_diagnostics(), DEVICE_FIELDS_TO_REDACT)
            for device in devices
        ]
        device_error = None
    except EmbyApiError as err:
        device_data = []
        device_error = str(err)

    return {
        "integration": {"name": NAME, "version": VERSION},
        "config_entry": {
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "runtime": {
            "device_count": len(device_data),
            "pyemby_initialized": runtime.pyemby is not None,
        },
        "automatic_cleanup": {
            "enabled": bool(entry.options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)),
            "age_days": int(
                entry.options.get(
                    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
                    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
                )
            ),
            "remove_ha_entities": bool(
                entry.options.get(CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES, True)
            ),
            "initial_run_completed": bool(
                entry.options.get(
                    CONF_SERVER_AUTO_CLEANUP_INITIAL_RUN_COMPLETED, False
                )
            ),
            "initial_delay_seconds": AUTO_CLEANUP_INITIAL_DELAY_SECONDS,
            "interval_hours": AUTO_CLEANUP_INTERVAL_HOURS,
            "scheduled": runtime.auto_cleanup_scheduled,
            "last_run_at": runtime.last_auto_cleanup_at,
            "last_candidate_count": runtime.last_auto_cleanup_candidate_count,
            "last_success_count": runtime.last_auto_cleanup_success_count,
            "last_failed_count": runtime.last_auto_cleanup_failed_count,
            "last_skipped_active_count": runtime.last_auto_cleanup_skipped_active_count,
            "last_skipped_without_activity_count": (
                runtime.last_auto_cleanup_skipped_without_activity_count
            ),
            "last_registry_queue_count": runtime.last_auto_cleanup_registry_queue_count,
            "last_error": runtime.last_auto_cleanup_error,
        },
        "devices": device_data,
        "device_query_error": device_error,
    }
