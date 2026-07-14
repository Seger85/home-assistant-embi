from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .models import PendingRegistryTarget, RegistryCleanupResult

_PENDING_REGISTRY_CLEANUP = f"{DOMAIN}_pending_registry_cleanup"


def queue_registry_cleanup(
    hass: HomeAssistant,
    entry: ConfigEntry,
    player_keys: Iterable[str],
) -> int:
    """Queue exact identities and optional exact entity IDs for same-process follow-up."""
    registry = er.async_get(hass)
    targets: dict[str, PendingRegistryTarget] = {}
    for key in sorted({str(value) for value in player_keys if value}):
        exact = [
            entity
            for entity in registry.entities.values()
            if entity.domain == "media_player"
            and entity.platform == DOMAIN
            and entity.config_entry_id == entry.entry_id
            and str(entity.unique_id) == key
        ]
        targets[key] = PendingRegistryTarget(
            player_key=key,
            entity_id=exact[0].entity_id if len(exact) == 1 else None,
            ambiguous=len(exact) > 1,
        )
    if not targets:
        return 0
    pending = hass.data.setdefault(_PENDING_REGISTRY_CLEANUP, {})
    pending[entry.entry_id] = targets
    return len(targets)


def _classify_unbound_exact_matches(
    registry: er.EntityRegistry,
    entry: ConfigEntry,
    player_key: str,
) -> tuple[Any | None, str | None]:
    exact_unique = [
        entity for entity in registry.entities.values() if str(entity.unique_id) == player_key
    ]
    if not exact_unique:
        return None, "missing"
    valid = [
        entity
        for entity in exact_unique
        if entity.domain == "media_player"
        and entity.platform == DOMAIN
        and entity.config_entry_id == entry.entry_id
    ]
    if len(valid) == 1:
        return valid[0], None
    if len(valid) > 1:
        return None, "ambiguous"
    if any(entity.domain != "media_player" or entity.platform != DOMAIN for entity in exact_unique):
        return None, "wrong_platform"
    if any(entity.config_entry_id != entry.entry_id for entity in exact_unique):
        return None, "wrong_entry"
    return None, "ambiguous"
