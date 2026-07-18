from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from homeassistant.helpers import selector

from .const import CONF_FLOW_ACTION, FLOW_ACTION_BACK, FLOW_ACTION_SAVE


def action_selector(options: Iterable[Mapping[str, str]]) -> selector.SelectSelector:
    """Return a frontend-serializable native list selector for flow actions."""
    normalized = [
        {"value": str(option["value"]), "label": str(option["label"])} for option in options
    ]
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=normalized,
            multiple=False,
            mode=selector.SelectSelectorMode.LIST,
        )
    )


def navigation_selector(
    *,
    german: bool,
    primary_label: str | None = None,
    primary_value: str = FLOW_ACTION_SAVE,
) -> selector.SelectSelector:
    """Return a non-persistent form action with a true back choice."""
    options: list[dict[str, str]] = []
    if primary_label is not None:
        options.append({"value": primary_value, "label": primary_label})
    options.append(
        {
            "value": FLOW_ACTION_BACK,
            "label": "\u2039 Zurück" if german else "\u2039 Back",
        }
    )
    return action_selector(options)


def back_requested(user_input: Mapping[str, Any] | None) -> bool:
    """Return whether the submitted non-persistent action is Back."""
    return bool(user_input) and user_input.get(CONF_FLOW_ACTION) == FLOW_ACTION_BACK
