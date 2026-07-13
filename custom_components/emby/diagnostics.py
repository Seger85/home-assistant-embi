from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .api import EmbyApiError
from .const import DATA_CLIENT, DOMAIN, NAME, VERSION

TO_REDACT = {CONF_API_KEY}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    runtime = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    client = runtime.get(DATA_CLIENT)
    try:
        devices = await client.async_get_devices() if client else []
        device_data = [device.as_diagnostics() for device in devices]
        device_error = None
    except EmbyApiError as err:
        device_data = []
        device_error = str(err)
    return {
        "integration": {"name": NAME, "version": VERSION},
        "config_entry": {
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "devices": device_data,
        "device_query_error": device_error,
    }
