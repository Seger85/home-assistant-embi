from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def state_is_restored(state: Any | None) -> bool:
    """Return whether Home Assistant restored this state without a live entity."""
    if state is None:
        return False
    attributes = getattr(state, "attributes", None)
    return bool(isinstance(attributes, Mapping) and attributes.get("restored") is True)


def state_blocks_registry_removal(state: Any | None) -> bool:
    """Protect live states while allowing exact stale-restored registry cleanup."""
    return state is not None and not state_is_restored(state)
