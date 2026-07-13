from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_NAME, CONF_PORT, CONF_SSL
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er, selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EmbyApiClient, EmbyApiError, EmbyAuthError
from .const import (
    CLIENT_MODE_ALL,
    CLIENT_MODES,
    CONF_ADD_DELETED_TO_IGNORED,
    CONF_ALLOWED_DEVICE_IDS,
    CONF_CLEANUP_ENTITY_IDS,
    CONF_CLIENT_MODE,
    CONF_CONFIRM_CLEANUP,
    CONF_CONFIRM_DELETE,
    CONF_DELETE_DEVICE_IDS,
    CONF_IGNORED_DEVICE_IDS,
    DEFAULT_PORT,
    DEFAULT_SSL,
    DOMAIN,
)
from .helpers import (
    device_selector_options,
    merge_missing_options,
    server_device_selector_options,
)


def _text_selector(*, password: bool = False) -> selector.TextSelector:
    config: dict[str, Any] = {}
    if password:
        config["type"] = selector.TextSelectorType.PASSWORD
    return selector.TextSelector(selector.TextSelectorConfig(**config))


def _connection_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "EMBi")): _text_selector(),
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): _text_selector(),
            vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=65535,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(CONF_SSL, default=defaults.get(CONF_SSL, DEFAULT_SSL)): selector.BooleanSelector(),
            vol.Required(CONF_API_KEY, default=defaults.get(CONF_API_KEY, "")): _text_selector(password=True),
        }
    )


async def _validate(hass, user_input: dict[str, Any]) -> dict[str, Any]:
    client = EmbyApiClient(
        session=async_get_clientsession(hass),
        host=user_input[CONF_HOST],
        port=int(user_input[CONF_PORT]),
        api_key=user_input[CONF_API_KEY],
        use_ssl=user_input[CONF_SSL],
    )
    return await client.async_validate()


class EmbyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2
    MINOR_VERSION = 0

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
                server_id = str(info.get("Id") or f"{user_input[CONF_HOST]}:{int(user_input[CONF_PORT])}")
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
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await _validate(self.hass, user_input)
            except EmbyAuthError:
                errors["base"] = "invalid_auth"
            except EmbyApiError:
                errors["base"] = "cannot_connect"
            else:
                server_id = str(info.get("Id") or f"{user_input[CONF_HOST]}:{int(user_input[CONF_PORT])}")
                await self.async_set_unique_id(server_id)
                self._abort_if_unique_id_mismatch()
                data = dict(user_input)
                data[CONF_PORT] = int(data[CONF_PORT])
                title = data.pop(CONF_NAME)
                self.hass.config_entries.async_update_entry(entry, title=title)
                return self.async_update_reload_and_abort(entry, data_updates=data)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_connection_schema(user_input or defaults),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return EmbyOptionsFlow(config_entry)


class EmbyOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    def _client(self) -> EmbyApiClient:
        return EmbyApiClient(
            session=async_get_clientsession(self.hass),
            host=self._entry.data[CONF_HOST],
            port=self._entry.data[CONF_PORT],
            api_key=self._entry.data[CONF_API_KEY],
            use_ssl=self._entry.data[CONF_SSL],
        )

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        return self.async_show_menu(
            step_id="init",
            menu_options=["clients", "ha_cleanup", "server_cleanup", "about"],
        )

    async def async_step_clients(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        current = dict(self._entry.options)
        try:
            devices = await self._client().async_get_devices()
        except EmbyApiError:
            errors["base"] = "cannot_connect"
            devices = []

        configured = [
            *current.get(CONF_ALLOWED_DEVICE_IDS, []),
            *current.get(CONF_IGNORED_DEVICE_IDS, []),
        ]
        missing_label = (
            "nicht aktuell vom Server gemeldet"
            if str(self.hass.config.language).lower().startswith("de")
            else "not currently reported by the server"
        )
        options = merge_missing_options(
            device_selector_options(devices), configured, missing_label
        )
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
            return self.async_create_entry(title="", data=updated)
        return self.async_show_form(
            step_id="clients", data_schema=schema, errors=errors, last_step=False
        )

    async def async_step_ha_cleanup(self, user_input: dict[str, Any] | None = None):
        registry = er.async_get(self.hass)
        entries = sorted(
            (
                entry
                for entry in registry.entities.values()
                if entry.domain == "media_player" and entry.platform == DOMAIN
            ),
            key=lambda entry: entry.entity_id,
        )
        choices = []
        for entry in entries:
            source = "UI" if entry.config_entry_id else "Legacy YAML"
            label = entry.name or entry.original_name or entry.entity_id
            choices.append(
                {
                    "value": entry.entity_id,
                    "label": f"{label} · {source} · {entry.unique_id}",
                }
            )

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
        errors: dict[str, str] = {}
        if user_input is not None:
            selected = list(user_input.get(CONF_CLEANUP_ENTITY_IDS, []))
            if selected and not user_input.get(CONF_CONFIRM_CLEANUP):
                errors["base"] = "confirmation_required"
            else:
                for entity_id in selected:
                    if registry.async_get(entity_id) is not None:
                        registry.async_remove(entity_id)
                return self.async_create_entry(title="", data=dict(self._entry.options))
        return self.async_show_form(
            step_id="ha_cleanup", data_schema=schema, errors=errors
        )

    async def async_step_server_cleanup(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        client = self._client()
        try:
            devices = await client.async_get_devices()
        except EmbyApiError:
            devices = []
            errors["base"] = "cannot_connect"

        options = server_device_selector_options(devices)
        schema = vol.Schema(
            {
                vol.Optional(CONF_DELETE_DEVICE_IDS, default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": key, "label": value} for key, value in options.items()],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_ADD_DELETED_TO_IGNORED, default=True): selector.BooleanSelector(),
                vol.Required(CONF_CONFIRM_DELETE, default=False): selector.BooleanSelector(),
            }
        )
        if user_input is not None and not errors:
            selected = list(user_input.get(CONF_DELETE_DEVICE_IDS, []))
            if selected and not user_input.get(CONF_CONFIRM_DELETE):
                errors["base"] = "confirmation_required"
            else:
                try:
                    for device_id in selected:
                        await client.async_delete_device(device_id)
                except EmbyApiError:
                    errors["base"] = "delete_failed"
                else:
                    current = dict(self._entry.options)
                    if user_input.get(CONF_ADD_DELETED_TO_IGNORED):
                        ignored = set(current.get(CONF_IGNORED_DEVICE_IDS, []))
                        ignored.update(selected)
                        current[CONF_IGNORED_DEVICE_IDS] = sorted(ignored)
                    return self.async_create_entry(title="", data=current)
        return self.async_show_form(
            step_id="server_cleanup", data_schema=schema, errors=errors
        )

    async def async_step_about(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=dict(self._entry.options))
        return self.async_show_form(step_id="about", data_schema=vol.Schema({}))
