from __future__ import annotations

import logging
from collections import Counter
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import voluptuous as vol
from homeassistant.helpers import selector

from .const import (
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_USER_MASTER_VISIBILITY,
)
from .options_runtime import fresh_catalog, group_options
from .player_context import (
    ACTIVE_PLAYBACK_STATES,
    GROUP_TECHNICAL,
    GROUP_USER_PREFIX,
    PLAYBACK_UNKNOWN,
    group_player_catalog,
)

_LOGGER = logging.getLogger(__name__)


def _localized_activity(
    value: datetime | None,
    *,
    german: bool,
    time_zone: str,
) -> str:
    """Return one explicit mobile-safe activity fragment."""
    if value is None:
        return "zuletzt unbekannt" if german else "last access unknown"
    try:
        zone = ZoneInfo(time_zone)
    except ZoneInfoNotFoundError:
        zone = ZoneInfo("UTC")
    normalized = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    local = normalized.astimezone(zone)
    if german:
        return f"zuletzt {local:%d.%m.%Y %H:%M}"
    return f"last access {local:%Y-%m-%d %H:%M}"


def _sort_group_players(players):
    """Sort known activity oldest first and keep unknown timestamps last."""
    return sorted(
        players,
        key=lambda player: (
            player.last_activity is None,
            player.last_activity.timestamp() if player.last_activity is not None else 0,
            player.selector_label.casefold(),
        ),
    )


def _player_toggle_fields(players, *, german: bool, time_zone: str):
    """Return unique compact labels without entity or technical IDs."""
    seen: Counter[str] = Counter()
    result = []
    for player in players:
        primary = player.selector_label
        activity = _localized_activity(
            player.last_activity,
            german=german,
            time_zone=time_zone,
        )
        candidate = f"{primary} · {activity}"
        seen[candidate] += 1
        label = candidate if seen[candidate] == 1 else f"{primary} ({seen[candidate]}) · {activity}"
        result.append((label, player))
    return result


class MobilePlayerGroupMixin:
    """Override only the player-group page with mobile-safe labels."""

    async def async_step_player_group(self, user_input: dict[str, Any] | None = None):
        if not self._selected_group:
            return await self.async_step_ha_players()
        errors: dict[str, str] = {}
        try:
            players, _stats = await fresh_catalog(self)
        except Exception:
            _LOGGER.exception("Failed to load current EMBi player catalog")
            players = []
            errors["base"] = "cannot_connect"
        group_players = _sort_group_players(
            list(group_player_catalog(players).get(self._selected_group, []))
        )
        toggle_fields = _player_toggle_fields(
            group_players,
            german=self._is_de(),
            time_zone=self.hass.config.time_zone,
        )
        fields: dict[Any, Any] = {
            vol.Required(label, default=player.visible_in_embi): selector.BooleanSelector()
            for label, player in toggle_fields
        }

        if user_input is not None and not errors:
            requested = {
                player.player_key: bool(user_input.get(label, player.visible_in_embi))
                for label, player in toggle_fields
            }
            if any(
                not requested.get(player.player_key, player.visible_in_embi)
                and (
                    player.playback in ACTIVE_PLAYBACK_STATES or player.playback == PLAYBACK_UNKNOWN
                )
                for player in group_players
            ):
                errors["base"] = "playback_protected"
            else:
                hidden = {
                    str(value) for value in self._draft_options.get(CONF_HIDDEN_EXACT_PLAYERS, [])
                }
                group_keys = {player.player_key for player in group_players}
                user_name = (
                    self._selected_group.removeprefix(GROUP_USER_PREFIX)
                    if self._selected_group.startswith(GROUP_USER_PREFIX)
                    else None
                )
                any_visible = any(requested.values())
                if user_name is not None:
                    visibility = dict(self._draft_options.get(CONF_USER_MASTER_VISIBILITY, {}))
                    visibility[user_name] = any_visible
                    self._draft_options[CONF_USER_MASTER_VISIBILITY] = visibility
                    hidden -= group_keys
                    if any_visible:
                        hidden.update(key for key, visible in requested.items() if not visible)
                elif self._selected_group == GROUP_TECHNICAL:
                    self._draft_options[CONF_TECHNICAL_ACCESS_VISIBILITY] = any_visible
                    hidden -= group_keys
                    if any_visible:
                        hidden.update(key for key, visible in requested.items() if not visible)
                else:
                    hidden -= group_keys
                    hidden.update(key for key, visible in requested.items() if not visible)
                self._draft_options[CONF_HIDDEN_EXACT_PLAYERS] = sorted(hidden)
                self._selected_group = None
                return await self.async_step_ha_players()

        group_name = next(
            (
                option["label"].rsplit(" · ", 1)[0]
                for option in group_options(players, german=self._is_de())
                if option["value"] == self._selected_group
            ),
            self._selected_group,
        )
        return self.async_show_form(
            step_id="player_group",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                "group": str(group_name),
                "count": str(len(group_players)),
            },
        )
