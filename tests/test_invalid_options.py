from __future__ import annotations

import pytest
from test_options_flow import setup_flow

from custom_components.emby.const import CONF_SERVER_AUTO_CLEANUP_ENABLED
from custom_components.emby.legacy_migration import migrate_options
from custom_components.emby.options_model import default_options


@pytest.mark.parametrize(
    "key,value",
    [
        ("server_auto_cleanup_enabled", "false"),
        ("server_auto_cleanup_age_days", None),
        ("server_auto_cleanup_age_days", -1),
        ("server_auto_cleanup_age_days", 1.5),
        ("server_auto_cleanup_age_days", "invalid"),
        ("global_player_mode", []),
        ("hidden_exact_players", [{"bad": "shape"}]),
        ("user_master_visibility", {"Alex": "false"}),
    ],
)
def test_invalid_settings_never_enable_automatic_cleanup_and_repair_is_idempotent(key, value):
    source = {**default_options(), CONF_SERVER_AUTO_CLEANUP_ENABLED: True, key: value}
    normalized, changed = migrate_options(source, [])
    assert changed
    assert normalized[CONF_SERVER_AUTO_CLEANUP_ENABLED] is False
    repeated, changed_again = migrate_options(normalized, [])
    assert not changed_again
    assert repeated == normalized


@pytest.mark.asyncio
async def test_options_apply_cannot_recreate_a_lost_journal_and_reenable_cleanup():
    flow, entry, store, _ = setup_flow()
    entry.runtime_data.maintenance_recovery_required = True
    entry.runtime_data.maintenance_storage_available = False
    flow._draft_options[CONF_SERVER_AUTO_CLEANUP_ENABLED] = True
    result = await flow.async_step_apply_changes()
    assert result["step_id"] == "review_changes"
    assert flow._review_error == "storage_failed"
    assert not store.saved
    assert not entry.options[CONF_SERVER_AUTO_CLEANUP_ENABLED]
