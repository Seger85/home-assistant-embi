from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .api import EmbyApiError, EmbyAuthError
from .cleanup import async_delete_device_records, plan_device_cleanup, plan_registry_followup
from .const import (
    FOLLOW_UP_INTERRUPTED,
    FOLLOW_UP_PENDING,
    RUN_MODE_AUTOMATIC,
    RUN_STATUS_FAILED,
    RUN_STATUS_INTERRUPTED,
    RUN_STATUS_PARTIAL_FAILURE,
    RUN_STATUS_REGISTRY_PENDING,
    RUN_STATUS_RUNNING,
    RUN_STATUS_SERVER_COMPLETED,
)
from .maintenance_common import (
    _async_finish_without_registry,
    _async_save_state,
    _log_report,
    _next_regular_run,
    _notify_failure,
    _utc_iso,
    active_player_keys,
)
from .maintenance_registry_queue import _PENDING_REGISTRY_CLEANUP, queue_registry_cleanup
from .models import CleanupRunReport, EmbiRuntimeData

_LOGGER = logging.getLogger(__name__)


async def _async_execute_cleanup(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    mode: str,
    age_days: int,
    remove_ha_entities: bool,
    selected_record_ids: set[str] | None = None,
) -> tuple[CleanupRunReport, bool]:
    """Run one fail-safe cleanup and return its report and reload requirement."""
    runtime: EmbiRuntimeData = entry.runtime_data
    automatic = mode == RUN_MODE_AUTOMATIC
    lock = runtime.cleanup_lock
    if lock.locked():
        _LOGGER.info("EMBi cleanup skipped because another cleanup is already running")
        return runtime.maintenance_state.report, False

    async with lock:
        report = CleanupRunReport(
            status=RUN_STATUS_RUNNING,
            mode=mode,
            started_at=_utc_iso(),
            age_threshold_days=int(age_days),
        )
        runtime.maintenance_state.report = report
        if not await _async_save_state(hass, entry):
            report.status = RUN_STATUS_FAILED
            report.last_error = "storage_unavailable_before_cleanup"
            report.completed_at = _utc_iso()
            _log_report(report)
            return report, False

        client = runtime.api_client
        try:
            devices = await client.async_get_devices()
        except EmbyAuthError:
            report.status = RUN_STATUS_FAILED
            report.last_error = "authentication_failed"
            report.completed_at = _utc_iso()
            if automatic:
                runtime.maintenance_state.initial_run_completed = True
                report.next_run_at = _next_regular_run()
            await _async_save_state(hass, entry)
            _LOGGER.error("EMBi cleanup failed because authentication was rejected")
            _notify_failure(
                hass, entry, "Die EMBi-Bereinigung konnte nicht authentifiziert werden."
            )
            return report, False
        except EmbyApiError:
            report.status = RUN_STATUS_FAILED
            report.last_error = "device_query_failed"
            report.completed_at = _utc_iso()
            if automatic:
                runtime.maintenance_state.initial_run_completed = True
                report.next_run_at = _next_regular_run()
            await _async_save_state(hass, entry)
            _LOGGER.error("EMBi cleanup failed because the device list was unavailable")
            _notify_failure(hass, entry, "EMBi konnte die Geräteliste nicht sicher abrufen.")
            return report, False

        active = active_player_keys(hass, entry)
        plan = plan_device_cleanup(
            devices,
            now=dt_util.utcnow(),
            age_days=age_days,
            active_player_keys=active,
        )
        report.skipped_active = len(plan.skipped_active)
        report.skipped_without_activity = len(plan.skipped_without_activity)

        candidates = plan.candidates
        if selected_record_ids is not None:
            by_id = {record.record_id: record for record in plan.candidates}
            if not selected_record_ids or any(value not in by_id for value in selected_record_ids):
                report.status = RUN_STATUS_FAILED
                report.last_error = "manual_selection_no_longer_valid"
                report.completed_at = _utc_iso()
                await _async_save_state(hass, entry)
                _LOGGER.error("EMBi manual cleanup selection failed revalidation")
                return report, False
            candidates = tuple(by_id[value] for value in sorted(selected_record_ids))

        report.server_candidates = len(candidates)
        if not await _async_save_state(hass, entry):
            report.status = RUN_STATUS_FAILED
            report.last_error = "storage_unavailable_before_delete"
            report.completed_at = _utc_iso()
            return report, False

        if not candidates:
            await _async_finish_without_registry(hass, entry, automatic=automatic)
            return report, False

        result = await async_delete_device_records(client, candidates)
        report.server_deleted = len(result.succeeded)
        report.server_failed = len(result.failed)
        report.status = RUN_STATUS_SERVER_COMPLETED
        if result.failed:
            report.last_error = "one_or_more_server_deletes_failed"

        if not await _async_save_state(hass, entry):
            report.status = RUN_STATUS_INTERRUPTED
            report.last_error = "storage_failed_after_server_delete"
            report.follow_up_status = FOLLOW_UP_INTERRUPTED
            report.result_counts_complete = False
            report.completed_at = _utc_iso()
            _LOGGER.error(
                "EMBi server cleanup completed but the persistent report could not be saved; registry follow-up was skipped"
            )
            _notify_failure(
                hass,
                entry,
                "EMBi hat die Serverbereinigung verarbeitet "
                f"({report.server_deleted} gelöscht, {report.server_failed} fehlgeschlagen), "
                "konnte den persistenten Laufbericht danach aber nicht sicher speichern. "
                "Die Registry-Nachbereitung wurde ausgelassen.",
            )
            return report, False

        if result.succeeded and remove_ha_entities:
            try:
                remaining = await client.async_get_devices()
            except EmbyApiError:
                report.last_error = "post_delete_revalidation_failed"
                report.status = RUN_STATUS_PARTIAL_FAILURE
                report.follow_up_status = FOLLOW_UP_INTERRUPTED
                await _async_finish_without_registry(hass, entry, automatic=automatic)
                _LOGGER.warning(
                    "EMBi deleted server records but skipped registry follow-up because revalidation failed"
                )
                return report, False

            runtime.devices = remaining
            followup = plan_registry_followup(
                result.succeeded,
                remaining,
                active_player_keys=active_player_keys(hass, entry),
            )
            report.registry_entities_protected_active = len(followup.protected_active_keys)
            report.registry_entities_protected_remaining_history = len(
                followup.protected_remaining_history_keys
            )
            report.registry_keys_queued = queue_registry_cleanup(
                hass,
                entry,
                followup.eligible_keys,
            )
            if report.registry_keys_queued:
                report.status = RUN_STATUS_REGISTRY_PENDING
                report.follow_up_status = FOLLOW_UP_PENDING
                if not await _async_save_state(hass, entry):
                    report.status = RUN_STATUS_INTERRUPTED
                    report.follow_up_status = FOLLOW_UP_INTERRUPTED
                    report.last_error = "storage_failed_before_registry_followup"
                    report.result_counts_complete = False
                    hass.data.get(_PENDING_REGISTRY_CLEANUP, {}).pop(entry.entry_id, None)
                    return report, False
                return report, True

        await _async_finish_without_registry(hass, entry, automatic=automatic)
        return report, False
