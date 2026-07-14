from __future__ import annotations

from collections.abc import Callable
from typing import Any

import voluptuous as vol
from homeassistant.helpers import selector

from .api import EmbyApiError, EmbyDeviceRecord
from .const import (
    CLIENT_MODE_ALL,
    CLIENT_MODES,
    CONF_ALLOWED_DEVICE_IDS,
    CONF_CLIENT_MODE,
    CONF_CONFIRM_BULK,
    CONF_IGNORED_PLAYER_KEYS,
    CONF_IGNORED_REPORTED_DEVICE_IDS,
    CONF_UNRESOLVED_IGNORED_IDS,
)
from .helpers import (
    device_selector_options,
    merge_missing_options,
    reported_device_selector_options,
    unique_player_keys,
    unique_reported_device_ids,
)


class ClientOptionsMixin:
    async def async_step_clients(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        try:
            devices = await self._devices()
        except EmbyApiError:
            errors["base"] = "cannot_connect"
            devices = []

        missing_label = (
            "nicht aktuell vom Server gemeldet"
            if self._is_de()
            else "not currently reported by the server"
        )
        player_options = merge_missing_options(
            device_selector_options(devices),
            [
                *self._draft_options.get(CONF_ALLOWED_DEVICE_IDS, []),
                *self._draft_options.get(CONF_IGNORED_PLAYER_KEYS, []),
            ],
            missing_label,
        )
        raw_options = merge_missing_options(
            reported_device_selector_options(devices),
            self._draft_options.get(CONF_IGNORED_REPORTED_DEVICE_IDS, []),
            missing_label,
        )
        unresolved = list(self._draft_options.get(CONF_UNRESOLVED_IGNORED_IDS, []))
        unresolved_options = [
            {"value": value, "label": f"{value} · {missing_label}"} for value in unresolved
        ]

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_CLIENT_MODE,
                    default=self._draft_options.get(CONF_CLIENT_MODE, CLIENT_MODE_ALL),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=CLIENT_MODES,
                        translation_key="client_mode",
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_ALLOWED_DEVICE_IDS,
                    default=self._draft_options.get(CONF_ALLOWED_DEVICE_IDS, []),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": key, "label": label} for key, label in player_options.items()
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_IGNORED_PLAYER_KEYS,
                    default=self._draft_options.get(CONF_IGNORED_PLAYER_KEYS, []),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": key, "label": label} for key, label in player_options.items()
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_IGNORED_REPORTED_DEVICE_IDS,
                    default=self._draft_options.get(CONF_IGNORED_REPORTED_DEVICE_IDS, []),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": key, "label": label} for key, label in raw_options.items()
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_UNRESOLVED_IGNORED_IDS,
                    default=unresolved,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=unresolved_options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        if user_input is not None and not errors:
            self._draft_options[CONF_CLIENT_MODE] = user_input[CONF_CLIENT_MODE]
            for key in (
                CONF_ALLOWED_DEVICE_IDS,
                CONF_IGNORED_PLAYER_KEYS,
                CONF_IGNORED_REPORTED_DEVICE_IDS,
                CONF_UNRESOLVED_IGNORED_IDS,
            ):
                self._draft_options[key] = sorted(set(user_input.get(key, [])))
            return await self.async_step_init()

        return self.async_show_form(step_id="clients", data_schema=schema, errors=errors)

    async def async_step_clients_bulk(self, user_input: dict[str, Any] | None = None):
        return self.async_show_menu(
            step_id="clients_bulk",
            menu_options=[
                "clients_allow_all",
                "clients_allow_none",
                "clients_ignore_apps_all",
                "clients_ignore_apps_none",
                "clients_ignore_devices_all",
                "clients_ignore_devices_none",
            ],
        )

    async def _async_bulk_step(
        self,
        step_id: str,
        apply_action: Callable[[list[EmbyDeviceRecord]], None],
        user_input: dict[str, Any] | None,
        item_count: Callable[[list[EmbyDeviceRecord]], int],
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
                apply_action(devices)
                return await self.async_step_init()

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {vol.Required(CONF_CONFIRM_BULK, default=False): selector.BooleanSelector()}
            ),
            errors=errors,
            description_placeholders={"count": str(item_count(devices))},
        )

    async def async_step_clients_allow_all(self, user_input: dict[str, Any] | None = None):
        def apply(devices: list[EmbyDeviceRecord]) -> None:
            self._draft_options[CONF_ALLOWED_DEVICE_IDS] = unique_player_keys(devices)
            self._draft_options[CONF_CLIENT_MODE] = "allowlist"

        return await self._async_bulk_step(
            "clients_allow_all", apply, user_input, lambda devices: len(unique_player_keys(devices))
        )

    async def async_step_clients_allow_none(self, user_input: dict[str, Any] | None = None):
        def apply(devices: list[EmbyDeviceRecord]) -> None:
            self._draft_options[CONF_ALLOWED_DEVICE_IDS] = []

        return await self._async_bulk_step(
            "clients_allow_none", apply, user_input, lambda devices: 0
        )

    async def async_step_clients_ignore_apps_all(self, user_input: dict[str, Any] | None = None):
        def apply(devices: list[EmbyDeviceRecord]) -> None:
            self._draft_options[CONF_IGNORED_PLAYER_KEYS] = unique_player_keys(devices)

        return await self._async_bulk_step(
            "clients_ignore_apps_all",
            apply,
            user_input,
            lambda devices: len(unique_player_keys(devices)),
        )

    async def async_step_clients_ignore_apps_none(self, user_input: dict[str, Any] | None = None):
        def apply(devices: list[EmbyDeviceRecord]) -> None:
            self._draft_options[CONF_IGNORED_PLAYER_KEYS] = []

        return await self._async_bulk_step(
            "clients_ignore_apps_none", apply, user_input, lambda devices: 0
        )

    async def async_step_clients_ignore_devices_all(self, user_input: dict[str, Any] | None = None):
        def apply(devices: list[EmbyDeviceRecord]) -> None:
            self._draft_options[CONF_IGNORED_REPORTED_DEVICE_IDS] = unique_reported_device_ids(
                devices
            )

        return await self._async_bulk_step(
            "clients_ignore_devices_all",
            apply,
            user_input,
            lambda devices: len(unique_reported_device_ids(devices)),
        )

    async def async_step_clients_ignore_devices_none(
        self, user_input: dict[str, Any] | None = None
    ):
        def apply(devices: list[EmbyDeviceRecord]) -> None:
            self._draft_options[CONF_IGNORED_REPORTED_DEVICE_IDS] = []

        return await self._async_bulk_step(
            "clients_ignore_devices_none", apply, user_input, lambda devices: 0
        )
