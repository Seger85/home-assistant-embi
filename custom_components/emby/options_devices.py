from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.helpers import selector

from .const import (
    CONF_ALLOWED_DEVICE_IDS,
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_BACK,
    CONF_ENABLE_ENTITY_IDS,
    CONF_GLOBAL_PLAYER_MODE,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_HIDDEN_PAGE_PLAYER_KEYS,
    CONF_ONLY_DURING_PLAYBACK,
    CONF_PAGE,
    CONF_PLAYER_ACTION,
    CONF_SEARCH_QUERY,
    CONF_SELECTED_GROUP,
    CONF_SELECTED_PLAYER_KEY,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_UNRESOLVED_LEGACY_RULES,
    CONF_USER_MASTER_VISIBILITY,
    PLAYER_ACTION_DETAILS,
    PLAYER_ACTION_MANAGE_EXCEPTIONS,
    PLAYER_ACTION_REMOVE,
    PLAYER_ACTION_RESTORE,
    PLAYER_MODE_ACTIVE_ONLY,
    PLAYER_MODE_PERSISTENT,
    PLAYER_PAGE_SIZE,
)
from .options_runtime import (
    entity_options,
    fresh_catalog,
    group_options,
    page_slice,
    player_options,
    render_player_details,
)
from .player_context import (
    ACTIVE_PLAYBACK_STATES,
    CLIENT_CLASS_TECHNICAL,
    GROUP_USER_PREFIX,
    group_player_catalog,
)

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
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            multiple=False,
            translation_key=translation_key,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _page_selector(total_pages: int) -> selector.SelectSelector:
    return _single(
        [
            {"value": str(page), "label": f"{page} / {total_pages}"}
            for page in range(1, total_pages + 1)
        ]
    )


class DevicesOptionsMixin:
    """Compact Home Assistant player configuration with preserved draft state."""

    async def async_step_ha_players(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        try:
            players, stats = await fresh_catalog(self)
        except Exception:
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
        fields[vol.Optional(CONF_PLAYER_ACTION)] = _single(
            [PLAYER_ACTION_REMOVE, PLAYER_ACTION_RESTORE],
            translation_key="player_management_action",
        )
        fields[vol.Optional(CONF_BACK, default=False)] = selector.BooleanSelector()

        if user_input is not None:
            if user_input.get(CONF_BACK):
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
                        self._page_by_step["player_exceptions"] = 1
                        return await self.async_step_player_group()
                    action = user_input.get(CONF_PLAYER_ACTION)
                    if action == PLAYER_ACTION_REMOVE:
                        return await self.async_step_manage_ha_players()
                    if action == PLAYER_ACTION_RESTORE:
                        return await self.async_step_restore_ha_players()
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
            players = []
            errors["base"] = "cannot_connect"
        group_players = list(group_player_catalog(players).get(self._selected_group, []))
        if self._search_query:
            query = self._search_query.casefold()
            group_players = [player for player in group_players if query in player.search_text]

        fields: dict[Any, Any] = {}
        user_name: str | None = None
        if self._selected_group.startswith(GROUP_USER_PREFIX):
            user_name = self._selected_group.removeprefix(GROUP_USER_PREFIX)
            visibility = self._draft_options.get(CONF_USER_MASTER_VISIBILITY, {})
            fields[
                vol.Required(
                    "show_user_players",
                    default=(
                        visibility.get(user_name, True) if isinstance(visibility, dict) else True
                    ),
                )
            ] = selector.BooleanSelector()
        fields[vol.Required(CONF_PLAYER_ACTION)] = _single(
            [PLAYER_ACTION_MANAGE_EXCEPTIONS, PLAYER_ACTION_DETAILS],
            translation_key="player_group_action",
        )
        fields[vol.Optional(CONF_BACK, default=False)] = selector.BooleanSelector()

        if user_input is not None:
            if user_input.get(CONF_BACK):
                return await self.async_step_back_to_ha_players()
            if not errors:
                hide_user_group = user_name is not None and not bool(
                    user_input.get("show_user_players", True)
                )
                active_group = any(
                    player.playback in ACTIVE_PLAYBACK_STATES for player in group_players
                )
                if hide_user_group and active_group:
                    errors["base"] = "playback_protected"
                else:
                    if user_name is not None:
                        visibility = dict(self._draft_options.get(CONF_USER_MASTER_VISIBILITY, {}))
                        visibility[user_name] = bool(user_input.get("show_user_players", True))
                        self._draft_options[CONF_USER_MASTER_VISIBILITY] = visibility
                    action = user_input.get(CONF_PLAYER_ACTION)
                    if action == PLAYER_ACTION_MANAGE_EXCEPTIONS:
                        return await self.async_step_player_exceptions()
                    if action == PLAYER_ACTION_DETAILS:
                        return await self.async_step_player_details()
                    return await self.async_step_ha_players()

        group_name = user_name or next(
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
        if not self._selected_group:
            return await self.async_step_ha_players()
        errors: dict[str, str] = {}
        try:
            players, _stats = await fresh_catalog(self)
        except Exception:
            players = []
            errors["base"] = "cannot_connect"
        group_players = list(group_player_catalog(players).get(self._selected_group, []))
        query = self._search_query.casefold()
        if query:
            group_players = [player for player in group_players if query in player.search_text]

        requested_page = self._page_by_step.get("player_exceptions", 1)
        if user_input and user_input.get(CONF_PAGE):
            requested_page = int(user_input[CONF_PAGE])
        page_players, page, total_pages = page_slice(
            group_players, requested_page, page_size=PLAYER_PAGE_SIZE
        )
        self._page_by_step["player_exceptions"] = page
        hidden = {str(value) for value in self._draft_options.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
        fields: dict[Any, Any] = {
            vol.Optional(CONF_SEARCH_QUERY, default=self._search_query): selector.TextSelector(
                selector.TextSelectorConfig()
            )
        }
        if total_pages > 1:
            fields[vol.Optional(CONF_PAGE, default=str(page))] = _page_selector(total_pages)
        if page_players:
            fields[
                vol.Optional(
                    CONF_HIDDEN_PAGE_PLAYER_KEYS,
                    default=[
                        player.player_key for player in page_players if player.player_key in hidden
                    ],
                )
            ] = _multi(player_options(page_players))
        disabled = [
            player
            for player in page_players
            if player.registry_present and not player.registry_enabled and player.emby_present
        ]
        if disabled:
            fields[vol.Optional(CONF_ENABLE_ENTITY_IDS, default=[])] = _multi(
                entity_options(disabled)
            )
        fields[vol.Optional(CONF_BACK, default=False)] = selector.BooleanSelector()

        if user_input is not None:
            if user_input.get(CONF_BACK):
                return await self.async_step_player_group()
            if not errors:
                self._search_query = str(
                    user_input.get(CONF_SEARCH_QUERY, self._search_query)
                ).strip()
                selected_hidden = {
                    str(value) for value in user_input.get(CONF_HIDDEN_PAGE_PLAYER_KEYS, [])
                }
                page_keys = {player.player_key for player in page_players}
                hides_active = any(
                    player.playback in ACTIVE_PLAYBACK_STATES
                    and player.player_key in selected_hidden
                    for player in page_players
                )
                if hides_active:
                    errors["base"] = "playback_protected"
                else:
                    hidden -= page_keys
                    hidden.update(selected_hidden & page_keys)
                    self._draft_options[CONF_HIDDEN_EXACT_PLAYERS] = sorted(hidden)
                    self._pending_enable_entity_ids.update(
                        str(value) for value in user_input.get(CONF_ENABLE_ENTITY_IDS, [])
                    )
                    return await self.async_step_player_group()

        return self.async_show_form(
            step_id="player_exceptions",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                "count": str(len(group_players)),
                "page": str(page),
                "pages": str(total_pages),
            },
        )

    async def async_step_player_details(self, user_input: dict[str, Any] | None = None):
        if not self._selected_group:
            return await self.async_step_ha_players()
        errors: dict[str, str] = {}
        try:
            players, _stats = await fresh_catalog(self)
        except Exception:
            players = []
            errors["base"] = "cannot_connect"
        group_players = list(group_player_catalog(players).get(self._selected_group, []))
        by_key = {player.player_key: player for player in group_players}
        fields: dict[Any, Any] = {}
        if group_players:
            fields[
                vol.Optional(
                    CONF_SELECTED_PLAYER_KEY,
                    default=self._selected_player_key,
                )
            ] = _single(player_options(group_players))
        fields[vol.Optional(CONF_BACK, default=False)] = selector.BooleanSelector()

        if user_input is not None:
            if user_input.get(CONF_BACK):
                return await self.async_step_player_group()
            selected = user_input.get(CONF_SELECTED_PLAYER_KEY)
            if selected and str(selected) in by_key:
                self._selected_player_key = str(selected)
            elif selected:
                errors["base"] = "invalid_selection"

        selected_players = (
            [by_key[self._selected_player_key]] if self._selected_player_key in by_key else []
        )
        return self.async_show_form(
            step_id="player_details",
            data_schema=vol.Schema(fields),
            errors=errors,
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
        fields[vol.Optional(CONF_BACK, default=False)] = selector.BooleanSelector()
        if user_input is not None:
            if user_input.get(CONF_BACK):
                return await self.async_step_ha_players()
            kept = {str(value) for value in user_input.get("kept_rules", unresolved)}
            self._draft_options[CONF_UNRESOLVED_LEGACY_RULES] = sorted(kept)
            return await self.async_step_ha_players()
        return self.async_show_form(
            step_id="older_rules",
            data_schema=vol.Schema(fields),
            description_placeholders={"count": str(len(unresolved))},
        )
