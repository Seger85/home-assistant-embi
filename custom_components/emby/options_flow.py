from __future__ import annotations

from copy import deepcopy
from typing import Any

from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er

from .api import EmbyApiError, EmbyDeviceRecord
from .const import (
    CONF_ALLOWED_DEVICE_IDS,
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_USER_MASTER_VISIBILITY,
)
from .models import EmbiRuntimeData
from .options_cleanup import CleanupOptionsMixin
from .options_devices import DevicesOptionsMixin
from .options_draft import OptionsDraft
from .options_ha_cleanup import HomeAssistantCleanupOptionsMixin
from .options_model import migrate_options_090
from .options_review import semantic_changes
from .options_runtime import fresh_catalog, player_label_map
from .player_action_common import owned_exact
from .player_context import ACTIVE_PLAYBACK_STATES, CLIENT_CLASS_TECHNICAL

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
    """EMBi 0.9.1 Options Flow with a preserved in-memory draft."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        self._draft = OptionsDraft.from_options(config_entry.options)
        self._original_options = self._draft.original
        self._draft_options = self._draft.current
        self._pending_cleanup_records: dict[str, EmbyDeviceRecord] = {}
        self._pending_cleanup_age_days: int | None = None
        self._pending_ha_entity_ids: list[str] = []
        self._pending_restore_player_keys: list[str] = []
        self._pending_enable_entity_ids: set[str] = set()
        self._selected_group: str | None = None
        self._selected_player_key: str | None = None
        self._search_query = ""
        self._page_by_step: dict[str, int] = {}
        self._review_error: str | None = None
        self._section_error: dict[str, str] = {}
        self._manual_age_preset: str | None = None
        self._automatic_age_preset: str | None = None

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
            stats = None
        menu_options = ["ha_players", "server_cleanup"]
        _lines, count = await self._review_lines()
        if self._dirty:
            menu_options.append("review_changes")
        auto_status = bool(self._draft_options.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False))
        return self.async_show_menu(
            step_id="init",
            menu_options=menu_options,
            description_placeholders={
                "server_history": str(stats.server_history_records if stats else 0),
                "ha_players": str(stats.ha_players if stats else 0),
                "protected": str(stats.protected_playback if stats else 0),
                "server_missing": str(stats.server_missing if stats else 0),
                "automatic_cleanup": self._on_off(auto_status),
                "review_count": str(count),
            },
        )

    async def async_step_back_to_init(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_init()

    async def async_step_devices_players(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_ha_players(user_input)

    async def async_step_cleanup(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_server_cleanup(user_input)

    async def async_step_review_changes(self, user_input: dict[str, Any] | None = None):
        if not self._dirty:
            self._review_error = "no_changes"
        lines, count = await self._review_lines()
        return self.async_show_menu(
            step_id="review_changes",
            menu_options=["apply_changes", "discard_changes", "back_to_init"],
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
        self._pending_ha_entity_ids = []
        self._pending_restore_player_keys = []
        self._pending_enable_entity_ids.clear()
        self._selected_group = None
        self._selected_player_key = None
        self._search_query = ""
        self._page_by_step.clear()
        self._review_error = None
        self._section_error.clear()
        return await self.async_step_init()

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
        try:
            players, _stats = await fresh_catalog(self)
        except Exception:
            self._review_error = "cannot_connect"
            return await self.async_step_review_changes()

        before_hidden = {str(value) for value in original.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
        after_hidden = {str(value) for value in updated.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
        hide_keys = after_hidden - before_hidden
        restore_keys = before_hidden - after_hidden
        protected_keys = {
            player.player_key
            for player in players
            if player.player_key in hide_keys and player.playback in ACTIVE_PLAYBACK_STATES
        }

        original_technical = bool(original.get(CONF_TECHNICAL_ACCESS_VISIBILITY, False))
        updated_technical = bool(updated.get(CONF_TECHNICAL_ACCESS_VISIBILITY, False))
        protected_technical = {
            player.player_key
            for player in players
            if player.client_class == CLIENT_CLASS_TECHNICAL
            and player.playback in ACTIVE_PLAYBACK_STATES
        }
        if original_technical and not updated_technical and protected_technical:
            updated[CONF_TECHNICAL_ACCESS_VISIBILITY] = True
            protected_keys.update(protected_technical)

        original_user_visibility = original.get(CONF_USER_MASTER_VISIBILITY, {})
        if not isinstance(original_user_visibility, dict):
            original_user_visibility = {}
        user_visibility = updated.get(CONF_USER_MASTER_VISIBILITY, {})
        if not isinstance(user_visibility, dict):
            user_visibility = {}
        user_visibility = dict(user_visibility)
        for player in players:
            if len(player.users) != 1 or player.playback not in ACTIVE_PLAYBACK_STATES:
                continue
            user_name = player.users[0]
            if (
                original_user_visibility.get(user_name, True)
                and user_visibility.get(user_name, True) is False
            ):
                user_visibility[user_name] = True
                protected_keys.add(player.player_key)
        updated[CONF_USER_MASTER_VISIBILITY] = user_visibility

        if bool(original.get(CONF_AUTO_SHOW_NEW_PLAYERS, True)) and not bool(
            updated.get(CONF_AUTO_SHOW_NEW_PLAYERS, True)
        ):
            allowed = {str(value) for value in updated.get(CONF_ALLOWED_DEVICE_IDS, [])}
            allowed.update(player.player_key for player in players if player.visible_in_embi)
            updated[CONF_ALLOWED_DEVICE_IDS] = sorted(allowed)

        if protected_keys:
            after_hidden -= protected_keys
            updated[CONF_HIDDEN_EXACT_PLAYERS] = sorted(after_hidden)

        original_auto = bool(original.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False))
        updated_auto = bool(updated.get(CONF_SERVER_AUTO_CLEANUP_ENABLED, False))
        if original_auto != updated_auto:
            state = deepcopy(self._runtime.maintenance_state)
            if updated_auto:
                state.initial_run_completed = False
            state.report.next_run_at = None
            try:
                await self._runtime.maintenance_store.async_save(state)
            except Exception:
                self._review_error = "storage_failed"
                return await self.async_step_review_changes()
            self._runtime.maintenance_state = state

        self._runtime.suppress_update_listener = True
        try:
            self.hass.config_entries.async_update_entry(self._entry, options=updated)
            blocker = getattr(self.hass, "async_block_till_done", None)
            if blocker is not None:
                await blocker()
        except Exception:
            self._review_error = "save_failed"
            return await self.async_step_review_changes()
        finally:
            self._runtime.suppress_update_listener = False

        enabled = failed = 0
        registry = er.async_get(self.hass)
        for entity_id in sorted(self._pending_enable_entity_ids):
            entity = registry.async_get(entity_id)
            player_key = str(getattr(entity, "unique_id", ""))
            if not owned_exact(entity, self._entry, player_key):
                failed += 1
                continue
            registry.async_update_entity(entity_id, disabled_by=None)
            enabled += 1

        try:
            await self.hass.config_entries.async_reload(self._entry.entry_id)
        except Exception:
            failed += len(restore_keys)
        current_entry = self.hass.config_entries.async_get_entry(self._entry.entry_id) or self._entry
        registry = er.async_get(self.hass)
        restored = sum(
            any(owned_exact(entity, current_entry, player_key) for entity in registry.entities.values())
            for player_key in restore_keys
        )
        failed += max(0, len(restore_keys) - restored)

        return self.async_abort(
            reason="apply_complete",
            description_placeholders={
                "removed": "0",
                "restored": str(restored),
                "enabled": str(enabled),
                "protected": str(len(protected_keys)),
                "failed": str(failed),
            },
        )
