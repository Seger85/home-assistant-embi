from __future__ import annotations

import logging
from collections import Counter
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import voluptuous as vol
from homeassistant.helpers import selector

from .const import (
    CONF_ALLOWED_DEVICE_IDS,
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_FLOW_ACTION,
    CONF_GLOBAL_PLAYER_MODE,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_ONLY_DURING_PLAYBACK,
    CONF_SELECTED_GROUP,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_UNRESOLVED_LEGACY_RULES,
    CONF_USER_MASTER_VISIBILITY,
    FLOW_ACTION_APPLY,
    FLOW_ACTION_BACK,
    PLAYER_MODE_ACTIVE_ONLY,
    PLAYER_MODE_PERSISTENT,
)
from .options_runtime import fresh_catalog, group_options, render_player_details
from .player_context import (
    ACTIVE_PLAYBACK_STATES,
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


def _localized_activity(
    value: datetime | None,
    *,
    german: bool,
    time_zone: str,
) -> str:
    """Return one compact mobile-safe activity fragment."""
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
    """Return unique single-line labels without entity or technical IDs."""
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


def _group_action_selector(*, german: bool) -> selector.SelectSelector:
    return _single(
        [
            {
                "value": FLOW_ACTION_APPLY,
                "label": "Gruppe übernehmen" if german else "Apply group",
            },
            {
                "value": FLOW_ACTION_BACK,
                "label": "< Zurück" if german else "< Back",
            },
        ]
    )


class DevicesOptionsMixin:
    """Canonical Home Assistant player configuration with preserved draft state."""

    async def async_step_ha_players(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        try:
            players, stats = await fresh_catalog(self)
        except Exception:
            _LOGGER.exception("Failed to load current EMBi player catalog")
            players = []
            stats = None
            errors["base"] = "cannot_connect"

        requested_technical = bool(
            (user_input or {}).get(
                CONF_TECHNICAL_ACCESS_VISIBILITY,
                self._draft_options.get(CONF_TECHNICAL_ACCESS_VISIBILITY, False),
            )
        )
        groups = group_options(
            players,
            german=self._is_de(),
            include_technical=requested_technical,
        )
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
                default=requested_technical,
            ): selector.BooleanSelector(),
        }
        if groups:
            fields[vol.Optional(CONF_SELECTED_GROUP)] = _single(groups)

        if user_input is not None and not errors:
            requested_auto_show = bool(user_input.get(CONF_AUTO_SHOW_NEW_PLAYERS, True))
            self._draft_options[CONF_GLOBAL_PLAYER_MODE] = (
                PLAYER_MODE_ACTIVE_ONLY
                if user_input.get(CONF_ONLY_DURING_PLAYBACK)
                else PLAYER_MODE_PERSISTENT
            )
            self._draft_options[CONF_AUTO_SHOW_NEW_PLAYERS] = requested_auto_show
            self._draft_options[CONF_TECHNICAL_ACCESS_VISIBILITY] = requested_technical
            if not requested_auto_show:
                allowed = {
                    str(value) for value in self._draft_options.get(CONF_ALLOWED_DEVICE_IDS, [])
                }
                allowed.update(player.player_key for player in players if player.visible_in_embi)
                self._draft_options[CONF_ALLOWED_DEVICE_IDS] = sorted(allowed)

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
        self._group_submitted = {}
        return await self.async_step_ha_players()

    async def async_step_player_group(self, user_input: dict[str, Any] | None = None):
        """Edit one group without blocking safe switches beside active playback."""
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
        submitted = dict(getattr(self, "_group_submitted", {}))
        requested = {
            player.player_key: bool(submitted.get(player.player_key, player.visible_in_embi))
            for _label, player in toggle_fields
        }
        if user_input is not None:
            requested = {
                player.player_key: bool(user_input.get(label, player.visible_in_embi))
                for label, player in toggle_fields
            }
            self._group_submitted = dict(requested)

        fields: dict[Any, Any] = {
            vol.Required(label, default=requested[player.player_key]): selector.BooleanSelector()
            for label, player in toggle_fields
        }
        fields[vol.Required(CONF_FLOW_ACTION, default=FLOW_ACTION_APPLY)] = _group_action_selector(
            german=self._is_de()
        )

        blockers = [
            player
            for player in group_players
            if not requested.get(player.player_key, player.visible_in_embi)
            and player.playback in ACTIVE_PLAYBACK_STATES
        ]

        if user_input is not None and not errors:
            action = user_input.get(CONF_FLOW_ACTION, FLOW_ACTION_APPLY)
            hidden = {
                str(value) for value in self._draft_options.get(CONF_HIDDEN_EXACT_PLAYERS, [])
            }
            group_keys = {player.player_key for player in group_players}
            safe_requested = dict(requested)
            for player in blockers:
                safe_requested[player.player_key] = True

            user_name = (
                self._selected_group.removeprefix(GROUP_USER_PREFIX)
                if self._selected_group.startswith(GROUP_USER_PREFIX)
                else None
            )
            any_visible = any(safe_requested.values())
            if user_name is not None:
                visibility = dict(self._draft_options.get(CONF_USER_MASTER_VISIBILITY, {}))
                visibility[user_name] = any_visible
                self._draft_options[CONF_USER_MASTER_VISIBILITY] = visibility
                hidden -= group_keys
                if any_visible:
                    hidden.update(key for key, visible in safe_requested.items() if not visible)
            elif self._selected_group == GROUP_TECHNICAL:
                # The master and exact player switches are independent.
                hidden -= group_keys
                hidden.update(key for key, visible in safe_requested.items() if not visible)
            else:
                hidden -= group_keys
                hidden.update(key for key, visible in safe_requested.items() if not visible)
            self._draft_options[CONF_HIDDEN_EXACT_PLAYERS] = sorted(hidden)

            if blockers and action != FLOW_ACTION_BACK:
                errors["base"] = "playback_protected_named"
            else:
                self._selected_group = None
                self._group_submitted = {}
                return await self.async_step_ha_players()

        group_name = next(
            (
                option["label"].rsplit(" · ", 1)[0]
                for option in group_options(
                    players,
                    german=self._is_de(),
                    include_technical=True,
                )
                if option["value"] == self._selected_group
            ),
            self._selected_group,
        )
        blocked_players = ", ".join(player.selector_label for player in blockers) or "-"
        return self.async_show_form(
            step_id="player_group",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                "group": str(group_name),
                "count": str(len(group_players)),
                "blocked_players": blocked_players,
            },
        )

    async def async_step_player_exceptions(self, user_input: dict[str, Any] | None = None):
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
        if user_input is not None:
            kept = {str(value) for value in user_input.get("kept_rules", unresolved)}
            self._draft_options[CONF_UNRESOLVED_LEGACY_RULES] = sorted(kept)
            return await self.async_step_ha_players()
        return self.async_show_form(
            step_id="older_rules",
            data_schema=vol.Schema(fields),
            description_placeholders={"count": str(len(unresolved))},
        )
