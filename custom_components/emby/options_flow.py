from __future__ import annotations

import asyncio
import logging
from copy import deepcopy
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import persistent_notification
from homeassistant.helpers import entity_registry as er

from .api import EmbyApiError, EmbyDeviceRecord
from .const import (
    CONF_ALLOWED_DEVICE_IDS,
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_FLOW_ACTION,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_HIDDEN_WHOLE_DEVICES,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_USER_MASTER_VISIBILITY,
    FLOW_ACTION_APPLY,
    FLOW_ACTION_BACK,
    FLOW_ACTION_DISCARD,
)
from .maintenance import async_run_automatic_cleanup
from .models import EmbiRuntimeData
from .options_cleanup import CleanupOptionsMixin
from .options_devices import DevicesOptionsMixin
from .options_draft import OptionsDraft
from .options_ha_cleanup import HomeAssistantCleanupOptionsMixin
from .options_model import migrate_options_090
from .options_navigation import action_selector
from .options_review import semantic_changes
from .options_runtime import fresh_catalog, player_label_map, registry_entries
from .player_action_common import owned_exact
from .player_actions import async_remove_hidden_player_entities
from .player_context import (
    ACTIVE_PLAYBACK_STATES,
    CLIENT_CLASS_TECHNICAL,
    PLAYBACK_UNKNOWN,
    build_player_catalog,
)

_LOGGER = logging.getLogger(__name__)

_ERROR_TEXT_DE = {
    "no_changes": "Es gibt keine ungespeicherten Änderungen.",
    "cannot_connect": "Aktuelle Emby- und Home-Assistant-Daten konnten nicht geladen werden. Bitte erneut versuchen oder zurückgehen.",
    "storage_failed": "Der Wartungsstatus konnte nicht gespeichert werden. Es wurden keine Optionen übernommen.",
    "save_failed": "Die Änderungen konnten nicht sicher gespeichert werden. Es wurde kein Reload ausgeführt.",
}
_ERROR_TEXT_EN = {
    "no_changes": "There are no unsaved changes.",
    "cannot_connect": "Current Emby and Home Assistant data could not be loaded. Try again or go back.",
    "storage_failed": "The maintenance state could not be saved. No options were applied.",
    "save_failed": "The changes could not be saved safely. No reload was performed.",
}


class EmbyOptionsFlow(
    DevicesOptionsMixin,
    CleanupOptionsMixin,
    HomeAssistantCleanupOptionsMixin,
    config_entries.OptionsFlow,
):
    """EMBi 0.9.7 Options Flow with a preserved in-memory draft."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        self._draft = OptionsDraft.from_options(config_entry.options)
        self._original_options = self._draft.original
        self._draft_options = self._draft.current
        self._pending_cleanup_records: dict[str, EmbyDeviceRecord] = {}
        self._pending_cleanup_age_days: int | None = None
        self._pending_cleanup_ignore_age = False
        self._pending_ha_entity_ids: list[str] = []
        self._pending_restore_player_keys: list[str] = []
        self._pending_enable_entity_ids: set[str] = set()
        self._selected_group: str | None = None
        self._selected_player_key: str | None = None
        self._page_by_step: dict[str, int] = {}
        self._review_error: str | None = None
        self._section_error: dict[str, str] = {}
        self._automatic_age_preset: str | None = None
        self._apply_notice = ""

    @property
    def _dirty(self) -> bool:
        return self._draft.dirty or bool(self._pending_enable_entity_ids)

    @property
    def _runtime(self) -> EmbiRuntimeData:
        return self._entry.runtime_data

    def _is_de(self) -> bool:
        return str(self.hass.config.language).lower().startswith("de")

    def _on_off(self, value: bool) -> str:
        if self._is_de():
            return "ein" if value else "aus"
        return "on" if value else "off"

    def _error_text(self, code: str | None) -> str:
        if not code:
            return "-"
        mapping = _ERROR_TEXT_DE if self._is_de() else _ERROR_TEXT_EN
        return mapping.get(code, mapping["cannot_connect"])

    def _change_count_text(self, count: int) -> str:
        if self._is_de():
            return "1 Änderung" if count == 1 else f"{count} Änderungen"
        return "1 change" if count == 1 else f"{count} changes"

    async def _devices(self) -> list[EmbyDeviceRecord]:
        return await self._runtime.api_client.async_get_devices()

    async def _review_lines(self) -> tuple[list[str], int]:
        try:
            players, _stats = await fresh_catalog(self)
            labels = player_label_map(players)
        except Exception:
            _LOGGER.exception("Failed to build EMBi option-review labels")
            labels = {}
        changes = semantic_changes(
            self._original_options,
            self._draft_options,
            player_labels=labels,
            german=self._is_de(),
        )
        lines = [change.render() for change in changes]
        for entity_id in sorted(self._pending_enable_entity_ids):
            lines.append(
                f"{entity_id}\nIn Home Assistant deaktiviert → In Home Assistant aktivieren"
                if self._is_de()
                else f"{entity_id}\nDisabled in Home Assistant → Enable in Home Assistant"
            )
        return lines, len(changes) + len(self._pending_enable_entity_ids)

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        try:
            _players, stats = await fresh_catalog(self)
        except Exception:
            _LOGGER.exception("Failed to build EMBi root-menu statistics")
            stats = None
        menu_options = ["ha_players", "automatic_cleanup", "server_history_check"]
        _lines, count = await self._review_lines()
        if self._dirty:
            menu_options.append("review_changes")
        auto_status = bool(self._draft_options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False))
        auto_age = int(self._draft_options.get(CONF_SERVER_AUTO_CLEANUP_AGE_DAYS, 365))
        next_run = self._format_report_time(
            self._runtime.maintenance_state.report.next_run_at,
            empty="Kein Lauf geplant" if self._is_de() else "No run scheduled",
        )
        return self.async_show_menu(
            step_id="init",
            menu_options=menu_options,
            description_placeholders={
                "server_history": str(stats.server_history_records if stats else 0),
                "ha_players": str(stats.ha_players if stats else 0),
                "protected": str(stats.protected_playback if stats else 0),
                "server_missing": str(stats.server_missing if stats else 0),
                "automatic_cleanup": self._on_off(auto_status),
                "automatic_age": str(auto_age),
                "next_run": next_run,
                "review_count": str(count),
                "apply_notice": self._apply_notice,
            },
        )

    async def async_step_back_to_init(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_init()

    async def async_step_devices_players(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_ha_players(user_input)

    async def async_step_cleanup(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_server_cleanup(user_input)

    async def async_step_review_changes(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            action = user_input.get(CONF_FLOW_ACTION)
            if action == FLOW_ACTION_APPLY:
                return await self.async_step_apply_changes()
            if action == FLOW_ACTION_DISCARD:
                return await self.async_step_discard_changes()
            if action == FLOW_ACTION_BACK:
                return await self.async_step_init()
        if not self._dirty:
            self._review_error = "no_changes"
        lines, count = await self._review_lines()
        return self.async_show_form(
            step_id="review_changes",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FLOW_ACTION): action_selector(
                        [
                            {
                                "value": FLOW_ACTION_APPLY,
                                "label": (
                                    "Änderungen übernehmen" if self._is_de() else "Apply changes"
                                ),
                            },
                            {
                                "value": FLOW_ACTION_DISCARD,
                                "label": (
                                    "Änderungen verwerfen" if self._is_de() else "Discard changes"
                                ),
                            },
                            {
                                "value": FLOW_ACTION_BACK,
                                "label": "\u2039 Zurück" if self._is_de() else "\u2039 Back",
                            },
                        ]
                    )
                }
            ),
            description_placeholders={
                "count": str(count),
                "count_text": self._change_count_text(count),
                "changes": "\n\n".join(lines) or "-",
                "error": self._error_text(self._review_error),
            },
        )

    async def async_step_discard_changes(self, user_input: dict[str, Any] | None = None):
        self._draft.discard()
        self._pending_cleanup_records = {}
        self._pending_cleanup_age_days = None
        self._pending_cleanup_ignore_age = False
        self._pending_ha_entity_ids = []
        self._pending_restore_player_keys = []
        self._pending_enable_entity_ids.clear()
        self._selected_group = None
        self._selected_player_key = None
        self._page_by_step.clear()
        self._review_error = None
        self._section_error.clear()
        return await self.async_step_init()

    async def _async_finalize_apply(
        self,
        *,
        remove_keys: frozenset[str],
        enable_entity_ids: frozenset[str],
        cleanup_changed: bool,
        updated_auto: bool,
    ) -> None:
        # Reload and finish destructive follow-up work after the dialog has closed.
        try:
            # The listener task was scheduled first by async_update_entry.
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

    async def async_step_apply_changes(self, user_input: dict[str, Any] | None = None):
        self._review_error = None
        if not self._dirty:
            self._review_error = "no_changes"
            return await self.async_step_review_changes()
        try:
            devices = await self._devices()
        except EmbyApiError:
            self._review_error = "cannot_connect"
            return await self.async_step_review_changes()

        updated, _ = migrate_options_090(self._draft_options, devices)
        original, _ = migrate_options_090(self._original_options, devices)

        def _catalog(options: dict[str, Any]):
            return build_player_catalog(
                devices,
                registry_entries=registry_entries(self.hass),
                states=self.hass.states,
                entry_id=self._entry.entry_id,
                options=options,
                pyemby_devices=getattr(self._runtime.pyemby, "devices", None),
            )

        original_players = _catalog(original)
        intended_players = _catalog(updated)
        intended_invisible = {
            player.player_key for player in intended_players if not player.visible_in_embi
        }
        protected_keys = {
            player.player_key
            for player in intended_players
            if player.registry_present
            and not player.visible_in_embi
            and (player.playback in ACTIVE_PLAYBACK_STATES or player.playback == PLAYBACK_UNKNOWN)
        }

        if protected_keys:
            hidden = {str(value) for value in updated.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
            hidden_devices = {str(value) for value in updated.get(CONF_HIDDEN_WHOLE_DEVICES, [])}
            user_visibility = updated.get(CONF_USER_MASTER_VISIBILITY, {})
            if not isinstance(user_visibility, dict):
                user_visibility = {}
            user_visibility = dict(user_visibility)

            for player in intended_players:
                if player.player_key not in protected_keys:
                    continue
                hidden.discard(player.player_key)
                if player.reported_device_id and player.reported_device_id in hidden_devices:
                    hidden_devices.discard(player.reported_device_id)
                    hidden.update(
                        other.player_key
                        for other in intended_players
                        if other.player_key in intended_invisible
                        and other.player_key not in protected_keys
                        and other.reported_device_id == player.reported_device_id
                    )
                if len(player.users) == 1 and user_visibility.get(player.users[0]) is False:
                    user_visibility[player.users[0]] = True
                    hidden.update(
                        other.player_key
                        for other in intended_players
                        if other.player_key in intended_invisible
                        and other.player_key not in protected_keys
                        and other.users == player.users
                    )

            if not bool(updated.get(CONF_TECHNICAL_ACCESS_VISIBILITY, False)) and any(
                player.player_key in protected_keys
                and player.client_class == CLIENT_CLASS_TECHNICAL
                for player in intended_players
            ):
                updated[CONF_TECHNICAL_ACCESS_VISIBILITY] = True
                hidden.update(
                    player.player_key
                    for player in intended_players
                    if player.player_key in intended_invisible
                    and player.player_key not in protected_keys
                    and player.client_class == CLIENT_CLASS_TECHNICAL
                )

            updated[CONF_HIDDEN_EXACT_PLAYERS] = sorted(hidden)
            updated[CONF_HIDDEN_WHOLE_DEVICES] = sorted(hidden_devices)
            updated[CONF_USER_MASTER_VISIBILITY] = user_visibility

        if bool(original.get(CONF_AUTO_SHOW_NEW_PLAYERS, True)) and not bool(
            updated.get(CONF_AUTO_SHOW_NEW_PLAYERS, True)
        ):
            allowed = {str(value) for value in updated.get(CONF_ALLOWED_DEVICE_IDS, [])}
            allowed.update(
                player.player_key for player in original_players if player.visible_in_embi
            )
            updated[CONF_ALLOWED_DEVICE_IDS] = sorted(allowed)

        final_players = _catalog(updated)
        remove_keys = {
            player.player_key
            for player in final_players
            if player.registry_present
            and not player.visible_in_embi
            and player.player_key not in protected_keys
            and player.playback not in ACTIVE_PLAYBACK_STATES
            and player.playback != PLAYBACK_UNKNOWN
        }

        cleanup_keys = (
            CONF_SERVER_AUTO_CLEANUP_ENABLED,
            CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
            CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
        )
        cleanup_changed = any(original.get(key) != updated.get(key) for key in cleanup_keys)
        updated_auto = bool(updated.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False))
        if cleanup_changed:
            state = deepcopy(self._runtime.maintenance_state)
            state.report.next_run_at = None
            if updated_auto:
                state.initial_run_completed = False
            try:
                await self._runtime.maintenance_store.async_save(state)
            except Exception:
                self._review_error = "storage_failed"
                return await self.async_step_review_changes()
            self._runtime.maintenance_state = state

        self._runtime.suppress_update_listener = True
        try:
            self.hass.config_entries.async_update_entry(self._entry, options=updated)
        except Exception:
            self._runtime.suppress_update_listener = False
            _LOGGER.exception("Failed to store EMBi options")
            self._review_error = "save_failed"
            return await self.async_step_review_changes()

        self.hass.async_create_task(
            self._async_finalize_apply(
                remove_keys=frozenset(remove_keys),
                enable_entity_ids=frozenset(self._pending_enable_entity_ids),
                cleanup_changed=cleanup_changed,
                updated_auto=updated_auto,
            ),
            "Finalize EMBi option changes after closing the flow",
        )
        return self.async_abort(reason="apply_complete")
