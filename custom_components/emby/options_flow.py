from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from .api import EmbyApiError, EmbyDeviceRecord
from .const import (
    CONF_ALLOWED_DEVICE_IDS,
    CONF_CONFIRM_APPLY,
    CONF_CONFIRM_DISCARD,
    CONF_IGNORED_PLAYER_KEYS,
    CONF_IGNORED_REPORTED_DEVICE_IDS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_CLEANUP_ENABLED,
    VERSION,
)
from .helpers import migrate_stable_options
from .maintenance_flow import ServerMaintenanceOptionsMixin
from .models import EmbiRuntimeData
from .options_clients import ClientOptionsMixin
from .options_draft import OptionsDraft
from .options_registry import RegistryOptionsMixin


class EmbyOptionsFlow(
    ClientOptionsMixin,
    RegistryOptionsMixin,
    ServerMaintenanceOptionsMixin,
    config_entries.OptionsFlow,
):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        self._draft = OptionsDraft.from_options(config_entry.options)
        self._original_options = self._draft.original
        self._draft_options = self._draft.current
        self._pending_cleanup_records: dict[str, EmbyDeviceRecord] = {}
        self._pending_remove_ha_entities = False
        self._pending_auto_settings: dict[str, Any] | None = None

    @property
    def _dirty(self) -> bool:
        return self._draft.dirty

    @property
    def _runtime(self) -> EmbiRuntimeData:
        return self._entry.runtime_data

    def _is_de(self) -> bool:
        return str(self.hass.config.language).lower().startswith("de")

    async def _devices(self) -> list[EmbyDeviceRecord]:
        return await self._runtime.api_client.async_get_devices()

    def _draft_summary(self) -> str:
        if not self._dirty:
            return "Keine ungespeicherten Änderungen" if self._is_de() else "No unsaved changes"
        auto = bool(self._draft_options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False))
        allowed = len(self._draft_options.get(CONF_ALLOWED_DEVICE_IDS, []))
        ignored_apps = len(self._draft_options.get(CONF_IGNORED_PLAYER_KEYS, []))
        ignored_devices = len(self._draft_options.get(CONF_IGNORED_REPORTED_DEVICE_IDS, []))
        if self._is_de():
            return (
                f"Ungespeicherte Änderungen · Automatik: {'ein' if auto else 'aus'} · "
                f"Auswahl: {allowed} · App-Regeln: {ignored_apps} · Geräte-Regeln: {ignored_devices}"
            )
        return (
            f"Unsaved changes · Automation: {'on' if auto else 'off'} · Selected: {allowed} · "
            f"App rules: {ignored_apps} · Device rules: {ignored_devices}"
        )

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        menu_options = [
            "clients",
            "clients_bulk",
            "server_cleanup_settings",
            "server_auto_cleanup_settings",
        ]
        if not self._dirty:
            menu_options.append("ha_cleanup")
            if self._entry.options.get(CONF_SERVER_CLEANUP_ENABLED, False):
                menu_options.append("server_cleanup")
        menu_options.extend(["cleanup_report", "about", "apply", "discard"])
        return self.async_show_menu(
            step_id="init",
            menu_options=menu_options,
            description_placeholders={"draft_summary": self._draft_summary()},
        )

    async def async_step_cleanup_report(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return await self.async_step_init()
        report = self._runtime.maintenance_state.report

        def local_time(value: str | None) -> str:
            if not value:
                return "-"
            try:
                parsed = datetime.fromisoformat(value)
            except ValueError:
                return "-"
            return dt_util.as_local(parsed).strftime("%Y-%m-%d %H:%M:%S %Z")

        return self.async_show_form(
            step_id="cleanup_report",
            data_schema=vol.Schema({}),
            description_placeholders={
                "status": report.status,
                "mode": report.mode or "-",
                "started_at": local_time(report.started_at),
                "completed_at": local_time(report.completed_at),
                "age_days": str(report.age_threshold_days or "-"),
                "server_candidates": str(report.server_candidates),
                "server_deleted": str(report.server_deleted),
                "server_failed": str(report.server_failed),
                "skipped_active": str(report.skipped_active),
                "skipped_without_activity": str(report.skipped_without_activity),
                "registry_queued": str(report.registry_keys_queued),
                "registry_matched": str(report.registry_entities_matched),
                "registry_removed": str(report.registry_entities_removed),
                "registry_missing": str(report.registry_entities_missing),
                "registry_protected": str(report.registry_entities_protected),
                "last_error": report.last_error or "-",
                "counts_complete": str(report.result_counts_complete),
                "next_run_at": local_time(report.next_run_at),
            },
        )

    async def async_step_apply(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_CONFIRM_APPLY):
                errors["base"] = "confirmation_required"
            else:
                try:
                    devices = await self._devices()
                except EmbyApiError:
                    errors["base"] = "cannot_connect"
                else:
                    updated, _ = migrate_stable_options(dict(self._draft_options), devices)
                    original_normalized, _ = migrate_stable_options(
                        dict(self._original_options), devices
                    )
                    if updated == original_normalized:
                        return self.async_abort(reason="no_changes")
                    original_auto = bool(
                        self._original_options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False)
                    )
                    updated_auto = bool(updated.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False))
                    if updated_auto and not updated.get(CONF_SERVER_CLEANUP_ENABLED, False):
                        errors["base"] = "auto_requires_cleanup"
                    if not errors and original_auto != updated_auto:
                        state = deepcopy(self._runtime.maintenance_state)
                        if updated_auto:
                            state.initial_run_completed = False
                        state.report.next_run_at = None
                        try:
                            await self._runtime.maintenance_store.async_save(state)
                        except Exception:
                            errors["base"] = "storage_failed"
                        else:
                            self._runtime.maintenance_state = state
                    if not errors:
                        return self.async_create_entry(title="", data=updated)
        return self.async_show_form(
            step_id="apply",
            data_schema=vol.Schema(
                {vol.Required(CONF_CONFIRM_APPLY, default=False): selector.BooleanSelector()}
            ),
            errors=errors,
            description_placeholders={"draft_summary": self._draft_summary()},
        )

    async def async_step_discard(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_CONFIRM_DISCARD):
                errors["base"] = "confirmation_required"
            else:
                self._draft.discard()
                self._pending_auto_settings = None
                self._pending_cleanup_records = {}
                self._pending_remove_ha_entities = False
                return await self.async_step_init()
        return self.async_show_form(
            step_id="discard",
            data_schema=vol.Schema(
                {vol.Required(CONF_CONFIRM_DISCARD, default=False): selector.BooleanSelector()}
            ),
            errors=errors,
        )

    async def async_step_about(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return await self.async_step_init()
        return self.async_show_form(
            step_id="about",
            data_schema=vol.Schema({}),
            description_placeholders={"version": VERSION},
        )
