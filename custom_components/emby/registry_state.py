from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def state_is_restored(state: Any | None) -> bool:
    """Return whether Home Assistant restored this state without a live entity."""
    if state is None:
        return False
    attributes = getattr(state, "attributes", None)
    return bool(isinstance(attributes, Mapping) and attributes.get("restored") is True)


def state_can_be_removed_after_visibility_commit(state: Any | None) -> bool:
    """Allow restored or definitively inactive states after a committed hide."""
    if state is None or state_is_restored(state):
        return True
    return str(getattr(state, "state", "")).casefold() in {
        "idle",
        "off",
        "standby",
        "unavailable",
    }


def state_blocks_registry_removal(state: Any | None) -> bool:
    """Protect only live non-restored states that are not definitively inactive."""
    return not state_can_be_removed_after_visibility_commit(state)
