from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import CONF_HIDDEN_EXACT_PLAYERS, DOMAIN
from .maintenance_common import _async_save_state
from .models import EmbiRuntimeData, MaintenanceActionSummary
from .player_context import (
    ACTIVE_PLAYBACK_STATES,
    PLAYBACK_UNKNOWN,
    PlayerContext,
    build_player_catalog,
)
from .registry_state import state_can_be_removed_after_visibility_commit

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PlayerActionItem:
    entity_id: str | None
    player_key: str
    friendly_name: str
    status: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class PlayerActionResult:
    action: str
    requested: int
    succeeded: tuple[PlayerActionItem, ...]
    protected: tuple[PlayerActionItem, ...]
    failed: tuple[PlayerActionItem, ...]

    @property
    def status(self) -> str:
        if self.failed or self.protected:
            return "partial" if self.succeeded else "failed"
        return "completed"


def _registry_entries(registry: er.EntityRegistry) -> list[object]:
    return list(registry.entities.values())


def _find_context(
    contexts: Iterable[PlayerContext],
    *,
    entity_id: str | None = None,
    player_key: str | None = None,
) -> PlayerContext | None:
    for context in contexts:
        if entity_id is not None and context.entity_id == entity_id:
            return context
        if player_key is not None and context.player_key == player_key:
            return context
    return None


async def _fresh_catalog(hass: HomeAssistant, entry: ConfigEntry) -> list[PlayerContext]:
    runtime: EmbiRuntimeData = entry.runtime_data
    records = await runtime.api_client.async_get_devices()
    runtime.devices = records
    registry = er.async_get(hass)
    return build_player_catalog(
        records,
        registry_entries=_registry_entries(registry),
        states=hass.states,
        entry_id=entry.entry_id,
        options=entry.options,
        pyemby_devices=getattr(runtime.pyemby, "devices", None),
    )


async def _fresh_sessions(entry: ConfigEntry) -> tuple[list[dict[str, Any]], bool]:
    """Fetch current sessions without treating an API failure as inactivity."""
    runtime: EmbiRuntimeData = entry.runtime_data
    try:
        raw = await runtime.api_client._request("GET", "/Sessions")
    except Exception:
        return [], False
    if not isinstance(raw, list) or any(not isinstance(item, dict) for item in raw):
        return [], False
    return raw, True


def _session_matches(context: PlayerContext, session: dict[str, Any]) -> bool:
    device_id = str(session.get("DeviceId") or session.get("Device", {}).get("Id") or "")
    client = str(session.get("Client") or session.get("AppName") or "")
    if context.reported_device_id and device_id:
        if context.reported_device_id.casefold() != device_id.casefold():
            return False
    elif device_id and device_id.casefold() not in context.player_key.casefold():
        return False
    if client and context.app_name and client.casefold() != context.app_name.casefold():
        return False
    return bool(device_id or client)


def _session_is_playing_or_paused(session: dict[str, Any]) -> bool:
    if not isinstance(session.get("NowPlayingItem"), dict):
        return False
    play_state = session.get("PlayState")
    return isinstance(play_state, dict) and isinstance(play_state.get("IsPaused"), bool)


async def _unknown_is_safe(
    entry: ConfigEntry,
    context: PlayerContext,
    sessions_cache: tuple[list[dict[str, Any]], bool] | None,
) -> tuple[bool, tuple[list[dict[str, Any]], bool]]:
    sessions, reliable = sessions_cache or await _fresh_sessions(entry)
    if not reliable:
        return False, (sessions, reliable)
    blocked = any(
        _session_matches(context, session) and _session_is_playing_or_paused(session)
        for session in sessions
    )
    return not blocked, (sessions, reliable)


def _owned_exact(entity: object | None, entry: ConfigEntry, player_key: str) -> bool:
    return bool(
        entity is not None
        and getattr(entity, "domain", None) == "media_player"
        and getattr(entity, "platform", None) == DOMAIN
        and getattr(entity, "config_entry_id", None) == entry.entry_id
        and str(getattr(entity, "unique_id", "")) == player_key
    )


async def _record_action(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    action: str,
    started_at: str,
    result: PlayerActionResult,
) -> None:
    runtime: EmbiRuntimeData = entry.runtime_data
    summary = MaintenanceActionSummary(
        action=action,
        status=result.status,
        started_at=started_at,
        completed_at=dt_util.utcnow().isoformat(),
        requested=result.requested,
        succeeded=len(result.succeeded),
        protected=len(result.protected),
        failed=len(result.failed),
        reason_codes=tuple(
            sorted({item.reason for item in (*result.protected, *result.failed) if item.reason})
        ),
    )
    if action == "restore":
        runtime.maintenance_state.last_restore = summary
    else:
        runtime.maintenance_state.last_player_action = summary
    await _async_save_state(hass, entry)


async def _update_options_and_reload(
    hass: HomeAssistant,
    entry: ConfigEntry,
    options: dict[str, Any],
) -> bool:
    runtime: EmbiRuntimeData = entry.runtime_data
    runtime.suppress_update_listener = True
    try:
        hass.config_entries.async_update_entry(entry, options=options)
    finally:
        runtime.suppress_update_listener = False
    return bool(await hass.config_entries.async_reload(entry.entry_id))


async def async_remove_hidden_player_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    player_keys: Iterable[str],
    *,
    prevalidated_non_playing_keys: Iterable[str] = (),
    action: str = "remove",
) -> PlayerActionResult:
    """Remove exact hidden EMBi entities after fresh playback and ownership checks."""
    keys = tuple(dict.fromkeys(str(value) for value in player_keys if value))
    prevalidated = {str(value) for value in prevalidated_non_playing_keys}
    started_at = dt_util.utcnow().isoformat()
    runtime: EmbiRuntimeData = entry.runtime_data
    succeeded: list[PlayerActionItem] = []
    protected: list[PlayerActionItem] = []
    failed: list[PlayerActionItem] = []

    async with runtime.cleanup_lock:
        try:
            catalog = await _fresh_catalog(hass, entry)
        except Exception:
            result = PlayerActionResult(
                action,
                len(keys),
                (),
                (),
                tuple(
                    PlayerActionItem(None, key, "Emby player", "failed", "refresh_failed")
                    for key in keys
                ),
            )
            await _record_action(hass, entry, action=action, started_at=started_at, result=result)
            return result

        registry = er.async_get(hass)
        sessions_cache: tuple[list[dict[str, Any]], bool] | None = None
        for key in keys:
            context = _find_context(catalog, player_key=key)
            if context is None or not context.registry_present:
                succeeded.append(
                    PlayerActionItem(
                        None,
                        key,
                        context.ha_name if context else "Emby player",
                        "removed",
                    )
                )
                continue

            item = PlayerActionItem(
                context.entity_id,
                context.player_key,
                context.selector_label,
                "protected",
                context.protected_reason,
            )
            if context.playback in ACTIVE_PLAYBACK_STATES:
                protected.append(
                    PlayerActionItem(
                        item.entity_id,
                        item.player_key,
                        item.friendly_name,
                        "protected",
                        context.playback,
                    )
                )
                continue
            if context.playback == PLAYBACK_UNKNOWN and key not in prevalidated:
                safe, sessions_cache = await _unknown_is_safe(entry, context, sessions_cache)
                if not safe:
                    protected.append(
                        PlayerActionItem(
                            item.entity_id,
                            item.player_key,
                            item.friendly_name,
                            "protected",
                            "playback_revalidation_failed",
                        )
                    )
                    continue

            entity = registry.async_get(context.entity_id) if context.entity_id else None
            if entity is None:
                matches = [
                    candidate
                    for candidate in registry.entities.values()
                    if _owned_exact(candidate, entry, key)
                ]
                entity = matches[0] if len(matches) == 1 else None
            if entity is None:
                succeeded.append(PlayerActionItem(None, key, context.selector_label, "removed"))
                continue
            if not _owned_exact(entity, entry, key):
                failed.append(
                    PlayerActionItem(
                        entity.entity_id,
                        key,
                        context.selector_label,
                        "failed",
                        "ownership_changed",
                    )
                )
                continue

            state = hass.states.get(entity.entity_id)
            if not state_can_be_removed_after_visibility_commit(state):
                failed.append(
                    PlayerActionItem(
                        entity.entity_id,
                        key,
                        context.selector_label,
                        "failed",
                        "state_still_present",
                    )
                )
                continue
            if state is not None:
                hass.states.async_remove(entity.entity_id)
            registry.async_remove(entity.entity_id)
            if hass.states.get(entity.entity_id) is not None or any(
                _owned_exact(candidate, entry, key) for candidate in registry.entities.values()
            ):
                failed.append(
                    PlayerActionItem(
                        entity.entity_id,
                        key,
                        context.selector_label,
                        "failed",
                        "verification_failed",
                    )
                )
            else:
                succeeded.append(
                    PlayerActionItem(entity.entity_id, key, context.selector_label, "removed")
                )

    result = PlayerActionResult(
        action,
        len(keys),
        tuple(succeeded),
        tuple(protected),
        tuple(failed),
    )
    await _record_action(hass, entry, action=action, started_at=started_at, result=result)
    _LOGGER.log(
        logging.INFO if result.status == "completed" else logging.WARNING,
        "EMBi player lifecycle: %s requested, %s removed, %s protected, %s failed",
        result.requested,
        len(result.succeeded),
        len(result.protected),
        len(result.failed),
    )
    return result


async def async_remove_ha_players(
    hass: HomeAssistant,
    entry: ConfigEntry,
    entity_ids: Iterable[str],
) -> PlayerActionResult:
    """Commit exact hidden rules, reload once, then reconcile the selected entities."""
    requested_ids = tuple(dict.fromkeys(str(value) for value in entity_ids if value))
    try:
        catalog = await _fresh_catalog(hass, entry)
    except Exception:
        return PlayerActionResult(
            "remove",
            len(requested_ids),
            (),
            (),
            tuple(
                PlayerActionItem(value, "", value, "failed", "refresh_failed")
                for value in requested_ids
            ),
        )

    selected: list[PlayerContext] = []
    protected: list[PlayerActionItem] = []
    failed: list[PlayerActionItem] = []
    for entity_id in requested_ids:
        context = _find_context(catalog, entity_id=entity_id)
        if context is None:
            failed.append(PlayerActionItem(entity_id, "", entity_id, "failed", "target_changed"))
            continue
        if context.playback in ACTIVE_PLAYBACK_STATES:
            protected.append(
                PlayerActionItem(
                    context.entity_id,
                    context.player_key,
                    context.selector_label,
                    "protected",
                    context.playback,
                )
            )
            continue
        selected.append(context)

    if not selected:
        return PlayerActionResult("remove", len(requested_ids), (), tuple(protected), tuple(failed))

    options = dict(entry.options)
    hidden = {str(value) for value in options.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
    hidden.update(context.player_key for context in selected)
    options[CONF_HIDDEN_EXACT_PLAYERS] = sorted(hidden)
    try:
        reloaded = await _update_options_and_reload(hass, entry, options)
    except Exception:
        reloaded = False
    if not reloaded:
        failed.extend(
            PlayerActionItem(
                context.entity_id,
                context.player_key,
                context.selector_label,
                "failed",
                "hide_reload_failed",
            )
            for context in selected
        )
        return PlayerActionResult("remove", len(requested_ids), (), tuple(protected), tuple(failed))

    current_entry = hass.config_entries.async_get_entry(entry.entry_id) or entry
    reconciled = await async_remove_hidden_player_entities(
        hass,
        current_entry,
        (context.player_key for context in selected),
        action="remove",
    )
    return PlayerActionResult(
        "remove",
        len(requested_ids),
        reconciled.succeeded,
        tuple((*protected, *reconciled.protected)),
        tuple((*failed, *reconciled.failed)),
    )


async def async_restore_players(
    hass: HomeAssistant,
    entry: ConfigEntry,
    player_keys: Iterable[str],
) -> PlayerActionResult:
    """Remove exact hidden rules, reload once and verify stable unique IDs."""
    keys = tuple(dict.fromkeys(str(value) for value in player_keys if value))
    started_at = dt_util.utcnow().isoformat()
    options = dict(entry.options)
    hidden = {str(value) for value in options.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
    for key in keys:
        hidden.discard(key)
    options[CONF_HIDDEN_EXACT_PLAYERS] = sorted(hidden)
    try:
        reloaded = await _update_options_and_reload(hass, entry, options)
    except Exception:
        reloaded = False

    succeeded: list[PlayerActionItem] = []
    failed: list[PlayerActionItem] = []
    if reloaded:
        current_entry = hass.config_entries.async_get_entry(entry.entry_id) or entry
        registry = er.async_get(hass)
        for key in keys:
            matches = [
                entity
                for entity in registry.entities.values()
                if _owned_exact(entity, current_entry, key)
            ]
            if len(matches) == 1:
                entity = matches[0]
                succeeded.append(
                    PlayerActionItem(
                        entity.entity_id,
                        key,
                        entity.name or entity.original_name or entity.entity_id,
                        "restored",
                    )
                )
            else:
                failed.append(
                    PlayerActionItem(None, key, "Emby player", "failed", "verification_failed")
                )
    else:
        failed.extend(
            PlayerActionItem(None, key, "Emby player", "failed", "reload_failed") for key in keys
        )

    result = PlayerActionResult("restore", len(keys), tuple(succeeded), (), tuple(failed))
    await _record_action(hass, entry, action="restore", started_at=started_at, result=result)
    return result
