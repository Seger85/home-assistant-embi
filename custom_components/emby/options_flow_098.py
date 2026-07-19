from __future__ import annotations

import asyncio
import logging

from homeassistant.components import persistent_notification
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_ENABLED_SENSORS,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    DEFAULT_SERVER_CLEANUP_AGE_DAYS,
    SENSOR_ALBUM_COUNT,
    SENSOR_KEYS,
    SENSOR_MOVIE_COUNT,
    SENSOR_SONG_COUNT,
    SENSOR_TV_EPISODE_COUNT,
    SENSOR_TV_SERIES_COUNT,
    SENSOR_USERS_WATCHING,
)
from .maintenance import async_run_automatic_cleanup
from .options_devices_099 import MobilePlayerGroupMixin
from .options_flow import EmbyOptionsFlow as BaseEmbyOptionsFlow
from .options_sensors import SensorsOptionsMixin, remove_disabled_sensor_entities
from .player_action_common import owned_exact
from .player_actions import async_remove_hidden_player_entities

_LOGGER = logging.getLogger(__name__)

_SENSOR_LABELS = {
    SENSOR_MOVIE_COUNT: ("Filme", "Movies"),
    SENSOR_TV_SERIES_COUNT: ("Serien", "TV series"),
    SENSOR_TV_EPISODE_COUNT: ("Episoden", "TV episodes"),
    SENSOR_ALBUM_COUNT: ("Alben", "Albums"),
    SENSOR_SONG_COUNT: ("Songs", "Songs"),
    SENSOR_USERS_WATCHING: ("Aktuell schauende Benutzer", "Users currently watching"),
}


class EmbyOptionsFlow(MobilePlayerGroupMixin, SensorsOptionsMixin, BaseEmbyOptionsFlow):
    """EMBi 0.9.9 Options Flow extension for sensors and cleanup reporting."""

    async def _review_lines(self) -> tuple[list[str], int]:
        lines, count = await super()._review_lines()
        before = {
            str(value)
            for value in self._original_options.get(CONF_ENABLED_SENSORS, list(SENSOR_KEYS))
        }
        after = {
            str(value) for value in self._draft_options.get(CONF_ENABLED_SENSORS, list(SENSOR_KEYS))
        }
        for key in SENSOR_KEYS:
            if (key in before) == (key in after):
                continue
            label = _SENSOR_LABELS[key][0 if self._is_de() else 1]
            old = (
                "Ein"
                if self._is_de() and key in before
                else "Aus"
                if self._is_de()
                else "On"
                if key in before
                else "Off"
            )
            new = (
                "Ein"
                if self._is_de() and key in after
                else "Aus"
                if self._is_de()
                else "On"
                if key in after
                else "Off"
            )
            lines.append(f"{label}\n{old} → {new}")
            count += 1
        return lines, count

    async def async_step_init(self, user_input=None):
        result = await super().async_step_init(user_input)
        menu = list(result["menu_options"])
        if "sensors" not in menu:
            menu.insert(1, "sensors")
        result["menu_options"] = menu
        enabled = self._draft_options.get(CONF_ENABLED_SENSORS, list(SENSOR_KEYS))
        result["description_placeholders"]["sensor_enabled"] = str(len(enabled))
        result["description_placeholders"]["sensor_total"] = str(len(SENSOR_KEYS))
        return result

    def _cleanup_report_placeholders(self) -> dict[str, str]:
        placeholders = super()._cleanup_report_placeholders()
        report = self._runtime.maintenance_state.report
        age_limit = report.age_threshold_days or int(
            self._draft_options.get(
                CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
                DEFAULT_SERVER_CLEANUP_AGE_DAYS,
            )
        )
        placeholders["age_limit"] = str(age_limit)
        return placeholders

    async def _async_finalize_apply(
        self,
        *,
        remove_keys: frozenset[str],
        enable_entity_ids: frozenset[str],
        cleanup_changed: bool,
        updated_auto: bool,
    ) -> None:
        try:
            await asyncio.sleep(0)
            self._runtime.suppress_update_listener = False
            current_entry = (
                self.hass.config_entries.async_get_entry(self._entry.entry_id) or self._entry
            )
            registry = er.async_get(self.hass)
            for entity_id in sorted(enable_entity_ids):
                entity = registry.async_get(entity_id)
                player_key = str(getattr(entity, "unique_id", ""))
                if owned_exact(entity, current_entry, player_key):
                    registry.async_update_entity(entity_id, disabled_by=None)

            reloaded = await self.hass.config_entries.async_reload(self._entry.entry_id)
            if not reloaded:
                raise RuntimeError("EMBi reload after option commit returned false")

            current_entry = (
                self.hass.config_entries.async_get_entry(self._entry.entry_id) or self._entry
            )
            enabled = frozenset(
                str(value)
                for value in current_entry.options.get(CONF_ENABLED_SENSORS, list(SENSOR_KEYS))
            )
            remove_disabled_sensor_entities(self.hass, current_entry, enabled)

            if remove_keys:
                await async_remove_hidden_player_entities(
                    self.hass,
                    current_entry,
                    sorted(remove_keys),
                    prevalidated_non_playing_keys=remove_keys,
                )

            if cleanup_changed and updated_auto:
                reload_needed = await async_run_automatic_cleanup(self.hass, current_entry)
                if reload_needed:
                    await self.hass.config_entries.async_reload(current_entry.entry_id)
        except Exception:
            _LOGGER.exception("EMBi post-apply finalization failed")
            persistent_notification.async_create(
                self.hass,
                (
                    "EMBi hat die Optionen gespeichert, konnte Reload, Registry-Abgleich "
                    "oder die unmittelbare Bereinigung aber nicht vollständig abschließen. "
                    "Details stehen im Home-Assistant-Protokoll und in den EMBi-Diagnosen."
                    if self._is_de()
                    else "EMBi saved the options but could not fully complete reload, registry "
                    "reconciliation, or immediate cleanup. See the Home Assistant log and "
                    "EMBi diagnostics for details."
                ),
                title=(
                    "EMBi-Nachbereitung fehlgeschlagen"
                    if self._is_de()
                    else "EMBi post-processing failed"
                ),
                notification_id=f"emby_apply_failed_{self._entry.entry_id}",
            )
