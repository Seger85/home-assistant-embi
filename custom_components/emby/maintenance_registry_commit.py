from __future__ import annotations

from collections.abc import Iterable

from homeassistant.helpers import entity_registry as er

from .registry_operations import remove_exact_registry_entity


def apply_exact_registry_removals(
    registry: er.EntityRegistry,
    entity_ids: Iterable[str],
) -> int:
    """Apply only entity IDs returned by the exact safety evaluation."""
    removed = 0
    for entity_id in entity_ids:
        remove_exact_registry_entity(registry, entity_id)
        removed += 1
    return removed
