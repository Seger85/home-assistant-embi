from __future__ import annotations

from collections.abc import Callable
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_SSL
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EmbyApiClient, EmbyApiError, EmbyDeviceRecord
from .const import (
    CLIENT_MODE_ALL,
    CLIENT_MODE_ALLOWLIST,
    CLIENT_MODES,
    CONF_ALLOWED_DEVICE_IDS,
    CONF_CLEANUP_ENTITY_IDS,
    CONF_CLIENT_MODE,
    CONF_CONFIRM_BULK,
    CONF_CONFIRM_CLEANUP,
    CONF_IGNORED_DEVICE_IDS,
    CONF_SERVER_CLEANUP_API_KEY,
    CONF_SERVER_CLEANUP_ENABLED,
    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
    DOMAIN,
    VERSION,
)
from .helpers import (
    device_selector_options,
    merge_missing_options,
    registry_cleanup_reason,
    unique_player_keys,
    unique_reported_device_ids,
)
from .maintenance_flow import ServerMaintenanceOptionsMixin


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


class EmbyOptionsFlow(ServerMaintenanceOptionsMixin, config_entries.OptionsFlow):
    """Handle EMBi options and maintenance actions."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        self._pending_cleanup_records: dict[str, EmbyDeviceRecord] = {}
        self._pending_add_to_ignored = True
        self._pending_remove_ha_entities = True
        self._pending_cleanup_age_days = DEFAULT_SERVER_CLEANUP_AGE_DAYS

    def _client(self) -> EmbyApiClient:
        return _api_client(self.hass, dict(self._entry.data))

    def _cleanup_client(self) -> EmbyApiClient:
        cleanup_key = str(
            self._entry.options.get(CONF_SERVER_CLEANUP_API_KEY, "")
        ).strip()
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
            menu_options.extend(["server_cleanup", "server_auto_cleanup_settings"])
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
        options = merge_missing_options(
            device_selector_options(devices), configured, missing_label
        )
        selector_options = [
            {"value": key, "label": value} for key, value in options.items()
        ]
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
            updated[CONF_ALLOWED_DEVICE_IDS] = sorted(
                set(updated.get(CONF_ALLOWED_DEVICE_IDS, []))
            )
            updated[CONF_IGNORED_DEVICE_IDS] = sorted(
                set(updated.get(CONF_IGNORED_DEVICE_IDS, []))
            )
            return self.async_create_entry(title="", data=updated)

        return self.async_show_form(
            step_id="clients", data_schema=schema, errors=errors
        )

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

    async def async_step_clients_allow_all(
        self, user_input: dict[str, Any] | None = None
    ):
        def apply_action(
            options: dict[str, Any], devices: list[EmbyDeviceRecord]
        ) -> None:
            options[CONF_ALLOWED_DEVICE_IDS] = unique_player_keys(devices)
            options[CONF_CLIENT_MODE] = CLIENT_MODE_ALLOWLIST

        return await self._async_bulk_step(
            "clients_allow_all",
            apply_action,
            user_input,
            item_count=lambda devices: len(unique_player_keys(devices)),
        )

    async def async_step_clients_allow_none(
        self, user_input: dict[str, Any] | None = None
    ):
        def apply_action(
            options: dict[str, Any], devices: list[EmbyDeviceRecord]
        ) -> None:
            options[CONF_ALLOWED_DEVICE_IDS] = []

        return await self._async_bulk_step(
            "clients_allow_none", apply_action, user_input
        )

    async def async_step_clients_ignore_all(
        self, user_input: dict[str, Any] | None = None
    ):
        def apply_action(
            options: dict[str, Any], devices: list[EmbyDeviceRecord]
        ) -> None:
            options[CONF_IGNORED_DEVICE_IDS] = unique_reported_device_ids(devices)

        return await self._async_bulk_step(
            "clients_ignore_all",
            apply_action,
            user_input,
            item_count=lambda devices: len(unique_reported_device_ids(devices)),
        )

    async def async_step_clients_ignore_none(
        self, user_input: dict[str, Any] | None = None
    ):
        def apply_action(
            options: dict[str, Any], devices: list[EmbyDeviceRecord]
        ) -> None:
            options[CONF_IGNORED_DEVICE_IDS] = []

        return await self._async_bulk_step(
            "clients_ignore_none", apply_action, user_input
        )

    def _registry_cleanup_choices(self) -> list[dict[str, str]]:
        registry = er.async_get(self.hass)
        ignored_ids = self._entry.options.get(CONF_IGNORED_DEVICE_IDS, [])
        choices: list[dict[str, str]] = []

        reason_labels = {
            "legacy_yaml": "Altes YAML" if self._is_de() else "Legacy YAML",
            "registry_only": "Nur Registry" if self._is_de() else "Registry only",
            "ignored": "Ignoriert" if self._is_de() else "Ignored",
        }

        for entry in sorted(
            registry.entities.values(), key=lambda item: item.entity_id
        ):
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
                vol.Optional(
                    CONF_CLEANUP_ENTITY_IDS, default=[]
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=choices,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_CONFIRM_CLEANUP, default=False
                ): selector.BooleanSelector(),
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
                    return self.async_create_entry(
                        title="", data=dict(self._entry.options)
                    )

        return self.async_show_form(
            step_id="ha_cleanup",
            data_schema=schema,
            errors=errors,
            description_placeholders={"count": str(len(choices))},
        )

    async def async_step_about(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=dict(self._entry.options))
        return self.async_show_form(
            step_id="about",
            data_schema=vol.Schema({}),
            description_placeholders={"version": VERSION},
        )
