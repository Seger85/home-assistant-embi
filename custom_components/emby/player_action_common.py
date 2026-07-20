from __future__ import annotations

from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN


def owned_exact(entity: object | None, entry: ConfigEntry, player_key: str) -> bool:
    """Return whether an entity is owned by this exact EMBi player contract."""
    return bool(
        entity is not None
        and getattr(entity, "domain", None) == "media_player"
        and getattr(entity, "platform", None) == DOMAIN
        and getattr(entity, "config_entry_id", None) == entry.entry_id
        and str(getattr(entity, "unique_id", "")) == player_key
    )
