from __future__ import annotations

from homeassistant.helpers import entity_registry as er


def remove_exact_registry_entity(registry: er.EntityRegistry, entity_id: str) -> None:
    """Remove one registry entity after all caller-side safety checks passed."""
    registry.async_remove(entity_id)
