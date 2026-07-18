from __future__ import annotations

import contextlib
import logging
from collections.abc import Iterable
from dataclasses import dataclass

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


async def _update_options_and_reload(
    hass: HomeAssistant,
    entry: ConfigEntry,
    options: dict,
) -> bool:
    runtime: EmbiRuntimeData = entry.runtime_data
    runtime.suppress_update_listener = True
    try:
        hass.config_entries.async_update_entry(entry, options=options)
    finally:
        runtime.suppress_update_listener = False
    return bool(await hass.config_entries.async_reload(entry.entry_id))


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


async def async_remove_ha_players(
    hass: HomeAssistant,
    entry: ConfigEntry,
    entity_ids: Iterable[str],
) -> PlayerActionResult:
    """Hide exact players, remove their registry entries and verify no recreation."""
    requested_ids = tuple(dict.fromkeys(str(value) for value in entity_ids if value))
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
                "remove",
                len(requested_ids),
                (),
                (),
                tuple(
                    PlayerActionItem(value, "", value, "failed", "refresh_failed")
                    for value in requested_ids
                ),
            )
            await _record_action(hass, entry, action="remove", started_at=started_at, result=result)
            return result

        eligible: list[PlayerContext] = []
        for entity_id in requested_ids:
            context = _find_context(catalog, entity_id=entity_id)
            if context is None:
                failed.append(
                    PlayerActionItem(entity_id, "", entity_id, "failed", "target_changed")
                )
                continue
            item = PlayerActionItem(
                context.entity_id,
                context.player_key,
                context.ha_name,
                "protected",
                context.protected_reason,
            )
            if context.playback in ACTIVE_PLAYBACK_STATES:
                protected.append(item)
                continue
            if not context.removable:
                protected.append(item)
                continue
            eligible.append(context)

        if eligible:
            options = dict(entry.options)
            hidden = {str(value) for value in options.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
            hidden.update(context.player_key for context in eligible)
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
                        context.ha_name,
                        "failed",
                        "hide_reload_failed",
                    )
                    for context in eligible
                )
            else:
                current_entry = hass.config_entries.async_get_entry(entry.entry_id) or entry
                registry = er.async_get(hass)
                removed_keys: set[str] = set()
                for context in eligible:
                    entity = registry.async_get(context.entity_id) if context.entity_id else None
                    if entity is None:
                        candidates = [
                            candidate
                            for candidate in registry.entities.values()
                            if _owned_exact(candidate, current_entry, context.player_key)
                        ]
                        entity = candidates[0] if len(candidates) == 1 else None
                    if entity is not None and not _owned_exact(
                        entity, current_entry, context.player_key
                    ):
                        failed.append(
                            PlayerActionItem(
                                context.entity_id,
                                context.player_key,
                                context.ha_name,
                                "failed",
                                "ownership_changed",
                            )
                        )
                        continue
                    if entity is not None and hass.states.get(entity.entity_id) is not None:
                        failed.append(
                            PlayerActionItem(
                                entity.entity_id,
                                context.player_key,
                                context.ha_name,
                                "failed",
                                "state_still_present",
                            )
                        )
                        continue
                    if entity is not None:
                        registry.async_remove(entity.entity_id)
                    removed_keys.add(context.player_key)

                with contextlib.suppress(Exception):
                    await hass.config_entries.async_reload(entry.entry_id)
                registry = er.async_get(hass)
                for context in eligible:
                    if context.player_key not in removed_keys:
                        continue
                    still_registered = any(
                        _owned_exact(candidate, current_entry, context.player_key)
                        for candidate in registry.entities.values()
                    )
                    still_loaded = any(
                        state is not None
                        for state in (
                            hass.states.get(context.entity_id) if context.entity_id else None,
                        )
                    )
                    if still_registered or still_loaded:
                        failed.append(
                            PlayerActionItem(
                                context.entity_id,
                                context.player_key,
                                context.ha_name,
                                "failed",
                                "verification_failed",
                            )
                        )
                    else:
                        succeeded.append(
                            PlayerActionItem(
                                context.entity_id,
                                context.player_key,
                                context.ha_name,
                                "removed",
                            )
                        )

    result = PlayerActionResult(
        "remove",
        len(requested_ids),
        tuple(succeeded),
        tuple(protected),
        tuple(failed),
    )
    await _record_action(hass, entry, action="remove", started_at=started_at, result=result)
    _LOGGER.log(
        logging.INFO if result.status == "completed" else logging.WARNING,
        "EMBi HA player removal: %s requested, %s removed, %s protected, %s failed",
        result.requested,
        len(result.succeeded),
        len(result.protected),
        len(result.failed),
    )
    return result


async def async_restore_players(
    hass: HomeAssistant,
    entry: ConfigEntry,
    player_keys: Iterable[str],
) -> PlayerActionResult:
    """Remove only exact hidden rules, reload and verify the resulting entity."""
    keys = tuple(dict.fromkeys(str(value) for value in player_keys if value))
    started_at = dt_util.utcnow().isoformat()
    runtime: EmbiRuntimeData = entry.runtime_data
    succeeded: list[PlayerActionItem] = []
    failed: list[PlayerActionItem] = []

    async with runtime.cleanup_lock:
        options = dict(entry.options)
        hidden = {str(value) for value in options.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
        for key in keys:
            hidden.discard(key)
        options[CONF_HIDDEN_EXACT_PLAYERS] = sorted(hidden)
        try:
            reloaded = await _update_options_and_reload(hass, entry, options)
        except Exception:
            reloaded = False
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
                PlayerActionItem(None, key, "Emby player", "failed", "reload_failed")
                for key in keys
            )

    result = PlayerActionResult("restore", len(keys), tuple(succeeded), (), tuple(failed))
    await _record_action(hass, entry, action="restore", started_at=started_at, result=result)
    _LOGGER.log(
        logging.INFO if result.status == "completed" else logging.WARNING,
        "EMBi player restore: %s requested, %s restored, %s failed",
        result.requested,
        len(result.succeeded),
        len(result.failed),
    )
    return result


async def async_enable_ha_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    entity_ids: Iterable[str],
) -> PlayerActionResult:
    """Enable exact disabled EMBi entities without changing identity or metadata."""
    ids = tuple(dict.fromkeys(str(value) for value in entity_ids if value))
    started_at = dt_util.utcnow().isoformat()
    registry = er.async_get(hass)
    succeeded: list[PlayerActionItem] = []
    failed: list[PlayerActionItem] = []
    runtime: EmbiRuntimeData = entry.runtime_data
    async with runtime.cleanup_lock:
        for entity_id in ids:
            entity = registry.async_get(entity_id)
            if not _owned_exact(entity, entry, str(getattr(entity, "unique_id", ""))):
                failed.append(
                    PlayerActionItem(entity_id, "", entity_id, "failed", "ownership_changed")
                )
                continue
            registry.async_update_entity(entity_id, disabled_by=None)
            succeeded.append(
                PlayerActionItem(
                    entity_id,
                    str(entity.unique_id),
                    entity.name or entity.original_name or entity_id,
                    "enabled",
                )
            )
        if succeeded:
            await hass.config_entries.async_reload(entry.entry_id)
    result = PlayerActionResult("enable", len(ids), tuple(succeeded), (), tuple(failed))
    await _record_action(hass, entry, action="enable", started_at=started_at, result=result)
    return result


async def async_remove_hidden_player_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    player_keys: Iterable[str],
    *,
    prevalidated_non_playing_keys: Iterable[str] = (),
) -> PlayerActionResult:
    """Remove exact registry entities after their hidden options were committed."""
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
                "remove",
                len(keys),
                (),
                (),
                tuple(
                    PlayerActionItem(None, key, "Emby player", "failed", "refresh_failed")
                    for key in keys
                ),
            )
            await _record_action(hass, entry, action="remove", started_at=started_at, result=result)
            return result

        registry = er.async_get(hass)
        for key in keys:
            context = _find_context(catalog, player_key=key)
            if context is None or not context.registry_present:
                succeeded.append(
                    PlayerActionItem(
                        None, key, context.ha_name if context else "Emby player", "removed"
                    )
                )
                continue
            item = PlayerActionItem(
                context.entity_id,
                context.player_key,
                context.ha_name,
                "protected",
                context.protected_reason,
            )
            if context.playback in ACTIVE_PLAYBACK_STATES or (
                context.playback == PLAYBACK_UNKNOWN and key not in prevalidated
            ):
                protected.append(item)
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
                succeeded.append(PlayerActionItem(None, key, context.ha_name, "removed"))
                continue
            if not _owned_exact(entity, entry, key):
                failed.append(
                    PlayerActionItem(
                        entity.entity_id,
                        key,
                        context.ha_name,
                        "failed",
                        "ownership_changed",
                    )
                )
                continue
            if hass.states.get(entity.entity_id) is not None:
                failed.append(
                    PlayerActionItem(
                        entity.entity_id,
                        key,
                        context.ha_name,
                        "failed",
                        "state_still_present",
                    )
                )
                continue
            registry.async_remove(entity.entity_id)
            if any(_owned_exact(candidate, entry, key) for candidate in registry.entities.values()):
                failed.append(
                    PlayerActionItem(
                        entity.entity_id,
                        key,
                        context.ha_name,
                        "failed",
                        "verification_failed",
                    )
                )
            else:
                succeeded.append(
                    PlayerActionItem(entity.entity_id, key, context.ha_name, "removed")
                )

    result = PlayerActionResult(
        "remove",
        len(keys),
        tuple(succeeded),
        tuple(protected),
        tuple(failed),
    )
    await _record_action(hass, entry, action="remove", started_at=started_at, result=result)
    _LOGGER.log(
        logging.INFO if result.status == "completed" else logging.WARNING,
        "EMBi hidden-player reconciliation: %s requested, %s removed, %s protected, %s failed",
        result.requested,
        len(result.succeeded),
        len(result.protected),
        len(result.failed),
    )
    return result
