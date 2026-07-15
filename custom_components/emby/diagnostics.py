from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ALLOWED_DEVICE_IDS,
    CONF_IGNORED_PLAYER_KEYS,
    CONF_IGNORED_REPORTED_DEVICE_IDS,
    CONF_UNRESOLVED_IGNORED_IDS,
    NAME,
    VERSION,
)
from .models import EmbiRuntimeData

_OPTION_IDENTITIES = {
    CONF_ALLOWED_DEVICE_IDS,
    CONF_IGNORED_PLAYER_KEYS,
    CONF_IGNORED_REPORTED_DEVICE_IDS,
    CONF_UNRESOLVED_IGNORED_IDS,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return aggregate diagnostics without private device identities."""
    runtime: EmbiRuntimeData = entry.runtime_data
    return {
        "integration": {"name": NAME, "version": VERSION},
        "config_entry": {
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), {CONF_API_KEY}),
            "options": async_redact_data(dict(entry.options), _OPTION_IDENTITIES),
        },
        "runtime": {
            "device_count": len(runtime.devices),
            "pyemby_initialized": runtime.pyemby is not None,
            "maintenance_storage_available": runtime.maintenance_storage_available,
            "automatic_cleanup_scheduled": runtime.auto_cleanup_scheduled,
        },
        "last_cleanup_run": runtime.maintenance_state.report.as_dict(),
    }
