from __future__ import annotations

from homeassistant.core import HomeAssistant

from .entry_lifecycle import async_migrate_entry, async_unload_entry
from .entry_setup import async_setup_entry

__all__ = ["async_migrate_entry", "async_setup_entry", "async_unload_entry"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up EMBi."""
    return True
