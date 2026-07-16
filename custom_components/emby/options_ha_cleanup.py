from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.helpers import selector

from .const import CONF_CONFIRM_HA_REMOVAL, CONF_SELECTED_HA_ENTITY_IDS
from .options_runtime import entity_options, fresh_catalog, render_player_rows
from .player_actions import async_remove_ha_players


class HomeAssistantCleanupOptionsMixin:
    """Safe Home Assistant player removal from the combined Cleanup area."""

    async def async_step_manage_ha_players(self, user_input: dict[str, Any] | None = None):
        if self._dirty:
            return self.async_abort(reason="unsaved_changes")
        errors: dict[str, str] = {}
        try:
            players, stats = await fresh_catalog(self)
        except Exception:
            players = []
            stats = None
            errors["base"] = "cannot_connect"

        removable = [
            player
            for player in players
            if player.registry_present and player.removable and player.entity_id
        ]
        protected = [
            player for player in players if player.registry_present and not player.removable
        ]
        fields: dict[Any, Any] = {}
        if removable:
            fields[vol.Optional(CONF_SELECTED_HA_ENTITY_IDS, default=[])] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=entity_options(removable),
                    multiple=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )

        if user_input is not None and not errors:
            selected = [str(value) for value in user_input.get(CONF_SELECTED_HA_ENTITY_IDS, [])]
            allowed = {player.entity_id for player in removable}
            if not removable:
                return await self.async_step_cleanup()
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
                "protected": str(len(protected)),
                "all_rows": render_player_rows(players),
                "protected_rows": render_player_rows(protected),
            },
        )

    async def async_step_confirm_ha_removal(self, user_input: dict[str, Any] | None = None):
        if not self._pending_ha_entity_ids:
            return await self.async_step_manage_ha_players()
        count = len(self._pending_ha_entity_ids)
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_CONFIRM_HA_REMOVAL):
                errors["base"] = "confirmation_required"
            else:
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
        return self.async_show_form(
            step_id="confirm_ha_removal",
            data_schema=vol.Schema(
                {vol.Required(CONF_CONFIRM_HA_REMOVAL, default=False): selector.BooleanSelector()}
            ),
            errors=errors,
            description_placeholders={"count": str(count)},
        )
