from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from .api import EmbyApiError, EmbyDeviceRecord
from .cleanup import plan_device_cleanup
from .const import (
    AGE_PRESET_CUSTOM,
    AGE_PRESETS,
    CLEANUP_ACTION_MANAGE_HA_PLAYERS,
    CLEANUP_ACTION_MANUAL_CHECK,
    CONF_CLEANUP_ACTION,
    CONF_CONFIRM_SERVER_DELETION,
    CONF_DELETE_DEVICE_RECORD_IDS,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_AGE_DAYS,
    DEFAULT_REMOVE_HA_ENTITIES,
    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
    MAX_SERVER_CLEANUP_AGE_DAYS,
    MIN_SERVER_CLEANUP_AGE_DAYS,
)
from .helpers import age_days_from_input, age_preset_for_days, server_device_selector_options
from .maintenance import active_player_keys, async_run_manual_cleanup
from .options_runtime import fresh_catalog

_MANUAL_PRESET = "manual_age_preset"
_MANUAL_CUSTOM = "manual_custom_age_days"
_AUTO_PRESET = "automatic_age_preset"
_AUTO_CUSTOM = "automatic_custom_age_days"


def _age_preset() -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[*AGE_PRESETS, AGE_PRESET_CUSTOM],
            translation_key="cleanup_age_preset",
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _number() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=MIN_SERVER_CLEANUP_AGE_DAYS,
            max=MAX_SERVER_CLEANUP_AGE_DAYS,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _resolve(user_input: dict[str, Any], preset_key: str, custom_key: str) -> int:
    custom = user_input.get(custom_key)
    return age_days_from_input(
        str(user_input[preset_key]),
        int(custom) if custom is not None else None,
    )


class CleanupOptionsMixin:
    """Single combined Cleanup page with separate destructive operations."""

    async def async_step_cleanup(self, user_input: dict[str, Any] | None = None):
        manual_days = int(
            self._draft_options.get(
                CONF_SERVER_CLEANUP_AGE_DAYS, DEFAULT_SERVER_CLEANUP_AGE_DAYS
            )
        )
        automatic_days = int(
            self._draft_options.get(
                CONF_SERVER_AUTO_CLEANUP_AGE_DAYS, DEFAULT_SERVER_CLEANUP_AGE_DAYS
            )
        )
        errors: dict[str, str] = {}
        try:
            _players, stats = await fresh_catalog(self)
        except Exception:
            stats = None
            errors["base"] = "cannot_connect"

        fields: dict[Any, Any] = {
            vol.Required(
                CONF_SERVER_AUTO_CLEANUP_ENABLED,
                default=bool(
                    self._draft_options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)
                ),
            ): selector.BooleanSelector(),
            vol.Required(
                _AUTO_PRESET, default=age_preset_for_days(automatic_days)
            ): _age_preset(),
            vol.Optional(_AUTO_CUSTOM, default=automatic_days): _number(),
            vol.Required(
                CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
                default=bool(
                    self._draft_options.get(
                        CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
                        DEFAULT_REMOVE_HA_ENTITIES,
                    )
                ),
            ): selector.BooleanSelector(),
            vol.Required(
                _MANUAL_PRESET, default=age_preset_for_days(manual_days)
            ): _age_preset(),
            vol.Optional(_MANUAL_CUSTOM, default=manual_days): _number(),
        }
        if not self._dirty:
            fields[vol.Optional(CONF_CLEANUP_ACTION)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        CLEANUP_ACTION_MANUAL_CHECK,
                        CLEANUP_ACTION_MANAGE_HA_PLAYERS,
                    ],
                    translation_key="cleanup_action",
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )

        if user_input is not None and not errors:
            try:
                submitted_manual = _resolve(user_input, _MANUAL_PRESET, _MANUAL_CUSTOM)
                submitted_auto = _resolve(user_input, _AUTO_PRESET, _AUTO_CUSTOM)
            except (KeyError, TypeError, ValueError):
                errors["base"] = "invalid_age"
            else:
                before = dict(self._draft_options)
                self._draft_options[CONF_SERVER_CLEANUP_AGE_DAYS] = submitted_manual
                self._draft_options[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS] = submitted_auto
                self._draft_options[CONF_SERVER_AUTO_CLEANUP_ENABLED] = bool(
                    user_input.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)
                )
                self._draft_options[CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES] = bool(
                    user_input.get(
                        CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
                        DEFAULT_REMOVE_HA_ENTITIES,
                    )
                )
                action = user_input.get(CONF_CLEANUP_ACTION)
                if before != self._draft_options:
                    return await self.async_step_init()
                if action == CLEANUP_ACTION_MANUAL_CHECK:
                    return await self.async_step_server_history_check()
                if action == CLEANUP_ACTION_MANAGE_HA_PLAYERS:
                    return await self.async_step_manage_ha_players()
                return await self.async_step_init()

        report = self._runtime.maintenance_state.report
        server_count = stats.server_history_records if stats else 0
        ha_count = stats.ha_players if stats else 0
        return self.async_show_form(
            step_id="cleanup",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                "server_history": str(server_count),
                "ha_players": str(ha_count),
                "historical_difference": str(max(0, server_count - ha_count)),
                "removable": str(stats.removable_from_ha if stats else 0),
                "protected": str(stats.protected_playback if stats else 0),
                "last_status": report.status,
                "last_deleted": str(report.server_deleted),
                "last_protected": str(
                    report.skipped_active + report.registry_entities_protected
                ),
                "last_errors": str(report.server_failed),
                "next_run": report.next_run_at or "-",
            },
        )

    async def async_step_server_history_check(
        self, user_input: dict[str, Any] | None = None
    ):
        if self._dirty:
            return self.async_abort(reason="unsaved_changes")
        age_days = int(
            self._entry.options.get(
                CONF_SERVER_CLEANUP_AGE_DAYS, DEFAULT_SERVER_CLEANUP_AGE_DAYS
            )
        )
        errors: dict[str, str] = {}
        try:
            devices = await self._devices()
        except EmbyApiError:
            devices = []
            errors["base"] = "cannot_connect"
        plan = plan_device_cleanup(
            devices,
            now=dt_util.utcnow(),
            age_days=age_days,
            active_player_keys=active_player_keys(self.hass, self._entry),
        )
        candidates = {device.record_id: device for device in plan.candidates}
        if user_input is not None and not errors:
            if not candidates:
                return await self.async_step_cleanup()
            selected = [
                str(value) for value in user_input.get(CONF_DELETE_DEVICE_RECORD_IDS, [])
            ]
            if not selected:
                errors["base"] = "selection_required"
            elif any(record_id not in candidates for record_id in selected):
                errors["base"] = "invalid_selection"
            else:
                self._pending_cleanup_records = {
                    record_id: candidates[record_id] for record_id in selected
                }
                return await self.async_step_confirm_server_deletion()

        fields: dict[Any, Any] = {}
        if candidates:
            fields[vol.Optional(CONF_DELETE_DEVICE_RECORD_IDS, default=[])] = (
                selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": key, "label": label}
                            for key, label in server_device_selector_options(
                                plan.candidates
                            ).items()
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            )
        return self.async_show_form(
            step_id="server_history_check",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                "total": str(len(devices)),
                "candidates": str(len(plan.candidates)),
                "age_days": str(age_days),
                "active": str(len(plan.skipped_active)),
                "recent": str(len(plan.skipped_recent)),
                "without_activity": str(len(plan.skipped_without_activity)),
            },
        )

    async def async_step_confirm_server_deletion(
        self, user_input: dict[str, Any] | None = None
    ):
        if not self._pending_cleanup_records:
            return await self.async_step_server_history_check()
        errors: dict[str, str] = {}
        count = len(self._pending_cleanup_records)
        if user_input is not None:
            if not user_input.get(CONF_CONFIRM_SERVER_DELETION):
                errors["base"] = "confirmation_required"
            else:
                report, reload_needed = await async_run_manual_cleanup(
                    self.hass,
                    self._entry,
                    selected_record_ids=self._pending_cleanup_records,
                    age_days=int(
                        self._entry.options.get(
                            CONF_SERVER_CLEANUP_AGE_DAYS,
                            DEFAULT_SERVER_CLEANUP_AGE_DAYS,
                        )
                    ),
                    remove_ha_entities=False,
                )
                self._pending_cleanup_records = {}
                if reload_needed:
                    self.hass.async_create_task(
                        self.hass.config_entries.async_reload(self._entry.entry_id),
                        "Reload EMBi after manual server-history cleanup",
                    )
                return self.async_abort(
                    reason="server_cleanup_complete",
                    description_placeholders={
                        "server_deleted": str(report.server_deleted),
                        "server_failed": str(report.server_failed),
                    },
                )
        return self.async_show_form(
            step_id="confirm_server_deletion",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONFIRM_SERVER_DELETION, default=False
                    ): selector.BooleanSelector()
                }
            ),
            errors=errors,
            description_placeholders={"count": str(count)},
        )
