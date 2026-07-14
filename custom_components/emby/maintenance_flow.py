from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_SSL
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .api import EmbyApiClient, EmbyApiError, EmbyAuthError
from .cleanup import (
    async_delete_device_records,
    plan_device_cleanup,
    removable_player_keys,
)
from .const import (
    AUTO_CLEANUP_INITIAL_DELAY_SECONDS,
    AUTO_CLEANUP_INTERVAL_HOURS,
    CONF_ADD_DELETED_TO_IGNORED,
    CONF_AUTO_CLEANUP_CONFIRMATION_TEXT,
    CONF_CONFIRM_AUTO_CLEANUP,
    CONF_CONFIRM_DELETE,
    CONF_CONFIRMATION_TEXT,
    CONF_DELETE_DEVICE_RECORD_IDS,
    CONF_IGNORED_DEVICE_IDS,
    CONF_REMOVE_DELETED_HA_ENTITIES,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_INITIAL_RUN_COMPLETED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_AGE_DAYS,
    CONF_SERVER_CLEANUP_API_KEY,
    CONF_SERVER_CLEANUP_ENABLED,
    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
    MAX_SERVER_CLEANUP_AGE_DAYS,
    MIN_SERVER_CLEANUP_AGE_DAYS,
)
from .helpers import server_device_selector_options
from .maintenance import active_player_keys, queue_registry_cleanup


def _api_client(
    hass, data: dict[str, Any], api_key: str | None = None
) -> EmbyApiClient:
    return EmbyApiClient(
        session=async_get_clientsession(hass),
        host=data[CONF_HOST],
        port=int(data[CONF_PORT]),
        api_key=api_key or data[CONF_API_KEY],
        use_ssl=data[CONF_SSL],
    )


def _text_selector(*, password: bool = False) -> selector.TextSelector:
    config: dict[str, Any] = {}
    if password:
        config["type"] = selector.TextSelectorType.PASSWORD
    return selector.TextSelector(selector.TextSelectorConfig(**config))


def _age_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=MIN_SERVER_CLEANUP_AGE_DAYS,
            max=MAX_SERVER_CLEANUP_AGE_DAYS,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


class ServerMaintenanceOptionsMixin:
    async def async_step_server_cleanup_settings(
        self, user_input: dict[str, Any] | None = None
    ):
        current = dict(self._entry.options)
        errors: dict[str, str] = {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SERVER_CLEANUP_ENABLED,
                    default=current.get(CONF_SERVER_CLEANUP_ENABLED, False),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_SERVER_CLEANUP_API_KEY,
                    default="",
                ): _text_selector(password=True),
            }
        )

        if user_input is not None:
            enabled = bool(user_input.get(CONF_SERVER_CLEANUP_ENABLED))
            submitted_cleanup_key = str(
                user_input.get(CONF_SERVER_CLEANUP_API_KEY, "")
            ).strip()
            stored_cleanup_key = str(
                current.get(CONF_SERVER_CLEANUP_API_KEY, "")
            ).strip()
            effective_cleanup_key = submitted_cleanup_key or stored_cleanup_key
            if enabled and effective_cleanup_key:
                try:
                    await _api_client(
                        self.hass, dict(self._entry.data), effective_cleanup_key
                    ).async_validate()
                except EmbyAuthError:
                    errors["base"] = "invalid_cleanup_auth"
                except EmbyApiError:
                    errors["base"] = "cannot_connect"

            if not errors:
                updated = dict(current)
                updated[CONF_SERVER_CLEANUP_ENABLED] = enabled
                if enabled and effective_cleanup_key:
                    updated[CONF_SERVER_CLEANUP_API_KEY] = effective_cleanup_key
                else:
                    updated.pop(CONF_SERVER_CLEANUP_API_KEY, None)
                if not enabled:
                    updated[CONF_SERVER_AUTO_CLEANUP_ENABLED] = False
                return self.async_create_entry(title="", data=updated)

        return self.async_show_form(
            step_id="server_cleanup_settings",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_server_cleanup(self, user_input: dict[str, Any] | None = None):
        if not self._entry.options.get(CONF_SERVER_CLEANUP_ENABLED, False):
            return self.async_abort(reason="server_cleanup_disabled")

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SERVER_CLEANUP_AGE_DAYS,
                    default=self._entry.options.get(
                        CONF_SERVER_CLEANUP_AGE_DAYS,
                        DEFAULT_SERVER_CLEANUP_AGE_DAYS,
                    ),
                ): _age_selector()
            }
        )
        if user_input is not None:
            self._pending_cleanup_age_days = int(
                user_input.get(
                    CONF_SERVER_CLEANUP_AGE_DAYS,
                    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
                )
            )
            return await self.async_step_server_cleanup_select()

        return self.async_show_form(
            step_id="server_cleanup",
            data_schema=schema,
            description_placeholders={
                "default_age_days": str(DEFAULT_SERVER_CLEANUP_AGE_DAYS)
            },
        )

    async def async_step_server_cleanup_select(
        self, user_input: dict[str, Any] | None = None
    ):
        if not self._entry.options.get(CONF_SERVER_CLEANUP_ENABLED, False):
            return self.async_abort(reason="server_cleanup_disabled")

        errors: dict[str, str] = {}
        try:
            devices = await self._devices(cleanup=True)
        except EmbyAuthError:
            devices = []
            errors["base"] = "invalid_cleanup_auth"
        except EmbyApiError:
            devices = []
            errors["base"] = "cannot_connect"

        plan = plan_device_cleanup(
            devices,
            now=dt_util.utcnow(),
            age_days=self._pending_cleanup_age_days,
            active_player_keys=active_player_keys(self.hass, self._entry),
        )
        devices_by_record = {device.record_id: device for device in plan.candidates}
        options = server_device_selector_options(plan.candidates)
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_DELETE_DEVICE_RECORD_IDS, default=[]
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": key, "label": value}
                            for key, value in options.items()
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_ADD_DELETED_TO_IGNORED, default=True
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_REMOVE_DELETED_HA_ENTITIES,
                    default=True,
                ): selector.BooleanSelector(),
            }
        )

        if user_input is not None and not errors:
            selected = list(user_input.get(CONF_DELETE_DEVICE_RECORD_IDS, []))
            if not selected:
                errors["base"] = "selection_required"
            elif any(record_id not in devices_by_record for record_id in selected):
                errors["base"] = "invalid_selection"
            else:
                self._pending_cleanup_records = {
                    record_id: devices_by_record[record_id] for record_id in selected
                }
                self._pending_add_to_ignored = bool(
                    user_input.get(CONF_ADD_DELETED_TO_IGNORED, True)
                )
                self._pending_remove_ha_entities = bool(
                    user_input.get(CONF_REMOVE_DELETED_HA_ENTITIES, True)
                )
                return await self.async_step_server_cleanup_confirm()

        return self.async_show_form(
            step_id="server_cleanup_select",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "count": str(len(plan.candidates)),
                "age_days": str(self._pending_cleanup_age_days),
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
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_CONFIRM_DELETE, default=False
                ): selector.BooleanSelector(),
                vol.Required(CONF_CONFIRMATION_TEXT, default=""): _text_selector(),
            }
        )

        if user_input is not None:
            if not user_input.get(CONF_CONFIRM_DELETE):
                errors["base"] = "confirmation_required"
            elif str(user_input.get(CONF_CONFIRMATION_TEXT, "")).strip() != phrase:
                errors["base"] = "confirmation_text_mismatch"
            else:
                try:
                    current_devices = await self._devices(cleanup=True)
                except EmbyApiError:
                    errors["base"] = "cannot_connect"
                else:
                    active = active_player_keys(self.hass, self._entry)
                    plan = plan_device_cleanup(
                        current_devices,
                        now=dt_util.utcnow(),
                        age_days=self._pending_cleanup_age_days,
                        active_player_keys=active,
                    )
                    allowed = {record.record_id: record for record in plan.candidates}
                    selected_ids = set(self._pending_cleanup_records)
                    if any(record_id not in allowed for record_id in selected_ids):
                        errors["base"] = "invalid_selection"
                    else:
                        selected_records = [
                            allowed[record_id] for record_id in selected_ids
                        ]
                        result = await async_delete_device_records(
                            self._cleanup_client(), selected_records
                        )
                        current_options = dict(self._entry.options)
                        updated = dict(current_options)
                        updated[CONF_SERVER_CLEANUP_AGE_DAYS] = (
                            self._pending_cleanup_age_days
                        )
                        if self._pending_add_to_ignored and result.succeeded:
                            ignored = set(updated.get(CONF_IGNORED_DEVICE_IDS, []))
                            ignored.update(
                                record.reported_device_id for record in result.succeeded
                            )
                            updated[CONF_IGNORED_DEVICE_IDS] = sorted(ignored)

                        queued = 0
                        if self._pending_remove_ha_entities and result.succeeded:
                            try:
                                remaining = await self._devices(cleanup=True)
                            except EmbyApiError:
                                remaining = None
                            if remaining is not None:
                                removable = removable_player_keys(
                                    result.succeeded,
                                    remaining,
                                    active_player_keys=active_player_keys(
                                        self.hass, self._entry
                                    ),
                                )
                                queued = queue_registry_cleanup(
                                    self.hass,
                                    self._entry.entry_id,
                                    removable,
                                )

                        options_changed = updated != current_options
                        if options_changed:
                            self.hass.config_entries.async_update_entry(
                                self._entry, options=updated
                            )
                        elif queued:
                            self.hass.async_create_task(
                                self.hass.config_entries.async_reload(
                                    self._entry.entry_id
                                ),
                                "Reload EMBi after manual device cleanup",
                            )

                        self._pending_cleanup_records = {}
                        return self.async_abort(
                            reason="server_cleanup_complete",
                            description_placeholders={
                                "success_count": str(len(result.succeeded)),
                                "failed_count": str(len(result.failed)),
                                "ha_cleanup_count": str(queued),
                                "failed_devices": ", ".join(
                                    record.label for record in result.failed
                                )
                                or "-",
                            },
                        )

        return self.async_show_form(
            step_id="server_cleanup_confirm",
            data_schema=schema,
            errors=errors,
            description_placeholders={"count": str(count), "phrase": phrase},
        )

    async def async_step_server_auto_cleanup_settings(
        self, user_input: dict[str, Any] | None = None
    ):
        if not self._entry.options.get(CONF_SERVER_CLEANUP_ENABLED, False):
            return self.async_abort(reason="server_cleanup_disabled")

        current = dict(self._entry.options)
        phrase = "AUTOMATISCH LÖSCHEN" if self._is_de() else "ENABLE AUTO DELETE"
        errors: dict[str, str] = {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SERVER_AUTO_CLEANUP_ENABLED,
                    default=current.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
                    default=current.get(
                        CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
                        DEFAULT_SERVER_CLEANUP_AGE_DAYS,
                    ),
                ): _age_selector(),
                vol.Required(
                    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
                    default=current.get(
                        CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
                        True,
                    ),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_CONFIRM_AUTO_CLEANUP,
                    default=False,
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_AUTO_CLEANUP_CONFIRMATION_TEXT,
                    default="",
                ): _text_selector(),
            }
        )

        if user_input is not None:
            enabled = bool(user_input.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False))
            enabling = enabled and not current.get(
                CONF_SERVER_AUTO_CLEANUP_ENABLED, False
            )
            if enabling and not user_input.get(CONF_CONFIRM_AUTO_CLEANUP):
                errors["base"] = "confirmation_required"
            elif enabling and (
                str(user_input.get(CONF_AUTO_CLEANUP_CONFIRMATION_TEXT, "")).strip()
                != phrase
            ):
                errors["base"] = "confirmation_text_mismatch"
            else:
                updated = dict(current)
                updated[CONF_SERVER_AUTO_CLEANUP_ENABLED] = enabled
                if enabling:
                    updated[CONF_SERVER_AUTO_CLEANUP_INITIAL_RUN_COMPLETED] = False
                elif not enabled:
                    updated.pop(CONF_SERVER_AUTO_CLEANUP_INITIAL_RUN_COMPLETED, None)
                updated[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS] = int(
                    user_input.get(
                        CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
                        DEFAULT_SERVER_CLEANUP_AGE_DAYS,
                    )
                )
                updated[CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES] = bool(
                    user_input.get(CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES, True)
                )
                return self.async_create_entry(title="", data=updated)

        return self.async_show_form(
            step_id="server_auto_cleanup_settings",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "phrase": phrase,
                "delay_seconds": str(AUTO_CLEANUP_INITIAL_DELAY_SECONDS),
                "interval_hours": str(AUTO_CLEANUP_INTERVAL_HOURS),
                "default_age_days": str(DEFAULT_SERVER_CLEANUP_AGE_DAYS),
            },
        )
