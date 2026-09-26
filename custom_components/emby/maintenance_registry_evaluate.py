from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er

from .api import EmbyDeviceRecord
from .const import DOMAIN
from .maintenance_registry_queue import _classify_unbound_exact_matches
from .models import PendingRegistryTarget, RegistryCleanupResult
from .player_identity import unique_id_matches
from .registry_state import state_blocks_registry_removal


@dataclass(slots=True, frozen=True)
class RegistryEvaluation:
    """Transient exact removals plus an aggregate privacy-safe result."""

    result: RegistryCleanupResult
    entity_ids_to_remove: tuple[str, ...]


def evaluate_registry_targets(
    *,
    registry: er.EntityRegistry,
    states: Any,
    entry: ConfigEntry,
    current_devices: Iterable[EmbyDeviceRecord],
    targets: Mapping[str, PendingRegistryTarget],
    protected_player_keys: Iterable[str] = (),
) -> RegistryEvaluation:
    """Revalidate exact queued targets without mutating the registry."""
    remaining_player_keys = {device.player_key for device in current_devices}
    protected = set(protected_player_keys)
    matched = missing = 0
    protected_remaining = wrong_entry = wrong_platform = wrong_unique = 0
    state_still_present = ambiguous = protected_active = 0
    removable_entity_ids: list[str] = []

    for key, target in targets.items():
        if key in protected:
            protected_active += 1
            continue
        if key in remaining_player_keys:
            protected_remaining += 1
            continue
        if target.ambiguous:
            ambiguous += 1
            continue

        entity = registry.async_get(target.entity_id) if target.entity_id else None
        reason: str | None = None
        if entity is None and target.entity_id is None:
            entity, reason = _classify_unbound_exact_matches(registry, entry, key)
        elif entity is None:
            reason = "missing"

        if reason == "missing":
            missing += 1
            continue
        if reason == "ambiguous":
            ambiguous += 1
            continue
        if reason == "wrong_platform":
            wrong_platform += 1
            continue
        if reason == "wrong_entry":
            wrong_entry += 1
            continue
        if entity is None:
            missing += 1
            continue

        if entity.domain != "media_player" or entity.platform != DOMAIN:
            wrong_platform += 1
            continue
        if entity.config_entry_id != entry.entry_id:
            wrong_entry += 1
            continue
        if not unique_id_matches(entity.unique_id, entry.entry_id, key):
            wrong_unique += 1
            continue

        matched += 1
        if state_blocks_registry_removal(states.get(entity.entity_id)):
            state_still_present += 1
            continue
        removable_entity_ids.append(entity.entity_id)

    return RegistryEvaluation(
        result=RegistryCleanupResult(
            queued=len(targets),
            matched=matched,
            removed=0,
            missing=missing,
            protected_remaining_history=protected_remaining,
            protected_active=protected_active,
            wrong_entry=wrong_entry,
            wrong_platform=wrong_platform,
            wrong_unique_id=wrong_unique,
            state_still_present=state_still_present,
            revalidation_ambiguous=ambiguous,
        ),
        entity_ids_to_remove=tuple(removable_entity_ids),
    )
