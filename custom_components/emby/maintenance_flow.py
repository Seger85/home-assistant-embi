from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from .api import EmbyApiError
from .cleanup import plan_device_cleanup
from .const import (
    AGE_PRESET_CUSTOM,
    AGE_PRESETS,
    CONF_AGE_PRESET,
    CONF_CONFIRM_AUTO_CLEANUP,
    CONF_CONFIRM_DELETE,
    CONF_CONFIRMATION_TEXT,
    CONF_CUSTOM_AGE_DAYS,
    CONF_DELETE_DEVICE_RECORD_IDS,
    CONF_REMOVE_DELETED_HA_ENTITIES,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_AGE_DAYS,
    CONF_SERVER_CLEANUP_ENABLED,
    DEFAULT_REMOVE_HA_ENTITIES,
    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
    MAX_SERVER_CLEANUP_AGE_DAYS,
    MIN_SERVER_CLEANUP_AGE_DAYS,
)
from .helpers import age_days_from_input, age_preset_for_days, server_device_selector_options
from .maintenance import active_player_keys, async_run_manual_cleanup


def _age_preset_selector() -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[*AGE_PRESETS, AGE_PRESET_CUSTOM],
            translation_key="cleanup_age_preset",
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _custom_age_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=MIN_SERVER_CLEANUP_AGE_DAYS,
            max=MAX_SERVER_CLEANUP_AGE_DAYS,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _age_schema(current_days: int, extra: dict[Any, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_AGE_PRESET,
                default=age_preset_for_days(current_days),
            ): _age_preset_selector(),
            vol.Optional(
                CONF_CUSTOM_AGE_DAYS,
                default=current_days,
            ): _custom_age_selector(),
            **extra,
        }
    )


def _resolve_age(user_input: dict[str, Any]) -> int:
    return age_days_from_input(
        str(user_input[CONF_AGE_PRESET]),
        int(user_input[CONF_CUSTOM_AGE_DAYS])
        if user_input.get(CONF_CUSTOM_AGE_DAYS) is not None
        else None,
    )


class ServerMaintenanceOptionsMixin:
    """Draft settings and separately confirmed destructive maintenance actions."""

    async def async_step_server_cleanup_settings(self, user_input: dict[str, Any] | None = None):
        current_days = int(
            self._draft_options.get(
                CONF_SERVER_CLEANUP_AGE_DAYS,
                DEFAULT_SERVER_CLEANUP_AGE_DAYS,
            )
        )
        errors: dict[str, str] = {}
        schema = _age_schema(
            current_days,
            {
                vol.Required(
                    CONF_SERVER_CLEANUP_ENABLED,
                    default=self._draft_options.get(CONF_SERVER_CLEANUP_ENABLED, False),
                ): selector.BooleanSelector()
            },
        )
        if user_input is not None:
            try:
                age_days = _resolve_age(user_input)
            except (TypeError, ValueError):
                errors["base"] = "invalid_age"
            else:
                enabled = bool(user_input.get(CONF_SERVER_CLEANUP_ENABLED, False))
                self._draft_options[CONF_SERVER_CLEANUP_ENABLED] = enabled
                self._draft_options[CONF_SERVER_CLEANUP_AGE_DAYS] = age_days
                if not enabled:
                    self._draft_options[CONF_SERVER_AUTO_CLEANUP_ENABLED] = False
                return await self.async_step_init()
        return self.async_show_form(
            step_id="server_cleanup_settings",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_server_auto_cleanup_settings(
        self, user_input: dict[str, Any] | None = None
    ):
        current_days = int(
            self._draft_options.get(
                CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
                DEFAULT_SERVER_CLEANUP_AGE_DAYS,
            )
        )
        errors: dict[str, str] = {}
        schema = _age_schema(
            current_days,
            {
                vol.Required(
                    CONF_SERVER_AUTO_CLEANUP_ENABLED,
                    default=self._draft_options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
                    default=self._draft_options.get(
                        CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
                        DEFAULT_REMOVE_HA_ENTITIES,
                    ),
                ): selector.BooleanSelector(),
            },
        )
        if user_input is not None:
            if not self._draft_options.get(CONF_SERVER_CLEANUP_ENABLED, False):
                errors["base"] = "server_cleanup_disabled"
            else:
                try:
                    age_days = _resolve_age(user_input)
                except (TypeError, ValueError):
                    errors["base"] = "invalid_age"
                else:
                    submitted = {
                        CONF_SERVER_AUTO_CLEANUP_ENABLED: bool(
                            user_input.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)
                        ),
                        CONF_SERVER_AUTO_CLEANUP_AGE_DAYS: age_days,
                        CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES: bool(
                            user_input.get(
                                CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
                                DEFAULT_REMOVE_HA_ENTITIES,
                            )
                        ),
                    }
                    enabling = submitted[CONF_SERVER_AUTO_CLEANUP_ENABLED] and not bool(
                        self._draft_options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)
                    )
                    if enabling:
                        self._pending_auto_settings = submitted
                        return await self.async_step_server_auto_cleanup_confirm()
                    self._draft_options.update(submitted)
                    return await self.async_step_init()
        return self.async_show_form(
            step_id="server_auto_cleanup_settings",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_server_auto_cleanup_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        if self._pending_auto_settings is None:
            return await self.async_step_server_auto_cleanup_settings()
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_CONFIRM_AUTO_CLEANUP):
                errors["base"] = "confirmation_required"
            else:
                self._draft_options.update(self._pending_auto_settings)
                self._pending_auto_settings = None
                return await self.async_step_init()
        return self.async_show_form(
            step_id="server_auto_cleanup_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONFIRM_AUTO_CLEANUP,
                        default=False,
                    ): selector.BooleanSelector()
                }
            ),
            errors=errors,
        )

    async def async_step_server_cleanup(self, user_input: dict[str, Any] | None = None):
        if self._dirty:
            return self.async_abort(reason="unsaved_changes")
        if not self._entry.options.get(CONF_SERVER_CLEANUP_ENABLED, False):
            return self.async_abort(reason="server_cleanup_disabled")

        age_days = int(
            self._entry.options.get(
                CONF_SERVER_CLEANUP_AGE_DAYS,
                DEFAULT_SERVER_CLEANUP_AGE_DAYS,
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
        schema = vol.Schema(
            {
                vol.Optional(CONF_DELETE_DEVICE_RECORD_IDS, default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": key, "label": label}
                            for key, label in server_device_selector_options(plan.candidates).items()
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_REMOVE_DELETED_HA_ENTITIES,
                    default=DEFAULT_REMOVE_HA_ENTITIES,
                ): selector.BooleanSelector(),
            }
        )
        if user_input is not None and not errors:
            selected = list(user_input.get(CONF_DELETE_DEVICE_RECORD_IDS, []))
            if not selected:
                errors["base"] = "selection_required"
            elif any(record_id not in candidates for record_id in selected):
                errors["base"] = "invalid_selection"
            else:
                self._pending_cleanup_records = {
                    record_id: candidates[record_id] for record_id in selected
                }
                self._pending_remove_ha_entities = bool(
                    user_input.get(
                        CONF_REMOVE_DELETED_HA_ENTITIES,
                        DEFAULT_REMOVE_HA_ENTITIES,
                    )
                )
                return await self.async_step_server_cleanup_confirm()

        return self.async_show_form(
            step_id="server_cleanup",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "count": str(len(plan.candidates)),
                "age_days": str(age_days),
                "active_count": str(len(plan.skipped_active)),
                "unknown_count": str(len(plan.skipped_without_activity)),
            },
        )

    async def async_step_server_cleanup_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        if not self._pending_cleanup_records:
            return await self.async_step_server_cleanup()
        count = len(self._pending_cleanup_records)
        phrase = f"LÖSCHEN {count}" if self._is_de() else f"DELETE {count}"
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_CONFIRM_DELETE):
                errors["base"] = "confirmation_required"
            elif str(user_input.get(CONF_CONFIRMATION_TEXT, "")).strip() != phrase:
                errors["base"] = "confirmation_text_mismatch"
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
                    remove_ha_entities=self._pending_remove_ha_entities,
                )
                self._pending_cleanup_records = {}
                if reload_needed:
                    self.hass.async_create_task(
                        self.hass.config_entries.async_reload(self._entry.entry_id),
                        "Reload EMBi after manual device cleanup",
                    )
                return self.async_abort(
                    reason="server_cleanup_complete",
                    description_placeholders={
                        "server_deleted": str(report.server_deleted),
                        "server_failed": str(report.server_failed),
                        "registry_queued": str(report.registry_keys_queued),
                        "registry_removed": str(report.registry_entities_removed),
                    },
                )
        return self.async_show_form(
            step_id="server_cleanup_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONFIRM_DELETE,
                        default=False,
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_CONFIRMATION_TEXT,
                        default="",
                    ): selector.TextSelector(),
                }
            ),
            errors=errors,
            description_placeholders={"count": str(count), "phrase": phrase},
        )
