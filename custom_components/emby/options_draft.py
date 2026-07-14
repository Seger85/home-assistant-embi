from __future__ import annotations

from copy import deepcopy
from typing import Any


class OptionsDraft:
    """Mutable draft that never writes through to stored options."""

    def __init__(self, options: dict[str, Any]) -> None:
        self.original = deepcopy(options)
        self.current = deepcopy(options)

    @property
    def dirty(self) -> bool:
        """Return whether the draft differs from the original options."""
        return self.current != self.original

    def discard(self) -> None:
        """Discard all changes without replacing public dict references."""
        self.current.clear()
        self.current.update(deepcopy(self.original))

    def applied(self, options: dict[str, Any]) -> None:
        """Update both snapshots after a successful apply."""
        self.original.clear()
        self.original.update(deepcopy(options))
        self.current.clear()
        self.current.update(deepcopy(options))
