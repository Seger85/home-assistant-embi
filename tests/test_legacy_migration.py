from __future__ import annotations

from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.const import (
    CONF_ALLOWED_DEVICE_IDS,
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_GLOBAL_PLAYER_MODE,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_HIDDEN_WHOLE_DEVICES,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_AGE_DAYS,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_UNRESOLVED_LEGACY_RULES,
    PLAYER_MODE_ACTIVE_ONLY,
    PLAYER_MODE_PERSISTENT,
)
from custom_components.emby.legacy_migration import LEGACY_OPTION_KEYS
from custom_components.emby.options_model import migrate_options


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


def test_upgrade_preserves_cleanup_values_and_automatic_state() -> None:
    old = {
        "client_mode": "all",
        CONF_SERVER_CLEANUP_AGE_DAYS: 364,
        CONF_SERVER_AUTO_CLEANUP_AGE_DAYS: 365,
        CONF_SERVER_AUTO_CLEANUP_ENABLED: True,
        CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES: True,
    }
    migrated, changed = migrate_options(old, [record()])
    assert changed is True
    assert migrated[CONF_SERVER_CLEANUP_AGE_DAYS] == 364
    assert migrated[CONF_SERVER_AUTO_CLEANUP_AGE_DAYS] == 365
    assert migrated[CONF_SERVER_AUTO_CLEANUP_ENABLED] is True
    assert migrated[CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES] is True
    assert migrated[CONF_TECHNICAL_ACCESS_VISIBILITY] is True
    assert "client_mode" not in migrated


def test_active_only_and_allowlist_preserve_effective_visibility() -> None:
    item = record(record_id="legacy-record")
    active, _ = migrate_options({"client_mode": "active_only"}, [item])
    allowlist, _ = migrate_options(
        {
            "client_mode": "allowlist",
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
        "ignored_player_keys": [item.player_key],
        "ignored_reported_device_ids": [item.reported_device_id],
        "unresolved_ignored_ids": ["legacy-unknown"],
        "ignored_device_ids": ["not-resolvable"],
    }
    migrated, _ = migrate_options(old, [item])
    assert migrated[CONF_HIDDEN_EXACT_PLAYERS] == [item.player_key]
    assert migrated[CONF_HIDDEN_WHOLE_DEVICES] == [item.reported_device_id]
    assert migrated[CONF_UNRESOLVED_LEGACY_RULES] == [
        "legacy-unknown",
        "not-resolvable",
    ]
    assert all(key not in migrated for key in LEGACY_OPTION_KEYS)


def test_numeric_legacy_ignore_requires_unique_match() -> None:
    unique = record(record_id="100", reported_id="unique")
    ambiguous_a = record(record_id="200", reported_id="first", app="A")
    ambiguous_b = record(record_id="200", reported_id="second", app="B")
    migrated, _ = migrate_options(
        {"ignored_device_ids": ["100", "200"]},
        [unique, ambiguous_a, ambiguous_b],
    )
    assert migrated[CONF_HIDDEN_WHOLE_DEVICES] == ["unique"]
    assert migrated[CONF_UNRESOLVED_LEGACY_RULES] == ["200"]


def test_migration_is_idempotent() -> None:
    first, _ = migrate_options(
        {
            "client_mode": "active_only",
            CONF_SERVER_AUTO_CLEANUP_ENABLED: True,
            CONF_SERVER_AUTO_CLEANUP_AGE_DAYS: 364,
        },
        [record()],
    )
    second, changed = migrate_options(first, [record()])
    assert second == first
    assert changed is False
