from __future__ import annotations

from collections.abc import Callable
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_NAME, CONF_PORT, CONF_SSL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EmbyApiClient, EmbyApiError, EmbyAuthError, EmbyDeviceRecord
from .cleanup import async_delete_device_records
from .const import (
    CLIENT_MODE_ALL,
    CLIENT_MODE_ALLOWLIST,
    CLIENT_MODES,
    CONF_ADD_DELETED_TO_IGNORED,
    CONF_ALLOWED_DEVICE_IDS,
    CONF_CLEANUP_ENTITY_IDS,
    CONF_CLIENT_MODE,
    CONF_CONFIRM_BULK,
    CONF_CONFIRM_CLEANUP,
    CONF_CONFIRM_DELETE,
    CONF_CONFIRMATION_TEXT,
    CONF_DELETE_DEVICE_RECORD_IDS,
    CONF_IGNORED_DEVICE_IDS,
    CONF_SERVER_CLEANUP_API_KEY,
    CONF_SERVER_CLEANUP_ENABLED,
    DEFAULT_PORT,
    DEFAULT_SSL,
    DOMAIN,
    VERSION,
)
from .helpers import (
    device_selector_options,
    merge_missing_options,
    registry_cleanup_reason,
    server_device_selector_options,
    unique_player_keys,
    unique_reported_device_ids,
)


def _text_selector(*, password: bool = False) -> selector.TextSelector:
    config: dict[str, Any] = {}
    if password:
        config["type"] = selector.TextSelectorType.PASSWORD
    return selector.TextSelector(selector.TextSelectorConfig(**config))


def _connection_schema(
    defaults: dict[str, Any] | None = None, *, require_api_key: bool = True
) -> vol.Schema:
    defaults = defaults or {}
    api_key_marker = (
        vol.Required(CONF_API_KEY, default="")
        if require_api_key
        else vol.Optional(CONF_API_KEY, default="")
    )
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "EMBi")): _text_selector(),
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): _text_selector(),
            vol.Required(
                CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=65535,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_SSL, default=defaults.get(CONF_SSL, DEFAULT_SSL)
            ): selector.BooleanSelector(),
            api_key_marker: _text_selector(password=True),
        }
    )


def _api_client(
    hass: HomeAssistant, data: dict[str, Any], api_key: str | None = None
) -> EmbyApiClient:
    return EmbyApiClient(
        session=async_get_clientsession(hass),
        host=data[CONF_HOST],
        port=int(data[CONF_PORT]),
        api_key=api_key or data[CONF_API_KEY],
        use_ssl=data[CONF_SSL],
    )


async def _validate(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, Any]:
    return await _api_client(hass, user_input).async_validate()


class EmbyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the EMBi config flow."""

    VERSION = 2
    MINOR_VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await _validate(self.hass, user_input)
            except EmbyAuthError:
                errors["base"] = "invalid_auth"
            except EmbyApiError:
                errors["base"] = "cannot_connect"
            else:
                server_id = str(
                    info.get("Id") or f"{user_input[CONF_HOST]}:{int(user_input[CONF_PORT])}"
                )
                await self.async_set_unique_id(server_id)
                self._abort_if_unique_id_configured()
                data = dict(user_input)
                data[CONF_PORT] = int(data[CONF_PORT])
                title = data.pop(CONF_NAME)
                return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_connection_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        entry = self._get_reconfigure_entry()
        defaults = {CONF_NAME: entry.title, **entry.data}
        defaults.pop(CONF_API_KEY, None)
        errors: dict[str, str] = {}
        if user_input is not None:
            data = dict(user_input)
            submitted_api_key = str(data.get(CONF_API_KEY, "")).strip()
            data[CONF_API_KEY] = submitted_api_key or entry.data[CONF_API_KEY]
            try:
                info = await _validate(self.hass, data)
            except EmbyAuthError:
                errors["base"] = "invalid_auth"
            except EmbyApiError:
                errors["base"] = "cannot_connect"
            else:
                server_id = str(info.get("Id") or f"{data[CONF_HOST]}:{int(data[CONF_PORT])}")
                await self.async_set_unique_id(server_id)
                self._abort_if_unique_id_mismatch()
                data[CONF_PORT] = int(data[CONF_PORT])
                title = data.pop(CONF_NAME)
                self.hass.config_entries.async_update_entry(entry, title=title)
                return self.async_update_reload_and_abort(entry, data_updates=data)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_connection_schema(
                {
                    key: value
                    for key, value in (user_input or defaults).items()
                    if key != CONF_API_KEY
                },
                require_api_key=False,
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return EmbyOptionsFlow(config_entry)


class EmbyOptionsFlow(config_entries.OptionsFlow):
    """Handle EMBi options and maintenance actions."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        self._pending_cleanup_records: dict[str, EmbyDeviceRecord] = {}
        self._pending_add_to_ignored = True

    def _client(self) -> EmbyApiClient:
        return _api_client(self.hass, dict(self._entry.data))

    def _cleanup_client(self) -> EmbyApiClient:
        cleanup_key = str(self._entry.options.get(CONF_SERVER_CLEANUP_API_KEY, "")).strip()
        return _api_client(
            self.hass,
            dict(self._entry.data),
            cleanup_key or self._entry.data[CONF_API_KEY],
        )

    def _is_de(self) -> bool:
        return str(self.hass.config.language).lower().startswith("de")

    async def _devices(self, *, cleanup: bool = False) -> list[EmbyDeviceRecord]:
        client = self._cleanup_client() if cleanup else self._client()
        return await client.async_get_devices()

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        menu_options = [
            "clients",
            "clients_bulk",
            "ha_cleanup",
            "server_cleanup_settings",
        ]
        if self._entry.options.get(CONF_SERVER_CLEANUP_ENABLED, False):
            menu_options.append("server_cleanup")
        menu_options.append("about")
        return self.async_show_menu(step_id="init", menu_options=menu_options)

    async def async_step_clients(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        current = dict(self._entry.options)
        try:
            devices = await self._devices()
        except EmbyApiError:
            errors["base"] = "cannot_connect"
            devices = []

        configured = [
            *current.get(CONF_ALLOWED_DEVICE_IDS, []),
            *current.get(CONF_IGNORED_DEVICE_IDS, []),
        ]
        missing_label = (
            "nicht aktuell vom Server gemeldet"
            if self._is_de()
            else "not currently reported by the server"
        )
        options = merge_missing_options(device_selector_options(devices), configured, missing_label)
        selector_options = [{"value": key, "label": value} for key, value in options.items()]
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_CLIENT_MODE,
                    default=current.get(CONF_CLIENT_MODE, CLIENT_MODE_ALL),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=CLIENT_MODES,
                        translation_key="client_mode",
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_ALLOWED_DEVICE_IDS,
                    default=current.get(CONF_ALLOWED_DEVICE_IDS, []),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=selector_options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_IGNORED_DEVICE_IDS,
                    default=current.get(CONF_IGNORED_DEVICE_IDS, []),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=selector_options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        if user_input is not None and not errors:
            updated = {**current, **user_input}
            updated[CONF_ALLOWED_DEVICE_IDS] = sorted(set(updated.get(CONF_ALLOWED_DEVICE_IDS, [])))
            updated[CONF_IGNORED_DEVICE_IDS] = sorted(set(updated.get(CONF_IGNORED_DEVICE_IDS, [])))
            return self.async_create_entry(title="", data=updated)

        return self.async_show_form(step_id="clients", data_schema=schema, errors=errors)

    async def async_step_clients_bulk(self, user_input: dict[str, Any] | None = None):
        return self.async_show_menu(
            step_id="clients_bulk",
            menu_options=[
                "clients_allow_all",
                "clients_allow_none",
                "clients_ignore_all",
                "clients_ignore_none",
            ],
        )

    async def _async_bulk_step(
        self,
        step_id: str,
        apply_action: Callable[[dict[str, Any], list[EmbyDeviceRecord]], None],
        user_input: dict[str, Any] | None,
        item_count: Callable[[list[EmbyDeviceRecord]], int] | None = None,
    ):
        errors: dict[str, str] = {}
        try:
            devices = await self._devices()
        except EmbyApiError:
            devices = []
            errors["base"] = "cannot_connect"

        if user_input is not None and not errors:
            if not user_input.get(CONF_CONFIRM_BULK):
                errors["base"] = "confirmation_required"
            else:
                updated = dict(self._entry.options)
                apply_action(updated, devices)
                return self.async_create_entry(title="", data=updated)

        schema = vol.Schema(
            {vol.Required(CONF_CONFIRM_BULK, default=False): selector.BooleanSelector()}
        )
        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "count": str(item_count(devices) if item_count else len(devices))
            },
        )

    async def async_step_clients_allow_all(self, user_input: dict[str, Any] | None = None):
        def apply_action(options: dict[str, Any], devices: list[EmbyDeviceRecord]) -> None:
            options[CONF_ALLOWED_DEVICE_IDS] = unique_player_keys(devices)
            options[CONF_CLIENT_MODE] = CLIENT_MODE_ALLOWLIST

        return await self._async_bulk_step(
            "clients_allow_all",
            apply_action,
            user_input,
            item_count=lambda devices: len(unique_player_keys(devices)),
        )

    async def async_step_clients_allow_none(self, user_input: dict[str, Any] | None = None):
        def apply_action(options: dict[str, Any], devices: list[EmbyDeviceRecord]) -> None:
            options[CONF_ALLOWED_DEVICE_IDS] = []

        return await self._async_bulk_step("clients_allow_none", apply_action, user_input)

    async def async_step_clients_ignore_all(self, user_input: dict[str, Any] | None = None):
        def apply_action(options: dict[str, Any], devices: list[EmbyDeviceRecord]) -> None:
            options[CONF_IGNORED_DEVICE_IDS] = unique_reported_device_ids(devices)

        return await self._async_bulk_step(
            "clients_ignore_all",
            apply_action,
            user_input,
            item_count=lambda devices: len(unique_reported_device_ids(devices)),
        )

    async def async_step_clients_ignore_none(self, user_input: dict[str, Any] | None = None):
        def apply_action(options: dict[str, Any], devices: list[EmbyDeviceRecord]) -> None:
            options[CONF_IGNORED_DEVICE_IDS] = []

        return await self._async_bulk_step("clients_ignore_none", apply_action, user_input)

    def _registry_cleanup_choices(self) -> list[dict[str, str]]:
        registry = er.async_get(self.hass)
        ignored_ids = self._entry.options.get(CONF_IGNORED_DEVICE_IDS, [])
        choices: list[dict[str, str]] = []

        reason_labels = {
            "legacy_yaml": "Altes YAML" if self._is_de() else "Legacy YAML",
            "registry_only": "Nur Registry" if self._is_de() else "Registry only",
            "ignored": "Ignoriert" if self._is_de() else "Ignored",
        }

        for entry in sorted(registry.entities.values(), key=lambda item: item.entity_id):
            if entry.domain != "media_player" or entry.platform != DOMAIN:
                continue

            reason = registry_cleanup_reason(
                has_state=self.hass.states.get(entry.entity_id) is not None,
                config_entry_id=entry.config_entry_id,
                target_entry_id=self._entry.entry_id,
                unique_id=str(entry.unique_id),
                ignored_ids=ignored_ids,
            )
            if reason is None:
                continue

            status = reason_labels[reason]
            label = entry.name or entry.original_name or entry.entity_id
            choices.append(
                {
                    "value": entry.entity_id,
                    "label": f"{label} · {status} · {entry.unique_id}",
                }
            )
        return choices

    async def async_step_ha_cleanup(self, user_input: dict[str, Any] | None = None):
        registry = er.async_get(self.hass)
        choices = self._registry_cleanup_choices()
        allowed_values = {choice["value"] for choice in choices}
        errors: dict[str, str] = {}

        schema = vol.Schema(
            {
                vol.Optional(CONF_CLEANUP_ENTITY_IDS, default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=choices,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_CONFIRM_CLEANUP, default=False): selector.BooleanSelector(),
            }
        )

        if user_input is not None:
            selected = list(user_input.get(CONF_CLEANUP_ENTITY_IDS, []))
            if any(entity_id not in allowed_values for entity_id in selected):
                errors["base"] = "invalid_selection"
            elif selected and not user_input.get(CONF_CONFIRM_CLEANUP):
                errors["base"] = "confirmation_required"
            else:
                revalidated_values = {
                    choice["value"] for choice in self._registry_cleanup_choices()
                }
                if any(entity_id not in revalidated_values for entity_id in selected):
                    errors["base"] = "invalid_selection"
                else:
                    for entity_id in selected:
                        if registry.async_get(entity_id) is not None:
                            registry.async_remove(entity_id)
                    return self.async_create_entry(title="", data=dict(self._entry.options))

        return self.async_show_form(
            step_id="ha_cleanup",
            data_schema=schema,
            errors=errors,
            description_placeholders={"count": str(len(choices))},
        )

    async def async_step_server_cleanup_settings(self, user_input: dict[str, Any] | None = None):
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
            submitted_cleanup_key = str(user_input.get(CONF_SERVER_CLEANUP_API_KEY, "")).strip()
            stored_cleanup_key = str(current.get(CONF_SERVER_CLEANUP_API_KEY, "")).strip()
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
                return self.async_create_entry(title="", data=updated)

        return self.async_show_form(
            step_id="server_cleanup_settings",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_server_cleanup(self, user_input: dict[str, Any] | None = None):
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

        devices_by_record = {device.record_id: device for device in devices}
        options = server_device_selector_options(devices)
        schema = vol.Schema(
            {
                vol.Optional(CONF_DELETE_DEVICE_RECORD_IDS, default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": key, "label": value} for key, value in options.items()],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_ADD_DELETED_TO_IGNORED, default=True): selector.BooleanSelector(),
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
                return await self.async_step_server_cleanup_confirm()

        return self.async_show_form(
            step_id="server_cleanup",
            data_schema=schema,
            errors=errors,
            description_placeholders={"count": str(len(devices))},
        )

    async def async_step_server_cleanup_confirm(self, user_input: dict[str, Any] | None = None):
        if not self._pending_cleanup_records:
            return await self.async_step_server_cleanup()

        count = len(self._pending_cleanup_records)
        phrase = f"LÖSCHEN {count}" if self._is_de() else f"DELETE {count}"
        errors: dict[str, str] = {}
        schema = vol.Schema(
            {
                vol.Required(CONF_CONFIRM_DELETE, default=False): selector.BooleanSelector(),
                vol.Required(CONF_CONFIRMATION_TEXT, default=""): _text_selector(),
            }
        )

        if user_input is not None:
            if not user_input.get(CONF_CONFIRM_DELETE):
                errors["base"] = "confirmation_required"
            elif str(user_input.get(CONF_CONFIRMATION_TEXT, "")).strip() != phrase:
                errors["base"] = "confirmation_text_mismatch"
            else:
                result = await async_delete_device_records(
                    self._cleanup_client(), self._pending_cleanup_records.values()
                )

                updated = dict(self._entry.options)
                if self._pending_add_to_ignored and result.succeeded:
                    ignored = set(updated.get(CONF_IGNORED_DEVICE_IDS, []))
                    ignored.update(record.reported_device_id for record in result.succeeded)
                    updated[CONF_IGNORED_DEVICE_IDS] = sorted(ignored)

                self.hass.config_entries.async_update_entry(self._entry, options=updated)
                return self.async_abort(
                    reason="server_cleanup_complete",
                    description_placeholders={
                        "success_count": str(len(result.succeeded)),
                        "failed_count": str(len(result.failed)),
                        "failed_devices": ", ".join(record.label for record in result.failed)
                        or "-",
                    },
                )

        return self.async_show_form(
            step_id="server_cleanup_confirm",
            data_schema=schema,
            errors=errors,
            description_placeholders={"count": str(count), "phrase": phrase},
        )

    async def async_step_about(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=dict(self._entry.options))
        return self.async_show_form(
            step_id="about",
            data_schema=vol.Schema({}),
            description_placeholders={"version": VERSION},
        )
