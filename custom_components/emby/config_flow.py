from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_NAME, CONF_PORT, CONF_SSL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EmbyApiClient, EmbyApiError, EmbyAuthError
from .const import DEFAULT_PORT, DEFAULT_SSL, DOMAIN
from .options_flow import EmbyOptionsFlow


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
