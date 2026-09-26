from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class OptionsDraft:
    """Mutable draft whose original value remains unchanged until final apply."""

    original: dict[str, Any]
    current: dict[str, Any]

    @classmethod
    def from_options(cls, options: Mapping[str, Any]) -> OptionsDraft:
        original = deepcopy(dict(options))
        return cls(original=original, current=deepcopy(original))

    @property
    def dirty(self) -> bool:
        return self.current != self.original

    def update(self, values: Mapping[str, Any]) -> None:
        self.current.update(deepcopy(dict(values)))

    def discard(self) -> None:
        self.current.clear()
        self.current.update(deepcopy(self.original))

    def applied(self) -> dict[str, Any]:
        return deepcopy(self.current)
