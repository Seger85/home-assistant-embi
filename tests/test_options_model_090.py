from __future__ import annotations

from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.const import (
    CLIENT_MODE_ACTIVE_ONLY,
    CLIENT_MODE_ALLOWLIST,
    CONF_ALLOWED_DEVICE_IDS,
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_CLIENT_MODE,
    CONF_GLOBAL_PLAYER_MODE,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_HIDDEN_WHOLE_DEVICES,
    CONF_IGNORED_PLAYER_KEYS,
    CONF_IGNORED_REPORTED_DEVICE_IDS,
    CONF_OPTIONS_SCHEMA_VERSION,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_AGE_DAYS,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_UNRESOLVED_IGNORED_IDS,
    CONF_UNRESOLVED_LEGACY_RULES,
    OPTIONS_SCHEMA_VERSION,
    PLAYER_MODE_ACTIVE_ONLY,
    PLAYER_MODE_PERSISTENT,
)
from custom_components.emby.options_model import (
    default_options_090,
    migrate_options_090,
    should_expose_player,
)


def record(
    *,
    record_id: str = "record-1",
    reported_id: str = "device-1",
    app: str = "Emby App",
) -> EmbyDeviceRecord:
    return EmbyDeviceRecord.from_api(
        {
            "Id": record_id,
            "ReportedDeviceId": reported_id,
            "Name": "Living room",
            "AppName": app,
        }
    )


def test_new_install_defaults_match_the_frozen_contract() -> None:
    options = default_options_090()

    assert options[CONF_OPTIONS_SCHEMA_VERSION] == OPTIONS_SCHEMA_VERSION
    assert options[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_PERSISTENT
    assert options[CONF_AUTO_SHOW_NEW_PLAYERS] is True
    assert options[CONF_TECHNICAL_ACCESS_VISIBILITY] is False
    assert options[CONF_SERVER_AUTO_CLEANUP_ENABLED] is False
    assert options[CONF_SERVER_CLEANUP_AGE_DAYS] == 365
    assert options[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS] == 365


def test_upgrade_preserves_exact_cleanup_values_and_automatic_state() -> None:
    old = {
        CONF_CLIENT_MODE: "all",
        CONF_SERVER_CLEANUP_AGE_DAYS: 364,
        CONF_SERVER_AUTO_CLEANUP_AGE_DAYS: 365,
        CONF_SERVER_AUTO_CLEANUP_ENABLED: True,
        CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES: True,
    }

    migrated, changed = migrate_options_090(old, [record()])

    assert changed is True
    assert migrated[CONF_SERVER_CLEANUP_AGE_DAYS] == 364
    assert migrated[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS] == 365
    assert migrated[CONF_SERVER_AUTO_CLEANUP_ENABLED] is True
    assert migrated[CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES] is True
    assert migrated[CONF_TECHNICAL_ACCESS_VISIBILITY] is True
    assert CONF_CLIENT_MODE not in migrated


def test_active_only_and_allowlist_keep_effective_visibility() -> None:
    item = record(record_id="legacy-record")
    active, _ = migrate_options_090(
        {CONF_CLIENT_MODE: CLIENT_MODE_ACTIVE_ONLY}, [item]
    )
    allowlist, _ = migrate_options_090(
        {
            CONF_CLIENT_MODE: CLIENT_MODE_ALLOWLIST,
            CONF_ALLOWED_DEVICE_IDS: ["legacy-record"],
        },
        [item],
    )

    assert active[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_ACTIVE_ONLY
    assert allowlist[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_PERSISTENT
    assert allowlist[CONF_AUTO_SHOW_NEW_PLAYERS] is False
    assert allowlist[CONF_ALLOWED_DEVICE_IDS] == [item.player_key]


def test_exact_ignore_rules_and_unresolved_values_are_preserved() -> None:
    item = record()
    old = {
        CONF_IGNORED_PLAYER_KEYS: [item.player_key],
        CONF_IGNORED_REPORTED_DEVICE_IDS: [item.reported_device_id],
        CONF_UNRESOLVED_IGNORED_IDS: ["legacy-unknown"],
        "ignored_device_ids": ["not-resolvable"],
    }

    migrated, _ = migrate_options_090(old, [item])

    assert migrated[CONF_HIDDEN_EXACT_PLAYERS] == [item.player_key]
    assert migrated[CONF_HIDDEN_WHOLE_DEVICES] == [item.reported_device_id]
    assert migrated[CONF_UNRESOLVED_LEGACY_RULES] == [
        "legacy-unknown",
        "not-resolvable",
    ]
    assert CONF_IGNORED_PLAYER_KEYS not in migrated
    assert CONF_IGNORED_REPORTED_DEVICE_IDS not in migrated
    assert CONF_UNRESOLVED_IGNORED_IDS not in migrated


def test_migration_is_idempotent() -> None:
    first, _ = migrate_options_090(
        {
            CONF_CLIENT_MODE: CLIENT_MODE_ACTIVE_ONLY,
            CONF_SERVER_AUTO_CLEANUP_ENABLED: True,
            CONF_SERVER_AUTO_CLEANUP_AGE_DAYS: 364,
        },
        [record()],
    )
    second, changed = migrate_options_090(first, [record()])

    assert second == first
    assert changed is False


def test_canonical_visibility_uses_exact_rules_and_playback_mode() -> None:
    options = default_options_090()
    key = "device-1.Emby App"

    assert should_expose_player(
        player_key=key,
        reported_device_id="device-1",
        state="idle",
        options=options,
        technical_access=False,
    )

    options[CONF_HIDDEN_EXACT_PLAYERS] = [key]
    assert not should_expose_player(
        player_key=key,
        reported_device_id="device-1",
        state="playing",
        options=options,
        technical_access=False,
    )

    options[CONF_HIDDEN_EXACT_PLAYERS] = []
    options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    assert not should_expose_player(
        player_key=key,
        reported_device_id="device-1",
        state="idle",
        options=options,
        technical_access=False,
    )
    assert should_expose_player(
        player_key=key,
        reported_device_id="device-1",
        state="paused",
        options=options,
        technical_access=False,
    )
