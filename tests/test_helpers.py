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
    server_device_selector_options,
    should_expose_device,
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


def test_server_cleanup_selector_uses_record_id() -> None:
    assert server_device_selector_options([_device()]) == {"341": "Living room · Emby Windows"}
