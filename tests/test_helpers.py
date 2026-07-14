from __future__ import annotations

from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.const import (
    CLIENT_MODE_ACTIVE_ONLY,
    CLIENT_MODE_ALL,
    CLIENT_MODE_ALLOWLIST,
    CONF_ALLOWED_DEVICE_IDS,
    CONF_IGNORED_DEVICE_IDS,
)
from custom_components.emby.helpers import (
    identifier_matches,
    migrate_legacy_device_options,
    registry_cleanup_reason,
    server_device_selector_options,
    should_expose_device,
    unique_player_keys,
    unique_reported_device_ids,
)


def _device() -> EmbyDeviceRecord:
    return EmbyDeviceRecord.from_api(
        {
            "Id": "341",
            "ReportedDeviceId": "client-1",
            "Name": "Living room",
            "AppName": "Emby Windows",
        }
    )


def test_raw_client_id_matches_all_app_variants() -> None:
    assert identifier_matches("client-1.Emby Windows", ["client-1"])
    assert identifier_matches("client-1.Emby Web", ["client-1"])
    assert not identifier_matches("client-2.Emby Windows", ["client-1"])


def test_ignore_list_always_wins() -> None:
    assert not should_expose_device(
        device_id="client-1.Emby Windows",
        state="Playing",
        mode=CLIENT_MODE_ALL,
        allowed_ids=[],
        ignored_ids=["client-1"],
    )
    assert not should_expose_device(
        device_id="client-1.Emby Windows",
        state="Playing",
        mode=CLIENT_MODE_ALLOWLIST,
        allowed_ids=["client-1.Emby Windows"],
        ignored_ids=["client-1"],
    )


def test_allowlist_requires_selected_identity() -> None:
    assert should_expose_device(
        device_id="client-1.Emby Windows",
        state="Idle",
        mode=CLIENT_MODE_ALLOWLIST,
        allowed_ids=["client-1.Emby Windows"],
        ignored_ids=[],
    )
    assert not should_expose_device(
        device_id="client-2.Emby Windows",
        state="Idle",
        mode=CLIENT_MODE_ALLOWLIST,
        allowed_ids=["client-1.Emby Windows"],
        ignored_ids=[],
    )


def test_active_mode_accepts_playing_and_paused_case_insensitively() -> None:
    for state in ("Playing", "playing", "Paused", "paused"):
        assert should_expose_device(
            device_id="client-1.Emby Windows",
            state=state,
            mode=CLIENT_MODE_ACTIVE_ONLY,
            allowed_ids=[],
            ignored_ids=[],
        )

    for state in ("Idle", "Off", None):
        assert not should_expose_device(
            device_id="client-1.Emby Windows",
            state=state,
            mode=CLIENT_MODE_ACTIVE_ONLY,
            allowed_ids=[],
            ignored_ids=[],
        )


def test_legacy_numeric_options_are_migrated_to_correct_identities() -> None:
    migrated, changed = migrate_legacy_device_options(
        {
            CONF_ALLOWED_DEVICE_IDS: ["341"],
            CONF_IGNORED_DEVICE_IDS: ["341"],
        },
        [_device()],
    )

    assert changed is True
    assert migrated[CONF_ALLOWED_DEVICE_IDS] == ["client-1.Emby Windows"]
    assert migrated[CONF_IGNORED_DEVICE_IDS] == ["client-1"]


def test_already_stable_options_are_unchanged() -> None:
    options = {
        CONF_ALLOWED_DEVICE_IDS: ["client-1.Emby Windows"],
        CONF_IGNORED_DEVICE_IDS: ["client-1"],
    }
    migrated, changed = migrate_legacy_device_options(options, [_device()])

    assert changed is False
    assert migrated == options


def test_unique_player_keys_deduplicate_historical_records() -> None:
    first = _device()
    second = EmbyDeviceRecord.from_api(
        {
            "Id": "342",
            "ReportedDeviceId": "client-1",
            "Name": "Living room duplicate",
            "AppName": "Emby Windows",
        }
    )

    assert unique_player_keys([first, second]) == ["client-1.Emby Windows"]


def test_unique_reported_device_ids_deduplicate_app_variants() -> None:
    first = _device()
    second = EmbyDeviceRecord.from_api(
        {
            "Id": "342",
            "ReportedDeviceId": "client-1",
            "Name": "Living room web",
            "AppName": "Emby Web",
        }
    )

    assert unique_reported_device_ids([first, second]) == ["client-1"]


def test_active_registry_entries_are_never_cleanup_candidates() -> None:
    assert (
        registry_cleanup_reason(
            has_state=True,
            config_entry_id=None,
            target_entry_id="entry-1",
            unique_id="client-1.Emby Windows",
            ignored_ids=[],
        )
        is None
    )
    assert (
        registry_cleanup_reason(
            has_state=True,
            config_entry_id="entry-1",
            target_entry_id="entry-1",
            unique_id="client-1.Emby Windows",
            ignored_ids=["client-1"],
        )
        is None
    )


def test_inactive_registry_cleanup_reasons_are_explicit() -> None:
    assert (
        registry_cleanup_reason(
            has_state=False,
            config_entry_id=None,
            target_entry_id="entry-1",
            unique_id="client-1.Emby Windows",
            ignored_ids=[],
        )
        == "legacy_yaml"
    )
    assert (
        registry_cleanup_reason(
            has_state=False,
            config_entry_id="entry-1",
            target_entry_id="entry-1",
            unique_id="client-1.Emby Windows",
            ignored_ids=["client-1"],
        )
        == "ignored"
    )
    assert (
        registry_cleanup_reason(
            has_state=False,
            config_entry_id="entry-1",
            target_entry_id="entry-1",
            unique_id="client-2.Emby Windows",
            ignored_ids=[],
        )
        == "registry_only"
    )


def test_server_cleanup_selector_uses_unique_context_and_record_id() -> None:
    first = EmbyDeviceRecord.from_api(
        {
            "Id": "history-record-0001",
            "ReportedDeviceId": "client-1",
            "Name": "Living room",
            "AppName": "Emby Windows",
            "AppVersion": "2.315.2.0",
            "DateLastActivity": "2026-07-13T18:35:44.0000000Z",
        }
    )
    second = EmbyDeviceRecord.from_api(
        {
            "Id": "history-record-0002",
            "ReportedDeviceId": "client-1",
            "Name": "Living room",
            "AppName": "Emby Windows",
            "AppVersion": "2.315.2.0",
            "DateLastActivity": "2026-07-13T18:35:44.0000000Z",
        }
    )

    options = server_device_selector_options([first, second])

    assert set(options) == {"history-record-0001", "history-record-0002"}
    assert options["history-record-0001"] != options["history-record-0002"]
    assert "Emby Windows 2.315.2.0" in options["history-record-0001"]
    assert "2026-07-13 18:35 UTC" in options["history-record-0001"]
    assert "ID hist…0001" in options["history-record-0001"]
