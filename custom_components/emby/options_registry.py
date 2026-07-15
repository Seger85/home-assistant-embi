from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    CONF_CLEANUP_ENTITY_IDS,
    CONF_CONFIRM_CLEANUP,
    CONF_IGNORED_PLAYER_KEYS,
    CONF_IGNORED_REPORTED_DEVICE_IDS,
    DOMAIN,
)
from .helpers import registry_cleanup_reason, reported_device_id_for_player_key
from .registry_operations import remove_exact_registry_entity


class RegistryOptionsMixin:
    def _registry_cleanup_choices(self) -> list[dict[str, str]]:
        registry = er.async_get(self.hass)
        choices: list[dict[str, str]] = []
        reason_labels = {
            "legacy_yaml": "Altes YAML" if self._is_de() else "Legacy YAML",
            "registry_only": "Nur Registry" if self._is_de() else "Registry only",
            "ignored": "Ignoriert" if self._is_de() else "Ignored",
        }
        for entity in sorted(registry.entities.values(), key=lambda item: item.entity_id):
            if entity.domain != "media_player" or entity.platform != DOMAIN:
                continue
            unique_id = str(entity.unique_id)
            reason = registry_cleanup_reason(
                has_state=self.hass.states.get(entity.entity_id) is not None,
                config_entry_id=entity.config_entry_id,
                target_entry_id=self._entry.entry_id,
                unique_id=unique_id,
                reported_device_id=reported_device_id_for_player_key(
                    self._runtime.devices, unique_id
                ),
                ignored_player_keys=self._entry.options.get(CONF_IGNORED_PLAYER_KEYS, []),
                ignored_reported_device_ids=self._entry.options.get(
                    CONF_IGNORED_REPORTED_DEVICE_IDS, []
                ),
            )
            if reason is None:
                continue
            label = entity.name or entity.original_name or entity.entity_id
            choices.append(
                {
                    "value": entity.entity_id,
                    "label": f"{label} · {reason_labels[reason]} · {unique_id}",
                }
            )
        return choices

    async def async_step_ha_cleanup(self, user_input: dict[str, Any] | None = None):
        if self._dirty:
            return self.async_abort(reason="unsaved_changes")
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
                revalidated = {choice["value"] for choice in self._registry_cleanup_choices()}
                if any(entity_id not in revalidated for entity_id in selected):
                    errors["base"] = "invalid_selection"
                else:
                    removed = 0
                    for entity_id in selected:
                        if registry.async_get(entity_id) is not None:
                            remove_exact_registry_entity(registry, entity_id)
                            removed += 1
                    return self.async_abort(
                        reason="ha_cleanup_complete",
                        description_placeholders={"removed_count": str(removed)},
                    )
        return self.async_show_form(
            step_id="ha_cleanup",
            data_schema=schema,
            errors=errors,
            description_placeholders={"count": str(len(choices))},
        )
