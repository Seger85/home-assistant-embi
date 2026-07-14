from __future__ import annotations

import logging
from collections.abc import Iterable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .api import EmbyDeviceRecord
from .const import (
    FOLLOW_UP_COMPLETED,
    FOLLOW_UP_INTERRUPTED,
    FOLLOW_UP_PENDING,
    RUN_MODE_AUTOMATIC,
    RUN_STATUS_COMPLETED,
    RUN_STATUS_INTERRUPTED,
    RUN_STATUS_REGISTRY_PENDING,
)
from .maintenance_common import (
    _async_save_state,
    _dismiss_failure,
    _log_report,
    _next_regular_run,
    _notify_failure,
    _set_terminal_status,
    _utc_iso,
)
from .maintenance_registry_commit import apply_exact_registry_removals
from .maintenance_registry_evaluate import evaluate_registry_targets
from .maintenance_registry_queue import _PENDING_REGISTRY_CLEANUP
from .models import EmbiRuntimeData, PendingRegistryTarget, RegistryCleanupResult

_LOGGER = logging.getLogger(__name__)


async def async_apply_pending_registry_cleanup(
    hass: HomeAssistant,
    entry: ConfigEntry,
    current_devices: Iterable[EmbyDeviceRecord],
) -> RegistryCleanupResult:
    """Apply same-process queued registry follow-up after fresh revalidation."""
    runtime: EmbiRuntimeData = entry.runtime_data
    report = runtime.maintenance_state.report
    pending_by_entry = hass.data.get(_PENDING_REGISTRY_CLEANUP, {})
    targets: dict[str, PendingRegistryTarget] = pending_by_entry.pop(entry.entry_id, {})

    if targets and not runtime.maintenance_storage_available:
        report.status = RUN_STATUS_INTERRUPTED
        report.follow_up_status = FOLLOW_UP_INTERRUPTED
        report.last_error = "storage_unavailable_before_registry_followup"
        report.completed_at = _utc_iso()
        _LOGGER.error("EMBi skipped registry follow-up because persistent storage is unavailable")
        _notify_failure(
            hass,
            entry,
            "EMBi hat die Registry-Nachbereitung aus Sicherheitsgründen ausgelassen, "
            "weil der persistente Wartungsstatus nicht verfügbar ist.",
        )
        if not pending_by_entry:
            hass.data.pop(_PENDING_REGISTRY_CLEANUP, None)
        return RegistryCleanupResult(queued=len(targets))

    if not targets:
        if report.status == RUN_STATUS_REGISTRY_PENDING or report.follow_up_status == FOLLOW_UP_PENDING:
            report.status = RUN_STATUS_INTERRUPTED
            report.follow_up_status = FOLLOW_UP_INTERRUPTED
            report.last_error = "registry_followup_interrupted"
            report.completed_at = _utc_iso()
            if report.mode == RUN_MODE_AUTOMATIC:
                report.next_run_at = _next_regular_run()
            await _async_save_state(hass, entry)
            _log_report(report)
            _notify_failure(
                hass,
                entry,
                "Die Registry-Nachbereitung wurde unterbrochen. "
                "Es wurde keine verspätete Registry-Löschung ausgeführt.",
            )
        return RegistryCleanupResult()

    if not pending_by_entry:
        hass.data.pop(_PENDING_REGISTRY_CLEANUP, None)

    registry = er.async_get(hass)
    evaluation = evaluate_registry_targets(
        registry=registry,
        states=hass.states,
        entry=entry,
        current_devices=current_devices,
        targets=targets,
    )
    removed = apply_exact_registry_removals(registry, evaluation.entity_ids_to_remove)
    result = evaluation.result
    if removed != result.removed:
        result = RegistryCleanupResult(
            queued=result.queued,
            matched=result.matched,
            removed=removed,
            missing=result.missing,
            protected_remaining_history=result.protected_remaining_history,
            wrong_entry=result.wrong_entry,
            wrong_platform=result.wrong_platform,
            wrong_unique_id=result.wrong_unique_id,
            state_still_present=result.state_still_present,
            revalidation_ambiguous=result.revalidation_ambiguous,
        )

    report.registry_keys_queued = result.queued
    report.registry_entities_matched = result.matched
    report.registry_entities_removed = result.removed
    report.registry_entities_missing = result.missing
    report.registry_entities_protected_remaining_history += result.protected_remaining_history
    report.registry_entities_wrong_entry = result.wrong_entry
    report.registry_entities_wrong_platform = result.wrong_platform
    report.registry_entities_wrong_unique_id = result.wrong_unique_id
    report.registry_entities_state_still_present = result.state_still_present
    report.registry_entities_revalidation_ambiguous = result.revalidation_ambiguous
    report.follow_up_status = FOLLOW_UP_COMPLETED
    report.completed_at = _utc_iso()
    _set_terminal_status(report)
    if report.mode == RUN_MODE_AUTOMATIC:
        runtime.maintenance_state.initial_run_completed = True
        report.next_run_at = _next_regular_run()

    if not await _async_save_state(hass, entry):
        report.status = RUN_STATUS_INTERRUPTED
        report.follow_up_status = FOLLOW_UP_INTERRUPTED
        report.last_error = "storage_failed_after_registry_followup"
        _log_report(report)
        return result

    _log_report(report)
    if report.status == RUN_STATUS_COMPLETED:
        _dismiss_failure(hass, entry)
    else:
        _notify_failure(
            hass,
            entry,
            "Die EMBi-Bereinigung wurde nur teilweise abgeschlossen. "
            "Details stehen unter ‚Letzter Bereinigungslauf‘ und in den Diagnosedaten.",
        )
    return result
