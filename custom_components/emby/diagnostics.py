from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .api import EmbyApiError
from .const import CONF_SERVER_CLEANUP_API_KEY, NAME, VERSION
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
        "devices": device_data,
        "device_query_error": device_error,
    }
