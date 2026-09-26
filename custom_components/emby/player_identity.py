"""Entry-scoped identities for new players, preserving every existing unique ID."""

from __future__ import annotations

from typing import Any

from .const import DOMAIN


def player_key_from_unique_id(unique_id: str, entry_id: str) -> str:
    """Decode our namespace; unprefixed published identities remain valid."""
    return str(unique_id).removeprefix(f"{entry_id}::")


def unique_id_matches(unique_id: str, entry_id: str, player_key: str) -> bool:
    return str(unique_id) in {player_key, f"{entry_id}::{player_key}"}


def player_unique_id(registry: Any, entry_id: str, player_key: str) -> str:
    """Reuse an owned legacy identity (including its HA tombstone), otherwise scope it."""
    for entity in (
        *registry.entities.values(),
        *getattr(registry, "deleted_entities", {}).values(),
    ):
        if (
            getattr(entity, "platform", None) == DOMAIN
            and getattr(entity, "config_entry_id", None) == entry_id
            and unique_id_matches(entity.unique_id, entry_id, player_key)
        ):
            # Deleted registry entries expose domain through their entity_id.
            domain = getattr(
                entity, "domain", str(getattr(entity, "entity_id", "")).partition(".")[0]
            )
            if domain == "media_player":
                return str(entity.unique_id)
    return f"{entry_id}::{player_key}"
