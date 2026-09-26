from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.emby.diagnostics import async_get_config_entry_diagnostics
from custom_components.emby.entry_lifecycle import async_remove_entry
from custom_components.emby.maintenance_common import _async_save_state
from custom_components.emby.maintenance_recovery import async_recover_maintenance
from custom_components.emby.maintenance_store import EmbiMaintenanceStore
from custom_components.emby.models import EmbiRuntimeData, MaintenanceState
from custom_components.emby.player_identity import player_key_from_unique_id, player_unique_id


@pytest.mark.asyncio
async def test_diagnostics_use_allowlist_and_user_sensor_rename_is_not_an_error(hass, entry):
    hass.config_entries._entries[entry.entry_id] = entry
    hass.config_entries.async_update_entry(
        entry,
        data={**entry.data, "unexpected": "private-extra-data"},
        options={
            "someone-private": False,
            "hidden_exact_players": ["private-device-id"],
            "private-extra-option": "sensitive",
        },
    )
    entry.runtime_data = EmbiRuntimeData(api_client=AsyncMock())
    registry = er.async_get(hass)
    sensor = registry.async_get_or_create(
        "sensor",
        "emby",
        f"{entry.entry_id}_movie_count",
        config_entry=entry,
        suggested_object_id="my_movies",
    )
    diagnostic = await async_get_config_entry_diagnostics(hass, entry)
    exported = json.dumps(diagnostic)
    for secret in (
        "test-secret",
        "127.0.0.1",
        "someone-private",
        "private-device-id",
        "private-extra-data",
        "private-extra-option",
    ):
        assert secret not in exported
    assert diagnostic["runtime"]["sensor_custom_entity_ids"] == 1
    assert "sensor_identity_mismatches" not in diagnostic["runtime"]
    assert registry.async_get(sensor.entity_id).entity_id == "sensor.my_movies"


@pytest.mark.asyncio
async def test_legacy_identity_and_metadata_survive_removal_and_new_server_is_scoped(
    hass, entry, entry_factory
):
    hass.config_entries._entries[entry.entry_id] = entry
    other = entry_factory(unique_id="second-server")
    hass.config_entries._entries[other.entry_id] = other
    registry = er.async_get(hass)
    legacy = registry.async_get_or_create(
        "media_player", "emby", "tv.App", config_entry=entry, suggested_object_id="living_room"
    )
    registry.async_update_entity(legacy.entity_id, name="Mein Fernseher")
    assert player_unique_id(registry, entry.entry_id, "tv.App") == "tv.App"
    second_uid = player_unique_id(registry, other.entry_id, "tv.App")
    assert second_uid == f"{other.entry_id}::tv.App"
    assert player_key_from_unique_id(second_uid, other.entry_id) == "tv.App"
    registry.async_remove(legacy.entity_id)
    assert player_unique_id(registry, entry.entry_id, "tv.App") == "tv.App"
    restored = registry.async_get_or_create(
        "media_player", "emby", "tv.App", config_entry=entry, suggested_object_id="other_name"
    )
    assert restored.entity_id == legacy.entity_id
    assert restored.name == "Mein Fernseher"
    second = registry.async_get_or_create(
        "media_player", "emby", second_uid, config_entry=other, suggested_object_id="living_room"
    )
    assert second.entity_id != restored.entity_id


@pytest.mark.asyncio
async def test_missing_store_requires_explicit_recovery_and_removal_is_entry_scoped(
    hass, entry, entry_factory
):
    hass.config_entries._entries[entry.entry_id] = entry
    store = EmbiMaintenanceStore.create(hass, entry.entry_id)
    runtime = EmbiRuntimeData(
        api_client=AsyncMock(),
        maintenance_store=store,
        maintenance_storage_available=False,
        maintenance_recovery_required=True,
    )
    entry.runtime_data = runtime
    assert not await _async_save_state(hass, entry)
    assert await store.async_load() is None
    assert not await async_recover_maintenance(hass, entry, reset=False)
    assert await async_recover_maintenance(hass, entry, reset=True)
    state = await store.async_load()
    assert state.initial_run_completed
    assert state.automatic_next_run_at is not None
    assert runtime.maintenance_storage_available and not runtime.maintenance_recovery_required
    other = entry_factory(unique_id="other")
    other_store = EmbiMaintenanceStore.create(hass, other.entry_id)
    await other_store.async_save(MaintenanceState())
    await async_remove_entry(hass, entry)
    assert await EmbiMaintenanceStore.create(hass, entry.entry_id).async_load() is None
    assert await other_store.async_load() is not None


@pytest.mark.asyncio
async def test_registry_followup_protects_fresh_playback_without_local_state(hass, entry):
    from custom_components.emby.maintenance_registry_apply import (
        async_apply_pending_registry_cleanup,
    )
    from custom_components.emby.maintenance_registry_queue import _PENDING_REGISTRY_CLEANUP
    from custom_components.emby.models import PendingRegistryTarget

    hass.config_entries._entries[entry.entry_id] = entry
    registry = er.async_get(hass)
    player = registry.async_get_or_create(
        "media_player", "emby", "tv.App", config_entry=entry, suggested_object_id="test_tv"
    )
    api = AsyncMock()
    api.async_get_sessions.return_value = [
        {
            "Id": "active",
            "DeviceId": "tv",
            "Client": "App",
            "NowPlayingItem": {"Id": "film"},
            "PlayState": {"IsPaused": False},
        }
    ]
    store = EmbiMaintenanceStore.create(hass, entry.entry_id)
    entry.runtime_data = EmbiRuntimeData(api_client=api, maintenance_store=store)
    hass.data[_PENDING_REGISTRY_CLEANUP] = {
        entry.entry_id: {"tv.App": PendingRegistryTarget("tv.App", player.entity_id)}
    }
    assert hass.states.get(player.entity_id) is None
    result = await async_apply_pending_registry_cleanup(hass, entry, [])
    assert result.protected_active == 1
    assert result.removed == 0
    assert registry.async_get(player.entity_id) is not None
    api.async_get_sessions.assert_awaited_once()
