from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.helpers import selector

from .const import (
    CONF_FLOW_ACTION,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_PAGE,
    CONF_SEARCH_QUERY,
    CONF_SELECTED_HA_ENTITY_IDS,
    CONF_SELECTED_RESTORE_KEYS,
    FLOW_ACTION_BACK,
    FLOW_ACTION_EXECUTE,
    PLAYER_PAGE_SIZE,
)
from .options_navigation import action_selector, back_requested, navigation_selector
from .options_runtime import entity_options, fresh_catalog, page_slice, player_options
from .player_actions import async_remove_ha_players, async_restore_players

_LOGGER = logging.getLogger(__name__)


def _multi(options: list[dict[str, str]]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            multiple=True,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _page_selector(total_pages: int) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": str(page), "label": f"{page} / {total_pages}"}
                for page in range(1, total_pages + 1)
            ],
            multiple=False,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


class HomeAssistantCleanupOptionsMixin:
    """Safe Home Assistant player removal and restoration in the player area."""

    async def async_step_manage_ha_players(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        try:
            players, stats = await fresh_catalog(self)
        except Exception:
            _LOGGER.exception("Failed to load current EMBi player catalog")
            players = []
            stats = None
            errors["base"] = "cannot_connect"

        query = self._search_query.casefold()
        removable = [
            player
            for player in players
            if player.registry_present and player.removable and player.entity_id
        ]
        if query:
            removable = [player for player in removable if query in player.search_text]
        if self._dirty and "base" not in errors:
            errors["base"] = "unsaved_changes"

        requested_page = self._page_by_step.get("manage_ha_players", 1)
        if user_input and user_input.get(CONF_PAGE):
            requested_page = int(user_input[CONF_PAGE])
        page_players, page, total_pages = page_slice(
            removable, requested_page, page_size=PLAYER_PAGE_SIZE
        )
        self._page_by_step["manage_ha_players"] = page

        fields: dict[Any, Any] = {
            vol.Optional(CONF_SEARCH_QUERY, default=self._search_query): selector.TextSelector(
                selector.TextSelectorConfig()
            )
        }
        if total_pages > 1:
            fields[vol.Optional(CONF_PAGE, default=str(page))] = _page_selector(total_pages)
        if page_players and not self._dirty:
            fields[vol.Optional(CONF_SELECTED_HA_ENTITY_IDS, default=[])] = _multi(
                entity_options(page_players)
            )
        fields[vol.Required(CONF_FLOW_ACTION, default="save")] = navigation_selector(
            german=self._is_de(),
            primary_label="Weiter" if self._is_de() else "Continue",
        )

        if user_input is not None:
            if back_requested(user_input):
                return await self.async_step_ha_players()
            self._search_query = str(user_input.get(CONF_SEARCH_QUERY, self._search_query)).strip()
            if not errors:
                selected = [str(value) for value in user_input.get(CONF_SELECTED_HA_ENTITY_IDS, [])]
                allowed = {player.entity_id for player in page_players}
                if not selected:
                    errors["base"] = "selection_required"
                elif any(entity_id not in allowed for entity_id in selected):
                    errors["base"] = "invalid_selection"
                else:
                    self._pending_ha_entity_ids = selected
                    return await self.async_step_confirm_ha_removal()

        return self.async_show_form(
            step_id="manage_ha_players",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                "ha_players": str(stats.ha_players if stats else 0),
                "removable": str(len(removable)),
                "protected": str(
                    sum(player.registry_present and not player.removable for player in players)
                ),
                "server_missing": str(sum(player.server_missing for player in players)),
                "page": str(page),
                "pages": str(total_pages),
            },
        )

    async def async_step_confirm_ha_removal(self, user_input: dict[str, Any] | None = None):
        if not self._pending_ha_entity_ids:
            return await self.async_step_manage_ha_players()
        if user_input is not None:
            action = user_input.get(CONF_FLOW_ACTION)
            if action == FLOW_ACTION_BACK:
                return await self.async_step_back_to_manage_ha_players()
            if action == FLOW_ACTION_EXECUTE:
                return await self.async_step_execute_ha_removal()
        return self.async_show_form(
            step_id="confirm_ha_removal",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FLOW_ACTION): action_selector(
                        [
                            {
                                "value": FLOW_ACTION_EXECUTE,
                                "label": (
                                    f"{len(self._pending_ha_entity_ids)} HA-Player entfernen"
                                    if self._is_de()
                                    else f"Remove {len(self._pending_ha_entity_ids)} HA players"
                                ),
                            },
                            {
                                "value": FLOW_ACTION_BACK,
                                "label": "\u2039 Zurück" if self._is_de() else "\u2039 Back",
                            },
                        ]
                    )
                }
            ),
            description_placeholders={"count": str(len(self._pending_ha_entity_ids))},
        )

    async def async_step_back_to_manage_ha_players(self, user_input: dict[str, Any] | None = None):
        self._pending_ha_entity_ids = []
        return await self.async_step_manage_ha_players()

    async def async_step_execute_ha_removal(self, user_input: dict[str, Any] | None = None):
        if not self._pending_ha_entity_ids:
            return await self.async_step_manage_ha_players()
        result = await async_remove_ha_players(
            self.hass,
            self._entry,
            self._pending_ha_entity_ids,
        )
        self._pending_ha_entity_ids = []
        return self.async_abort(
            reason="ha_player_removal_complete",
            description_placeholders={
                "requested": str(result.requested),
                "removed": str(len(result.succeeded)),
                "protected": str(len(result.protected)),
                "failed": str(len(result.failed)),
            },
        )

    async def async_step_restore_ha_players(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        try:
            players, _stats = await fresh_catalog(self)
        except Exception:
            _LOGGER.exception("Failed to load current EMBi player catalog")
            players = []
            errors["base"] = "cannot_connect"
        if self._dirty and "base" not in errors:
            errors["base"] = "unsaved_changes"

        hidden = {str(value) for value in self._entry.options.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
        candidates = [player for player in players if player.player_key in hidden]
        query = self._search_query.casefold()
        if query:
            candidates = [player for player in candidates if query in player.search_text]
        requested_page = self._page_by_step.get("restore_ha_players", 1)
        if user_input and user_input.get(CONF_PAGE):
            requested_page = int(user_input[CONF_PAGE])
        page_players, page, total_pages = page_slice(
            candidates, requested_page, page_size=PLAYER_PAGE_SIZE
        )
        self._page_by_step["restore_ha_players"] = page

        fields: dict[Any, Any] = {
            vol.Optional(CONF_SEARCH_QUERY, default=self._search_query): selector.TextSelector(
                selector.TextSelectorConfig()
            )
        }
        if total_pages > 1:
            fields[vol.Optional(CONF_PAGE, default=str(page))] = _page_selector(total_pages)
        if page_players and not self._dirty:
            fields[vol.Optional(CONF_SELECTED_RESTORE_KEYS, default=[])] = _multi(
                player_options(page_players)
            )
        fields[vol.Required(CONF_FLOW_ACTION, default="save")] = navigation_selector(
            german=self._is_de(),
            primary_label="Weiter" if self._is_de() else "Continue",
        )

        if user_input is not None:
            if back_requested(user_input):
                return await self.async_step_ha_players()
            self._search_query = str(user_input.get(CONF_SEARCH_QUERY, self._search_query)).strip()
            if not errors:
                selected = [str(value) for value in user_input.get(CONF_SELECTED_RESTORE_KEYS, [])]
                allowed = {player.player_key for player in page_players}
                if not selected:
                    errors["base"] = "selection_required"
                elif any(key not in allowed for key in selected):
                    errors["base"] = "invalid_selection"
                else:
                    result = await async_restore_players(
                        self.hass,
                        self._entry,
                        selected,
                    )
                    return self.async_abort(
                        reason="ha_player_restore_complete",
                        description_placeholders={
                            "requested": str(result.requested),
                            "restored": str(len(result.succeeded)),
                            "failed": str(len(result.failed)),
                        },
                    )

        return self.async_show_form(
            step_id="restore_ha_players",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                "candidates": str(len(candidates)),
                "page": str(page),
                "pages": str(total_pages),
            },
        )
