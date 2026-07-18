from __future__ import annotations

import logging
from collections import Counter
from typing import Any

import voluptuous as vol
from homeassistant.helpers import selector

from .const import (
    CONF_ALLOWED_DEVICE_IDS,
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_FLOW_ACTION,
    CONF_GLOBAL_PLAYER_MODE,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_ONLY_DURING_PLAYBACK,
    CONF_SEARCH_QUERY,
    CONF_SELECTED_GROUP,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_UNRESOLVED_LEGACY_RULES,
    CONF_USER_MASTER_VISIBILITY,
    PLAYER_MODE_ACTIVE_ONLY,
    PLAYER_MODE_PERSISTENT,
)
from .options_navigation import back_requested, navigation_selector
from .options_runtime import (
    fresh_catalog,
    group_options,
    player_options,
    render_player_details,
)
from .player_context import (
    ACTIVE_PLAYBACK_STATES,
    CLIENT_CLASS_TECHNICAL,
    GROUP_TECHNICAL,
    GROUP_USER_PREFIX,
    group_player_catalog,
)

_LOGGER = logging.getLogger(__name__)

_OLDER_RULES_GROUP = "older_rules"


def _multi(options: list[dict[str, str]]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            multiple=True,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _single(
    options: list[dict[str, str]], *, translation_key: str | None = None
) -> selector.SelectSelector:
    config: dict[str, Any] = {
        "options": options,
        "multiple": False,
        "mode": selector.SelectSelectorMode.DROPDOWN,
    }
    if translation_key is not None:
        config["translation_key"] = translation_key
    return selector.SelectSelector(selector.SelectSelectorConfig(**config))


def _page_selector(total_pages: int) -> selector.SelectSelector:
    return _single(
        [
            {"value": str(page), "label": f"{page} / {total_pages}"}
            for page in range(1, total_pages + 1)
        ]
    )


def _player_toggle_fields(players):
    """Return stable, unique and meaningful labels for native switches."""
    options = player_options(players)
    counts = Counter(option["label"] for option in options)
    seen: Counter[str] = Counter()
    by_key = {player.player_key: player for player in players}
    result = []
    for option in options:
        base = option["label"]
        player = by_key.get(option["value"])
        if player is None:
            continue
        seen[base] += 1
        label = base
        if counts[base] > 1:
            if player.users:
                label = f"{base} · {player.users[0]}"
            elif player.last_activity is not None:
                label = f"{base} · {player.last_activity.date().isoformat()}"
            if any(existing == label for existing, _player in result):
                label = f"{label} ({seen[base]})"
        result.append((label, player))
    return result


class DevicesOptionsMixin:
    """Compact Home Assistant player configuration with preserved draft state."""

    async def async_step_ha_players(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        try:
            players, stats = await fresh_catalog(self)
        except Exception:
            _LOGGER.exception("Failed to load current EMBi player catalog")
            players = []
            stats = None
            errors["base"] = "cannot_connect"

        groups = group_options(players, german=self._is_de())
        unresolved = [
            str(value) for value in self._draft_options.get(CONF_UNRESOLVED_LEGACY_RULES, [])
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
                default=self._draft_options.get(CONF_GLOBAL_PLAYER_MODE) == PLAYER_MODE_ACTIVE_ONLY,
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_AUTO_SHOW_NEW_PLAYERS,
                default=bool(self._draft_options.get(CONF_AUTO_SHOW_NEW_PLAYERS, True)),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_TECHNICAL_ACCESS_VISIBILITY,
                default=bool(self._draft_options.get(CONF_TECHNICAL_ACCESS_VISIBILITY, False)),
            ): selector.BooleanSelector(),
            vol.Optional(CONF_SEARCH_QUERY, default=self._search_query): selector.TextSelector(
                selector.TextSelectorConfig()
            ),
        }
        if groups:
            fields[vol.Optional(CONF_SELECTED_GROUP)] = _single(groups)
        fields[vol.Required(CONF_FLOW_ACTION, default="save")] = navigation_selector(
            german=self._is_de(),
            primary_label="Speichern & zurück" if self._is_de() else "Save & back",
        )

        if user_input is not None:
            if back_requested(user_input):
                return await self.async_step_init()
            if not errors:
                requested_auto_show = bool(user_input.get(CONF_AUTO_SHOW_NEW_PLAYERS, True))
                requested_technical = bool(user_input.get(CONF_TECHNICAL_ACCESS_VISIBILITY, False))
                active_technical = [
                    player
                    for player in players
                    if player.client_class == CLIENT_CLASS_TECHNICAL
                    and player.playback in ACTIVE_PLAYBACK_STATES
                ]
                technical_would_hide_active = (
                    bool(self._draft_options.get(CONF_TECHNICAL_ACCESS_VISIBILITY, False))
                    and not requested_technical
                    and bool(active_technical)
                )
                if technical_would_hide_active:
                    errors["base"] = "playback_protected"
                else:
                    self._draft_options[CONF_GLOBAL_PLAYER_MODE] = (
                        PLAYER_MODE_ACTIVE_ONLY
                        if user_input.get(CONF_ONLY_DURING_PLAYBACK)
                        else PLAYER_MODE_PERSISTENT
                    )
                    self._draft_options[CONF_AUTO_SHOW_NEW_PLAYERS] = requested_auto_show
                    self._draft_options[CONF_TECHNICAL_ACCESS_VISIBILITY] = requested_technical
                    if not requested_auto_show:
                        allowed = {
                            str(value)
                            for value in self._draft_options.get(CONF_ALLOWED_DEVICE_IDS, [])
                        }
                        allowed.update(
                            player.player_key for player in players if player.visible_in_embi
                        )
                        self._draft_options[CONF_ALLOWED_DEVICE_IDS] = sorted(allowed)
                    self._search_query = str(user_input.get(CONF_SEARCH_QUERY, "")).strip()
                    selected_group = user_input.get(CONF_SELECTED_GROUP)
                    if selected_group == _OLDER_RULES_GROUP:
                        return await self.async_step_older_rules()
                    if selected_group:
                        self._selected_group = str(selected_group)
                        return await self.async_step_player_group()
                    return await self.async_step_init()

        return self.async_show_form(
            step_id="ha_players",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                "ha_players": str(stats.ha_players if stats else 0),
                "playing": str(stats.protected_playback if stats else 0),
                "known_users": str(stats.known_users if stats else 0),
                "server_missing": str(stats.server_missing if stats else 0),
            },
        )

    async def async_step_back_to_ha_players(self, user_input: dict[str, Any] | None = None):
        self._selected_group = None
        self._selected_player_key = None
        return await self.async_step_ha_players()

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
        group_players = list(group_player_catalog(players).get(self._selected_group, []))
        toggle_fields = _player_toggle_fields(group_players)
        fields: dict[Any, Any] = {}
        for label, player in toggle_fields:
            fields[vol.Required(label, default=player.visible_in_embi)] = selector.BooleanSelector()
        fields[vol.Required(CONF_FLOW_ACTION, default="save")] = navigation_selector(
            german=self._is_de(),
            primary_label="Speichern & zurück" if self._is_de() else "Save & back",
        )

        if user_input is not None:
            if back_requested(user_input):
                return await self.async_step_back_to_ha_players()
            if not errors:
                requested = {
                    player.player_key: bool(user_input.get(label, player.visible_in_embi))
                    for label, player in toggle_fields
                }
                if any(
                    not requested.get(player.player_key, player.visible_in_embi)
                    and player.playback in ACTIVE_PLAYBACK_STATES
                    for player in group_players
                ):
                    errors["base"] = "playback_protected"
                else:
                    hidden = {
                        str(value)
                        for value in self._draft_options.get(CONF_HIDDEN_EXACT_PLAYERS, [])
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

    async def async_step_player_exceptions(self, user_input: dict[str, Any] | None = None):
        """Compatibility redirect; player switches now live directly on the group page."""
        return await self.async_step_player_group(user_input)

    async def async_step_player_details(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return await self.async_step_player_group()
        if not self._selected_group:
            return await self.async_step_ha_players()
        try:
            players, _stats = await fresh_catalog(self)
        except Exception:
            _LOGGER.exception("Failed to load current EMBi player catalog")
            players = []
        group_players = list(group_player_catalog(players).get(self._selected_group, []))
        selected_players = [
            player for player in group_players if player.player_key == self._selected_player_key
        ]
        return self.async_show_form(
            step_id="player_details",
            data_schema=vol.Schema({}),
            description_placeholders={
                "details": render_player_details(selected_players, german=self._is_de())
            },
        )

    async def async_step_older_rules(self, user_input: dict[str, Any] | None = None):
        unresolved = [
            str(value) for value in self._draft_options.get(CONF_UNRESOLVED_LEGACY_RULES, [])
        ]
        options = [
            {"value": value, "label": f"Legacy rule {index}"}
            for index, value in enumerate(unresolved, start=1)
        ]
        fields: dict[Any, Any] = {}
        if options:
            fields[vol.Optional("kept_rules", default=unresolved)] = _multi(options)
        fields[vol.Required(CONF_FLOW_ACTION, default="save")] = navigation_selector(
            german=self._is_de(),
            primary_label="Speichern & zurück" if self._is_de() else "Save & back",
        )
        if user_input is not None:
            if back_requested(user_input):
                return await self.async_step_ha_players()
            kept = {str(value) for value in user_input.get("kept_rules", unresolved)}
            self._draft_options[CONF_UNRESOLVED_LEGACY_RULES] = sorted(kept)
            return await self.async_step_ha_players()
        return self.async_show_form(
            step_id="older_rules",
            data_schema=vol.Schema(fields),
            description_placeholders={"count": str(len(unresolved))},
        )
