from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import voluptuous as vol
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from .api import EmbyApiError, EmbyDeviceRecord
from .cleanup import plan_device_cleanup
from .const import (
    AGE_PRESET_CUSTOM,
    AGE_PRESETS,
    CONF_DELETE_DEVICE_RECORD_IDS,
    CONF_FLOW_ACTION,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_AGE_DAYS,
    DEFAULT_REMOVE_HA_ENTITIES,
    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
    FLOW_ACTION_BACK,
    FLOW_ACTION_EXECUTE,
    FLOW_ACTION_OPEN_AUTOMATIC,
    FLOW_ACTION_OPEN_HISTORY,
    FLOW_ACTION_OPEN_LAST_RUN,
    MAX_SERVER_CLEANUP_AGE_DAYS,
    MIN_SERVER_CLEANUP_AGE_DAYS,
)
from .helpers import (
    age_days_from_input,
    age_preset_for_days,
    server_device_confirmation_details,
    server_device_selector_options,
)
from .maintenance import active_player_keys, async_run_manual_cleanup
from .options_navigation import action_selector, back_requested, navigation_selector

_MANUAL_PRESET = "manual_age_preset"
_MANUAL_CUSTOM = "manual_custom_age_days"
_AUTO_PRESET = "automatic_age_preset"
_AUTO_CUSTOM = "automatic_custom_age_days"

_LOGGER = logging.getLogger(__name__)


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


def _multi(options: list[dict[str, str]]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            multiple=True,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _resolve(user_input: dict[str, Any], preset_key: str, custom_key: str) -> int:
    custom = user_input.get(custom_key)
    return age_days_from_input(
        str(user_input[preset_key]),
        int(custom) if custom is not None else None,
    )


class CleanupOptionsMixin:
    """Separated Emby-server cleanup settings, preview and status pages."""

    async def async_step_server_cleanup(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            action = user_input.get(CONF_FLOW_ACTION)
            if action == FLOW_ACTION_OPEN_AUTOMATIC:
                return await self.async_step_automatic_cleanup()
            if action == FLOW_ACTION_OPEN_HISTORY:
                return await self.async_step_server_history_check()
            if action == FLOW_ACTION_OPEN_LAST_RUN:
                return await self.async_step_last_cleanup_run()
            if action == FLOW_ACTION_BACK:
                return await self.async_step_init()
        return self.async_show_form(
            step_id="server_cleanup",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FLOW_ACTION): action_selector(
                        [
                            {
                                "value": FLOW_ACTION_OPEN_AUTOMATIC,
                                "label": (
                                    "Automatische Bereinigung"
                                    if self._is_de()
                                    else "Automatic cleanup"
                                ),
                            },
                            {
                                "value": FLOW_ACTION_OPEN_HISTORY,
                                "label": (
                                    "Jetzt auf alte Einträge prüfen"
                                    if self._is_de()
                                    else "Check for old records now"
                                ),
                            },
                            {
                                "value": FLOW_ACTION_OPEN_LAST_RUN,
                                "label": (
                                    "Letzter Bereinigungslauf"
                                    if self._is_de()
                                    else "Last cleanup run"
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
        )

    async def async_step_back_to_server_cleanup(self, user_input: dict[str, Any] | None = None):
        self._pending_cleanup_records = {}
        self._pending_cleanup_age_days = None
        return await self.async_step_server_cleanup()

    async def async_step_automatic_cleanup(self, user_input: dict[str, Any] | None = None):
        automatic_days = int(
            self._draft_options.get(
                CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
                DEFAULT_SERVER_CLEANUP_AGE_DAYS,
            )
        )
        preset = self._automatic_age_preset or age_preset_for_days(automatic_days)
        if user_input and user_input.get(_AUTO_PRESET):
            preset = str(user_input[_AUTO_PRESET])
            self._automatic_age_preset = preset

        errors: dict[str, str] = {}
        fields: dict[Any, Any] = {
            vol.Required(
                CONF_SERVER_AUTO_CLEANUP_ENABLED,
                default=bool(self._draft_options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)),
            ): selector.BooleanSelector(),
            vol.Required(_AUTO_PRESET, default=preset): _age_preset(),
        }
        if preset == AGE_PRESET_CUSTOM:
            fields[vol.Required(_AUTO_CUSTOM, default=automatic_days)] = _number()
        fields[
            vol.Required(
                CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
                default=bool(
                    self._draft_options.get(
                        CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
                        DEFAULT_REMOVE_HA_ENTITIES,
                    )
                ),
            )
        ] = selector.BooleanSelector()
        fields[vol.Required(CONF_FLOW_ACTION, default="save")] = navigation_selector(
            german=self._is_de(),
            primary_label="Übernehmen" if self._is_de() else "Apply",
        )

        if user_input is not None:
            if back_requested(user_input):
                return await self.async_step_server_cleanup()
            try:
                submitted_auto = _resolve(user_input, _AUTO_PRESET, _AUTO_CUSTOM)
            except (KeyError, TypeError, ValueError):
                errors["base"] = "invalid_age"
            else:
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
                self._automatic_age_preset = age_preset_for_days(submitted_auto)
                return await self.async_step_server_cleanup()

        return self.async_show_form(
            step_id="automatic_cleanup",
            data_schema=vol.Schema(fields),
            errors=errors,
        )

    async def async_step_server_history_check(self, user_input: dict[str, Any] | None = None):
        manual_days = int(
            self._draft_options.get(
                CONF_SERVER_CLEANUP_AGE_DAYS,
                DEFAULT_SERVER_CLEANUP_AGE_DAYS,
            )
        )
        preset = self._manual_age_preset or age_preset_for_days(manual_days)
        if user_input and user_input.get(_MANUAL_PRESET):
            preset = str(user_input[_MANUAL_PRESET])
            self._manual_age_preset = preset

        errors: dict[str, str] = {}
        try:
            devices = await self._devices()
        except EmbyApiError:
            _LOGGER.exception("Failed to load Emby server-history records")
            devices = []
            errors["base"] = "cannot_connect"

        age_days = manual_days
        if user_input is not None and not back_requested(user_input):
            try:
                age_days = _resolve(user_input, _MANUAL_PRESET, _MANUAL_CUSTOM)
            except (KeyError, TypeError, ValueError):
                errors["base"] = "invalid_age"
            else:
                self._draft_options[CONF_SERVER_CLEANUP_AGE_DAYS] = age_days
                self._manual_age_preset = age_preset_for_days(age_days)

        plan = plan_device_cleanup(
            devices,
            now=dt_util.utcnow(),
            age_days=age_days,
            active_player_keys=active_player_keys(self.hass, self._entry),
        )
        candidates: dict[str, EmbyDeviceRecord] = {
            device.record_id: device for device in plan.candidates
        }

        fields: dict[Any, Any] = {vol.Required(_MANUAL_PRESET, default=preset): _age_preset()}
        if preset == AGE_PRESET_CUSTOM:
            fields[vol.Required(_MANUAL_CUSTOM, default=age_days)] = _number()
        if candidates:
            fields[vol.Optional(CONF_DELETE_DEVICE_RECORD_IDS, default=[])] = _multi(
                [
                    {"value": key, "label": label}
                    for key, label in server_device_selector_options(
                        plan.candidates,
                        time_zone=self.hass.config.time_zone,
                        german=self._is_de(),
                    ).items()
                ]
            )
        fields[vol.Required(CONF_FLOW_ACTION, default="save")] = navigation_selector(
            german=self._is_de(),
            primary_label="Übernehmen" if self._is_de() else "Apply",
        )

        if user_input is not None:
            if back_requested(user_input):
                return await self.async_step_server_cleanup()
            selected = [str(value) for value in user_input.get(CONF_DELETE_DEVICE_RECORD_IDS, [])]
            if selected and not errors:
                saved_age = int(
                    self._entry.options.get(
                        CONF_SERVER_CLEANUP_AGE_DAYS,
                        DEFAULT_SERVER_CLEANUP_AGE_DAYS,
                    )
                )
                if self._dirty or age_days != saved_age:
                    errors["base"] = "unsaved_changes"
                elif any(record_id not in candidates for record_id in selected):
                    errors["base"] = "invalid_selection"
                else:
                    self._pending_cleanup_records = {
                        record_id: candidates[record_id] for record_id in selected
                    }
                    self._pending_cleanup_age_days = age_days
                    return await self.async_step_confirm_server_deletion()
            elif (
                not selected
                and not errors
                and age_days
                != int(
                    self._entry.options.get(
                        CONF_SERVER_CLEANUP_AGE_DAYS,
                        DEFAULT_SERVER_CLEANUP_AGE_DAYS,
                    )
                )
            ):
                return await self.async_step_server_cleanup()

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

    async def async_step_confirm_server_deletion(self, user_input: dict[str, Any] | None = None):
        if not self._pending_cleanup_records:
            return await self.async_step_server_history_check()
        if user_input is not None:
            action = user_input.get(CONF_FLOW_ACTION)
            if action == FLOW_ACTION_BACK:
                return await self.async_step_back_to_server_history_check()
            if action == FLOW_ACTION_EXECUTE:
                return await self.async_step_execute_server_deletion()
        count = len(self._pending_cleanup_records)
        return self.async_show_form(
            step_id="confirm_server_deletion",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FLOW_ACTION): action_selector(
                        [
                            {
                                "value": FLOW_ACTION_EXECUTE,
                                "label": (
                                    f"{count} Emby-Einträge löschen"
                                    if self._is_de()
                                    else f"Delete {count} Emby records"
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
            description_placeholders={
                "count": str(count),
                "details": server_device_confirmation_details(
                    self._pending_cleanup_records.values(),
                    time_zone=self.hass.config.time_zone,
                    german=self._is_de(),
                ),
            },
        )

    async def async_step_back_to_server_history_check(
        self, user_input: dict[str, Any] | None = None
    ):
        self._pending_cleanup_records = {}
        self._pending_cleanup_age_days = None
        return await self.async_step_server_history_check()

    async def async_step_execute_server_deletion(self, user_input: dict[str, Any] | None = None):
        if not self._pending_cleanup_records:
            return await self.async_step_server_history_check()
        report, reload_needed = await async_run_manual_cleanup(
            self.hass,
            self._entry,
            selected_record_ids=self._pending_cleanup_records,
            age_days=int(
                self._pending_cleanup_age_days
                or self._entry.options.get(
                    CONF_SERVER_CLEANUP_AGE_DAYS,
                    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
                )
            ),
            remove_ha_entities=False,
        )
        self._pending_cleanup_records = {}
        self._pending_cleanup_age_days = None
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

    def _format_report_time(self, value: str | None, *, empty: str) -> str:
        if not value:
            return empty
        try:
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            try:
                zone = ZoneInfo(self.hass.config.time_zone)
            except ZoneInfoNotFoundError:
                zone = ZoneInfo("UTC")
            local = parsed.astimezone(zone)
        except (TypeError, ValueError):
            _LOGGER.warning("Invalid persisted EMBi maintenance timestamp: %r", value)
            return "Unbekannt" if self._is_de() else "Unknown"
        return local.strftime("%d.%m.%Y %H:%M" if self._is_de() else "%Y-%m-%d %H:%M")

    async def async_step_last_cleanup_run(self, user_input: dict[str, Any] | None = None):
        if back_requested(user_input):
            return await self.async_step_server_cleanup()
        report = self._runtime.maintenance_state.report
        never = "Noch nicht ausgeführt" if self._is_de() else "Not run yet"
        no_schedule = "Kein Lauf geplant" if self._is_de() else "No run scheduled"
        mode = {
            "manual": "Manuell" if self._is_de() else "Manual",
            "automatic": "Automatisch" if self._is_de() else "Automatic",
        }.get(report.mode, never)
        age = (
            f"{report.age_threshold_days} Tage"
            if self._is_de() and report.age_threshold_days is not None
            else (
                f"{report.age_threshold_days} days"
                if report.age_threshold_days is not None
                else "-"
            )
        )
        return self.async_show_form(
            step_id="last_cleanup_run",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FLOW_ACTION, default=FLOW_ACTION_BACK): navigation_selector(
                        german=self._is_de()
                    )
                }
            ),
            description_placeholders={
                "run_at": self._format_report_time(
                    report.completed_at or report.started_at,
                    empty=never,
                ),
                "mode": mode,
                "age": age,
                "deleted": str(report.server_deleted),
                "protected": str(report.skipped_active + report.registry_entities_protected),
                "failed": str(report.server_failed),
                "next_run": self._format_report_time(
                    report.next_run_at,
                    empty=no_schedule,
                ),
            },
        )
