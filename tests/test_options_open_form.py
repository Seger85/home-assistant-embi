from __future__ import annotations

from dataclasses import replace

import pytest
from test_options_flow import setup_flow

from custom_components.emby.const import (
    CONF_FLOW_ACTION,
    CONF_HIDDEN_EXACT_PLAYERS,
    FLOW_ACTION_APPLY,
)
from custom_components.emby.player_context import GROUP_USER_PREFIX


@pytest.mark.asyncio
async def test_activity_timestamp_change_does_not_drop_submitted_switch():
    flow, entry, _, _ = setup_flow()
    flow._selected_group = f"{GROUP_USER_PREFIX}Alex"
    shown = await flow.async_step_player_group()
    keys = [marker.schema for marker in shown["data_schema"].schema]
    label = next(key for key in keys if key != CONF_FLOW_ACTION)
    old = entry.runtime_data.api_client.devices[0]
    entry.runtime_data.api_client.devices[0] = replace(
        old, last_activity_date="2026-09-26T17:45:00Z"
    )
    await flow.async_step_player_group({label: False, CONF_FLOW_ACTION: FLOW_ACTION_APPLY})
    assert flow._draft_options["user_master_visibility"]["Alex"] is False
    assert entry.options["user_master_visibility"] == {}
    assert flow._draft_options[CONF_HIDDEN_EXACT_PLAYERS] == []
