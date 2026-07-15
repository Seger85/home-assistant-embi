from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class OptionsDraft:
    """Mutable draft whose original value remains unchanged until final apply."""

    original: dict[str, Any]
    current: dict[str, Any]

    @classmethod
    def from_options(cls, options: Mapping[str, Any]) -> OptionsDraft:
        original = dict(options)
        return cls(original=original, current=dict(original))

    @property
    def dirty(self) -> bool:
        return self.current != self.original

    def update(self, values: Mapping[str, Any]) -> None:
        self.current.update(values)

    def discard(self) -> None:
        self.current.clear()
        self.current.update(self.original)

    def applied(self) -> dict[str, Any]:
        return dict(self.current)
