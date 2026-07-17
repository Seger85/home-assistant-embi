from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_ALLOWED_DEVICE_IDS,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_HIDDEN_WHOLE_DEVICES,
    CONF_UNRESOLVED_LEGACY_RULES,
    CONF_USER_MASTER_VISIBILITY,
    NAME,
    VERSION,
)
from .models import EmbiRuntimeData
from .player_context import build_player_catalog, catalog_stats

_OPTION_IDENTITIES = {
    CONF_ALLOWED_DEVICE_IDS,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_HIDDEN_WHOLE_DEVICES,
    CONF_UNRESOLVED_LEGACY_RULES,
    CONF_USER_MASTER_VISIBILITY,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return useful aggregate diagnostics without private client identities."""
    runtime: EmbiRuntimeData = entry.runtime_data
    registry = er.async_get(hass)
    players = build_player_catalog(
        runtime.devices,
        registry_entries=registry.entities.values(),
        states=hass.states,
        entry_id=entry.entry_id,
        options=entry.options,
        pyemby_devices=getattr(runtime.pyemby, "devices", None),
    )
    stats = catalog_stats(players, server_history_records=len(runtime.devices))
    class_counts: dict[str, int] = {}
    group_counts: dict[str, int] = {}
    visibility_counts: dict[str, int] = {}
    for player in players:
        class_counts[player.client_class] = class_counts.get(player.client_class, 0) + 1
        group = "single_user" if player.group_key.startswith("user::") else player.group_key
        group_counts[group] = group_counts.get(group, 0) + 1
        visibility = "visible" if player.visible_in_embi else "hidden"
        visibility_counts[visibility] = visibility_counts.get(visibility, 0) + 1

    issues = sorted(
        {
            player.protected_reason
            for player in players
            if player.protected_reason and player.protected_reason not in {"playing", "paused"}
        }
    )
    return {
        "integration": {"name": NAME, "version": VERSION},
        "config_entry": {
            "title": "<redacted>",
            "version": entry.version,
            "minor_version": entry.minor_version,
            "data": async_redact_data(dict(entry.data), {CONF_API_KEY, CONF_HOST}),
            "options": async_redact_data(dict(entry.options), _OPTION_IDENTITIES),
        },
        "migration": runtime.maintenance_state.migration.as_dict(),
        "runtime": {
            "server_history_records": stats.server_history_records,
            "home_assistant_players": stats.ha_players,
            "playing_or_paused": stats.protected_playback,
            "removable_from_home_assistant": stats.removable_from_ha,
            "known_users": stats.known_users,
            "disabled_valid_entities": stats.disabled_valid,
            "server_missing_entities": stats.server_missing,
            "home_assistant_orphans": stats.orphans,
            "pyemby_initialized": runtime.pyemby is not None,
            "maintenance_storage_available": runtime.maintenance_storage_available,
            "automatic_cleanup_scheduled": runtime.auto_cleanup_scheduled,
        },
        "classification": class_counts,
        "user_groups": group_counts,
        "visibility": visibility_counts,
        "cleanup": {
            "last_run": runtime.maintenance_state.report.as_dict(),
            "last_player_action": runtime.maintenance_state.last_player_action.as_dict(),
            "last_restore": runtime.maintenance_state.last_restore.as_dict(),
        },
        "issues": issues,
    }
