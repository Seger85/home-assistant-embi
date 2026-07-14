from __future__ import annotations

from typing import Any

from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_IGNORED_PLAYER_KEYS,
    CONF_IGNORED_REPORTED_DEVICE_IDS,
    DOMAIN,
)
from .helpers import registry_cleanup_reason, reported_device_id_for_player_key


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
        from .options_registry_action import async_handle_registry_action

        return await async_handle_registry_action(self, user_input)
