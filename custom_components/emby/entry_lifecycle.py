from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONFIG_ENTRY_MINOR_VERSION, CONFIG_ENTRY_VERSION, PLATFORMS
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
    """Advance the schema marker without changing entity identities or options."""
    if entry.version < CONFIG_ENTRY_VERSION or entry.minor_version < CONFIG_ENTRY_MINOR_VERSION:
        hass.config_entries.async_update_entry(
            entry,
            version=CONFIG_ENTRY_VERSION,
            minor_version=CONFIG_ENTRY_MINOR_VERSION,
        )
    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload once after a completed normal options-flow apply."""
    runtime = getattr(entry, "runtime_data", None)
    if runtime is not None and runtime.suppress_update_listener:
        return
    await hass.config_entries.async_reload(entry.entry_id)
