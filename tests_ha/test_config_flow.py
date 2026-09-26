from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from homeassistant import loader
from homeassistant.config_entries import ConfigEntryState

from custom_components.emby.entry_lifecycle import async_update_listener
from custom_components.emby.models import EmbiRuntimeData


def prepare(hass):
    (Path(hass.config.config_dir) / "custom_components").symlink_to(
        Path(__file__).parents[1] / "custom_components", target_is_directory=True
    )
    loader.async_setup(hass)


@pytest.mark.asyncio
async def test_reauth_uses_one_reload_and_preserves_options(hass, entry, monkeypatch):
    prepare(hass)
    hass.config_entries._entries[entry.entry_id] = entry
    entry.runtime_data = EmbiRuntimeData(api_client=AsyncMock())
    entry.add_update_listener(async_update_listener)
    validate = AsyncMock(return_value={"Id": "test-server"})
    monkeypatch.setattr("custom_components.emby.config_flow._validate", validate)
    reload = AsyncMock(return_value=True)
    monkeypatch.setattr(hass.config_entries, "async_reload", reload)
    result = await hass.config_entries.flow.async_init(
        "emby", context={"source": "reauth", "entry_id": entry.entry_id}, data=dict(entry.data)
    )
    assert result["step_id"] == "reauth_confirm"
    rejected = await hass.config_entries.flow.async_configure(result["flow_id"], {"api_key": ""})
    assert rejected["errors"]["base"] == "invalid_auth"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"api_key": "new-key"}
    )
    assert result["type"] == "abort" and result["reason"] == "reauth_successful"
    await hass.async_block_till_done()
    assert entry.data["api_key"] == "new-key"
    assert dict(entry.options) == {}
    reload.assert_awaited_once_with(entry.entry_id)


@pytest.mark.asyncio
async def test_reconfigure_rejects_other_server_and_keeps_credentials(hass, entry, monkeypatch):
    prepare(hass)
    hass.config_entries._entries[entry.entry_id] = entry
    monkeypatch.setattr(
        "custom_components.emby.config_flow._validate",
        AsyncMock(return_value={"Id": "other-server"}),
    )
    result = await hass.config_entries.flow.async_init(
        "emby", context={"source": "reconfigure", "entry_id": entry.entry_id}
    )
    assert result["step_id"] == "reconfigure"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**entry.data, "api_key": "", "name": "EMBi"}
    )
    assert result["type"] == "abort" and result["reason"] == "unique_id_mismatch"
    assert entry.data["api_key"] == "test-secret"


@pytest.mark.asyncio
async def test_future_entry_major_is_rejected_by_home_assistant_before_migration(
    hass, entry, monkeypatch
):
    prepare(hass)
    hass.config_entries._entries[entry.entry_id] = entry
    hass.config_entries.async_update_entry(entry, version=99)
    migrate = AsyncMock(return_value=True)
    monkeypatch.setattr("custom_components.emby.async_migrate_entry", migrate)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.MIGRATION_ERROR
    migrate.assert_not_awaited()


@pytest.mark.asyncio
async def test_options_draft_review_apply_uses_one_native_listener_reload(hass, entry, monkeypatch):
    from custom_components.emby.options_model import default_options

    prepare(hass)
    hass.config_entries._entries[entry.entry_id] = entry
    initial = default_options()
    hass.config_entries.async_update_entry(entry, options=initial)
    api = AsyncMock()
    api.async_get_devices.return_value = []
    api.async_get_sessions.return_value = []
    entry.runtime_data = EmbiRuntimeData(api_client=api)
    entry.add_update_listener(async_update_listener)
    reload = AsyncMock(return_value=True)
    monkeypatch.setattr(hass.config_entries, "async_reload", reload)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "menu"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "sensors"}
    )
    assert result["step_id"] == "sensors"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"enabled_sensors": ["movie_count"]}
    )
    assert dict(entry.options) == initial
    reload.assert_not_awaited()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "review_changes"}
    )
    assert result["step_id"] == "review_changes"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"flow_action": "apply_changes"}
    )
    assert result["type"] == "abort" and result["reason"] == "apply_complete"
    await hass.async_block_till_done()
    assert entry.options["enabled_sensors"] == ["movie_count"]
    reload.assert_awaited_once_with(entry.entry_id)
