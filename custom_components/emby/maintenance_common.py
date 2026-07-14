from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import (
    AUTO_CLEANUP_INTERVAL_HOURS,
    DOMAIN,
    MAINTENANCE_NOTIFICATION_ID_PREFIX,
    RUN_STATUS_COMPLETED,
    RUN_STATUS_FAILED,
    RUN_STATUS_INTERRUPTED,
    RUN_STATUS_PARTIAL_FAILURE,
)
from .helpers import ACTIVE_STATES
from .models import CleanupRunReport, EmbiRuntimeData

_LOGGER = logging.getLogger(__name__)
_CLEANUP_LOCKS = f"{DOMAIN}_cleanup_locks"


def cleanup_lock(hass: HomeAssistant, entry_id: str) -> asyncio.Lock:
    """Return one process-wide cleanup lock per config entry."""
    locks = hass.data.setdefault(_CLEANUP_LOCKS, {})
    return locks.setdefault(entry_id, asyncio.Lock())


def active_player_keys(hass: HomeAssistant, entry: ConfigEntry) -> set[str]:
    """Return exact EMBi player keys that are currently playing or paused."""
    active: set[str] = set()
    runtime = getattr(entry, "runtime_data", None)
    pyemby = getattr(runtime, "pyemby", None)
    for device_id, device in getattr(pyemby, "devices", {}).items():
        if str(getattr(device, "state", "")).casefold() in ACTIVE_STATES:
            active.add(str(device_id))

    registry = er.async_get(hass)
    for entity in registry.entities.values():
        if (
            entity.domain != "media_player"
            or entity.platform != DOMAIN
            or entity.config_entry_id != entry.entry_id
        ):
            continue
        state = hass.states.get(entity.entity_id)
        if state is not None and str(state.state).casefold() in ACTIVE_STATES:
            active.add(str(entity.unique_id))
    return active


def _notification_id(entry: ConfigEntry) -> str:
    return f"{MAINTENANCE_NOTIFICATION_ID_PREFIX}_{entry.entry_id}"


def _notify_failure(hass: HomeAssistant, entry: ConfigEntry, message: str) -> None:
    persistent_notification.async_create(
        hass,
        message,
        title="EMBi-Bereinigung benötigt Aufmerksamkeit",
        notification_id=_notification_id(entry),
    )


def _dismiss_failure(hass: HomeAssistant, entry: ConfigEntry) -> None:
    persistent_notification.async_dismiss(hass, _notification_id(entry))


async def _async_save_state(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Persist runtime maintenance state and fail closed on storage errors."""
    runtime: EmbiRuntimeData = entry.runtime_data
    if runtime.maintenance_store is None:
        runtime.maintenance_storage_available = False
        _LOGGER.error("EMBi maintenance storage is unavailable")
        _notify_failure(
            hass,
            entry,
            "Der persistente EMBi-Wartungsstatus ist nicht verfügbar. "
            "Automatische Löschläufe bleiben aus Sicherheitsgründen angehalten.",
        )
        return False
    try:
        await runtime.maintenance_store.async_save(runtime.maintenance_state)
    except Exception:  # noqa: BLE001
        runtime.maintenance_storage_available = False
        _LOGGER.exception("EMBi failed to persist maintenance state")
        _notify_failure(
            hass,
            entry,
            "EMBi konnte den persistenten Lauf- und Schedulerstatus nicht speichern. "
            "Automatische Löschläufe bleiben aus Sicherheitsgründen angehalten.",
        )
        return False
    runtime.maintenance_storage_available = True
    return True


def _utc_iso(value: datetime | None = None) -> str:
    return (value or dt_util.utcnow()).isoformat()


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return dt_util.as_utc(parsed)


def _next_regular_run(completed_at: datetime | None = None) -> str:
    return _utc_iso((completed_at or dt_util.utcnow()) + timedelta(hours=AUTO_CLEANUP_INTERVAL_HOURS))


def _set_terminal_status(report: CleanupRunReport) -> None:
    if report.last_error or report.server_failed:
        report.status = RUN_STATUS_PARTIAL_FAILURE
    else:
        report.status = RUN_STATUS_COMPLETED


def _log_report(report: CleanupRunReport) -> None:
    message = (
        "EMBi cleanup completed: %s server candidates, %s deleted, %s failed; "
        "%s registry keys queued, %s matched, %s removed, %s missing, %s protected"
    )
    args = (
        report.server_candidates,
        report.server_deleted,
        report.server_failed,
        report.registry_keys_queued,
        report.registry_entities_matched,
        report.registry_entities_removed,
        report.registry_entities_missing,
        report.registry_entities_protected,
    )
    if report.status == RUN_STATUS_FAILED:
        _LOGGER.error(message, *args)
    elif report.status in {RUN_STATUS_PARTIAL_FAILURE, RUN_STATUS_INTERRUPTED}:
        _LOGGER.warning(message, *args)
    else:
        _LOGGER.info(message, *args)
