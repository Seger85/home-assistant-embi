from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.helpers import selector

from .const import (
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_ENABLE_ENTITY_IDS,
    CONF_GLOBAL_PLAYER_MODE,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_ONLY_DURING_PLAYBACK,
    CONF_SEARCH_QUERY,
    CONF_SELECTED_GROUP,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_UNRESOLVED_LEGACY_RULES,
    CONF_USER_MASTER_VISIBILITY,
    CONF_VISIBLE_PLAYER_KEYS,
    PLAYER_MODE_ACTIVE_ONLY,
    PLAYER_MODE_PERSISTENT,
)
from .options_runtime import entity_options, fresh_catalog, group_options, player_options
from .player_context import ACTIVE_PLAYBACK_STATES, GROUP_USER_PREFIX, group_player_catalog

_OLDER_RULES_GROUP = "older_rules"


def _multi(options: list[dict[str, str]]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            multiple=True,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _single(options: list[dict[str, str]]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            multiple=False,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


class DevicesOptionsMixin:
    """User-oriented Devices & players draft flow."""

    async def async_step_devices_players(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        try:
            players, stats = await fresh_catalog(self)
        except Exception:
            players = []
            stats = None
            errors["base"] = "cannot_connect"

        groups = group_options(players, german=self._is_de())
        unresolved = [
            str(value)
            for value in self._draft_options.get(CONF_UNRESOLVED_LEGACY_RULES, [])
        ]
        if unresolved:
            groups.append(
                {
                    "value": _OLDER_RULES_GROUP,
                    "label": (
                        f"Ältere Regeln · {len(unresolved)}"
                        if self._is_de()
                        else f"Older rules · {len(unresolved)}"
                    ),
                }
            )
        fields: dict[Any, Any] = {
            vol.Required(
                CONF_ONLY_DURING_PLAYBACK,
                default=self._draft_options.get(CONF_GLOBAL_PLAYER_MODE)
                == PLAYER_MODE_ACTIVE_ONLY,
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_AUTO_SHOW_NEW_PLAYERS,
                default=bool(self._draft_options.get(CONF_AUTO_SHOW_NEW_PLAYERS, True)),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_TECHNICAL_ACCESS_VISIBILITY,
                default=bool(
                    self._draft_options.get(CONF_TECHNICAL_ACCESS_VISIBILITY, False)
                ),
            ): selector.BooleanSelector(),
            vol.Optional(CONF_SEARCH_QUERY, default=self._search_query): selector.TextSelector(
                selector.TextSelectorConfig()
            ),
        }
        if groups:
            fields[vol.Optional(CONF_SELECTED_GROUP)] = _single(groups)

        if user_input is not None and not errors:
            self._draft_options[CONF_GLOBAL_PLAYER_MODE] = (
                PLAYER_MODE_ACTIVE_ONLY
                if user_input.get(CONF_ONLY_DURING_PLAYBACK)
                else PLAYER_MODE_PERSISTENT
            )
            self._draft_options[CONF_AUTO_SHOW_NEW_PLAYERS] = bool(
                user_input.get(CONF_AUTO_SHOW_NEW_PLAYERS, True)
            )
            self._draft_options[CONF_TECHNICAL_ACCESS_VISIBILITY] = bool(
                user_input.get(CONF_TECHNICAL_ACCESS_VISIBILITY, False)
            )
            self._search_query = str(user_input.get(CONF_SEARCH_QUERY, "")).strip()
            selected_group = user_input.get(CONF_SELECTED_GROUP)
            if selected_group == _OLDER_RULES_GROUP:
                return await self.async_step_older_rules()
            if selected_group:
                self._selected_group = str(selected_group)
                return await self.async_step_player_group()
            return await self.async_step_init()

        return self.async_show_form(
            step_id="devices_players",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                "ha_players": str(stats.ha_players if stats else 0),
                "playing": str(stats.protected_playback if stats else 0),
                "known_users": str(stats.known_users if stats else 0),
                "groups": "\n".join(option["label"] for option in groups) or "-",
            },
        )

    async def async_step_player_group(self, user_input: dict[str, Any] | None = None):
        if not self._selected_group:
            return await self.async_step_devices_players()
        errors: dict[str, str] = {}
        try:
            players, _stats = await fresh_catalog(self)
        except Exception:
            players = []
            errors["base"] = "cannot_connect"
        group_players = list(group_player_catalog(players).get(self._selected_group, []))
        if self._search_query:
            query = self._search_query.casefold()
            group_players = [player for player in group_players if query in player.search_text]

        hidden = {str(value) for value in self._draft_options.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
        fields: dict[Any, Any] = {
            vol.Optional(
                CONF_VISIBLE_PLAYER_KEYS,
                default=[
                    player.player_key
                    for player in group_players
                    if player.player_key not in hidden
                ],
            ): _multi(player_options(group_players))
        }
        user_name: str | None = None
        if self._selected_group.startswith(GROUP_USER_PREFIX):
            user_name = self._selected_group.removeprefix(GROUP_USER_PREFIX)
            visibility = self._draft_options.get(CONF_USER_MASTER_VISIBILITY, {})
            fields[
                vol.Required(
                    "show_user_players",
                    default=(
                        visibility.get(user_name, True)
                        if isinstance(visibility, dict)
                        else True
                    ),
                )
            ] = selector.BooleanSelector()
        disabled = [
            player
            for player in group_players
            if player.registry_present and not player.registry_enabled and player.emby_present
        ]
        if disabled:
            fields[vol.Optional(CONF_ENABLE_ENTITY_IDS, default=[])] = _multi(
                entity_options(disabled)
            )

        if user_input is not None and not errors:
            selected = {
                str(value) for value in user_input.get(CONF_VISIBLE_PLAYER_KEYS, [])
            }
            if any(
                player.playback in ACTIVE_PLAYBACK_STATES
                and player.player_key not in selected
                for player in group_players
            ):
                errors["base"] = "playback_protected"
            else:
                group_keys = {player.player_key for player in group_players}
                hidden -= group_keys
                hidden.update(group_keys - selected)
                self._draft_options[CONF_HIDDEN_EXACT_PLAYERS] = sorted(hidden)
                if user_name is not None:
                    visibility = dict(
                        self._draft_options.get(CONF_USER_MASTER_VISIBILITY, {})
                    )
                    visibility[user_name] = bool(user_input.get("show_user_players", True))
                    self._draft_options[CONF_USER_MASTER_VISIBILITY] = visibility
                self._pending_enable_entity_ids.update(
                    str(value) for value in user_input.get(CONF_ENABLE_ENTITY_IDS, [])
                )
                self._selected_group = None
                return await self.async_step_devices_players()

        return self.async_show_form(
            step_id="player_group",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                "group": self._selected_group,
                "player_rows": "\n\n".join(
                    player.selector_label for player in group_players
                )
                or "-",
            },
        )

    async def async_step_older_rules(self, user_input: dict[str, Any] | None = None):
        unresolved = [
            str(value)
            for value in self._draft_options.get(CONF_UNRESOLVED_LEGACY_RULES, [])
        ]
        options = [
            {"value": value, "label": f"Legacy rule {index}"}
            for index, value in enumerate(unresolved, start=1)
        ]
        if user_input is not None:
            kept = {str(value) for value in user_input.get("kept_rules", [])}
            self._draft_options[CONF_UNRESOLVED_LEGACY_RULES] = sorted(kept)
            return await self.async_step_devices_players()
        return self.async_show_form(
            step_id="older_rules",
            data_schema=vol.Schema(
                {vol.Optional("kept_rules", default=unresolved): _multi(options)}
            ),
            description_placeholders={"count": str(len(unresolved))},
        )
