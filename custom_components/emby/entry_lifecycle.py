from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import PLATFORMS
from .models import EmbiRuntimeData


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an EMBi config entry."""
    runtime: EmbiRuntimeData = entry.runtime_data
    runtime.unloading = True

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unloaded:
        runtime.unloading = False
        return False

    if runtime.cancel_auto_cleanup is not None:
        runtime.cancel_auto_cleanup()
        runtime.cancel_auto_cleanup = None
    runtime.auto_cleanup_scheduled = False
    if runtime.pyemby is not None:
        await runtime.pyemby.stop()
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config-entry formats without changing entity identities."""
    if entry.version < 3:
        hass.config_entries.async_update_entry(entry, version=3, minor_version=1)
    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload EMBi once after a completed options-flow apply."""
    await hass.config_entries.async_reload(entry.entry_id)
