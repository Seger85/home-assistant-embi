from __future__ import annotations

import pytest

from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.const import (
    AGE_PRESET_7,
    AGE_PRESET_30,
    AGE_PRESET_90,
    AGE_PRESET_180,
    AGE_PRESET_365,
    AGE_PRESET_CUSTOM,
    CLIENT_MODE_ACTIVE_ONLY,
    CLIENT_MODE_ALL,
    CLIENT_MODE_ALLOWLIST,
    CONF_ALLOWED_DEVICE_IDS,
    CONF_IGNORED_PLAYER_KEYS,
    CONF_IGNORED_REPORTED_DEVICE_IDS,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_AGE_DAYS,
    CONF_SERVER_CLEANUP_ENABLED,
    CONF_UNRESOLVED_IGNORED_IDS,
)
from custom_components.emby.helpers import (
    age_days_from_input,
    age_preset_for_days,
    device_is_ignored,
    migrate_stable_options,
    registry_cleanup_reason,
    should_expose_device,
    unique_player_keys,
    unique_reported_device_ids,
)


def device(
    record_id: str = "341",
    *,
    reported_id: str = "client.1",
    app: str = "Emby Windows",
) -> EmbyDeviceRecord:
    return EmbyDeviceRecord.from_api(
        {
            "Id": record_id,
            "ReportedDeviceId": reported_id,
            "Name": "Living room",
            "AppName": app,
        }
    )


@pytest.mark.parametrize(
    ("preset", "days"),
    [
        (AGE_PRESET_7, 7),
        (AGE_PRESET_30, 30),
        (AGE_PRESET_90, 90),
        (AGE_PRESET_180, 180),
        (AGE_PRESET_365, 365),
    ],
)
def test_age_presets_are_numeric_source_of_truth(preset: str, days: int) -> None:
    assert age_days_from_input(preset, 364) == days
    assert age_preset_for_days(days) == preset


def test_custom_age_values_are_preserved_without_364_to_365_migration() -> None:
    assert age_days_from_input(AGE_PRESET_CUSTOM, 364) == 364
    assert age_days_from_input(AGE_PRESET_CUSTOM, 417) == 417
    assert age_preset_for_days(364) == AGE_PRESET_CUSTOM
    with pytest.raises(ValueError):
        age_days_from_input(AGE_PRESET_CUSTOM, None)


def test_app_and_device_ignore_rules_are_exact_even_with_dots() -> None:
    player = "client.1.Emby Windows"
    assert device_is_ignored(
        player_key=player,
        reported_device_id="client.1",
        ignored_player_keys=[player],
        ignored_reported_device_ids=[],
    )
    assert device_is_ignored(
        player_key="client.1.Emby Web",
        reported_device_id="client.1",
        ignored_player_keys=[],
        ignored_reported_device_ids=["client.1"],
    )
    assert not device_is_ignored(
        player_key="client.10.Emby Windows",
        reported_device_id="client.10",
        ignored_player_keys=["client.1"],
        ignored_reported_device_ids=["client"],
    )


def test_exposure_modes_keep_app_and_device_scope_separate() -> None:
    kwargs = {
        "device_id": "client.1.Emby Windows",
        "reported_device_id": "client.1",
        "ignored_player_keys": [],
        "ignored_reported_device_ids": [],
    }
    assert should_expose_device(**kwargs, state="Idle", mode=CLIENT_MODE_ALL, allowed_ids=[])
    assert should_expose_device(
        **kwargs, state="playing", mode=CLIENT_MODE_ACTIVE_ONLY, allowed_ids=[]
    )
    assert not should_expose_device(
        **kwargs, state="idle", mode=CLIENT_MODE_ACTIVE_ONLY, allowed_ids=[]
    )
    assert should_expose_device(
        **kwargs,
        state="idle",
        mode=CLIENT_MODE_ALLOWLIST,
        allowed_ids=["client.1.Emby Windows"],
    )
    assert not should_expose_device(
        **kwargs,
        state="idle",
        mode=CLIENT_MODE_ALLOWLIST,
        allowed_ids=["client.1.Emby Web"],
    )


def test_rc3_migration_preserves_live_options_and_removes_obsolete_fields() -> None:
    record = device(record_id="341")
    options = {
        CONF_ALLOWED_DEVICE_IDS: ["341"],
        "ignored_device_ids": [record.player_key, record.reported_device_id, "unresolved"],
        CONF_SERVER_CLEANUP_ENABLED: True,
        CONF_SERVER_CLEANUP_AGE_DAYS: 364,
        CONF_SERVER_AUTO_CLEANUP_ENABLED: True,
        CONF_SERVER_AUTO_CLEANUP_AGE_DAYS: 364,
        CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES: True,
        "server_auto_cleanup_initial_run_completed": True,
        "server_cleanup_api_key": "obsolete-secret",
        "auto_cleanup_confirmation_text": "obsolete",
        "add_deleted_to_ignored": True,
    }
    migrated, changed = migrate_stable_options(options, [record])
    assert changed is True
    assert migrated[CONF_ALLOWED_DEVICE_IDS] == [record.player_key]
    assert migrated[CONF_IGNORED_PLAYER_KEYS] == [record.player_key]
    assert migrated[CONF_IGNORED_REPORTED_DEVICE_IDS] == [record.reported_device_id]
    assert migrated[CONF_UNRESOLVED_IGNORED_IDS] == ["unresolved"]
    assert migrated[CONF_SERVER_CLEANUP_AGE_DAYS] == 364
    assert migrated[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS] == 364
    assert migrated[CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES] is True
    for obsolete in (
        "ignored_device_ids",
        "server_cleanup_api_key",
        "auto_cleanup_confirmation_text",
        "add_deleted_to_ignored",
        "server_auto_cleanup_initial_run_completed",
    ):
        assert obsolete not in migrated
    assert "obsolete-secret" not in repr(migrated)


def test_numeric_legacy_ignore_requires_unique_match() -> None:
    unique = device(record_id="100", reported_id="unique")
    ambiguous_a = device(record_id="200", reported_id="first", app="A")
    ambiguous_b = device(record_id="200", reported_id="second", app="B")
    migrated, _ = migrate_stable_options(
        {"ignored_device_ids": ["100", "200"]},
        [unique, ambiguous_a, ambiguous_b],
    )
    assert migrated[CONF_IGNORED_REPORTED_DEVICE_IDS] == ["unique"]
    assert migrated[CONF_UNRESOLVED_IGNORED_IDS] == ["200"]


def test_unresolved_values_survive_idempotent_migration() -> None:
    options = {
        CONF_IGNORED_PLAYER_KEYS: ["exact.App"],
        CONF_IGNORED_REPORTED_DEVICE_IDS: ["exact-device"],
        CONF_UNRESOLVED_IGNORED_IDS: ["legacy-unknown"],
    }
    first, changed = migrate_stable_options(options, [])
    second, changed_again = migrate_stable_options(first, [])
    assert first == second == options
    assert changed is False
    assert changed_again is False


def test_unique_bulk_identities_use_correct_scope() -> None:
    records = [
        device("1", reported_id="same", app="App A"),
        device("2", reported_id="same", app="App A"),
        device("3", reported_id="same", app="App B"),
    ]
    assert unique_player_keys(records) == ["same.App A", "same.App B"]
    assert unique_reported_device_ids(records) == ["same"]


def test_registry_cleanup_reason_never_uses_substrings() -> None:
    assert (
        registry_cleanup_reason(
            has_state=False,
            config_entry_id="entry",
            target_entry_id="entry",
            unique_id="client.10.App",
            reported_device_id="client.10",
            ignored_player_keys=["client.1"],
            ignored_reported_device_ids=["client"],
        )
        == "registry_only"
    )
