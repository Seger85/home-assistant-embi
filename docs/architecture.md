# Architecture

EMBi uses canonical unversioned runtime modules:

- `options_flow.py`: one draft/apply controller
- `options_devices.py`: one player/group UI implementation
- `options_sensors.py`: one serializable sensor selector
- `player_context.py`: the canonical `PlayerContext` classification and playback-safety model
- `player_actions.py`: exact manual and post-commit player actions
- `player_reconciliation.py`: idempotent setup/reload visibility enforcement
- `registry_state.py`: state-removal safety predicates
- `sensor.py`: the Home Assistant sensor platform backed by one update coordinator
- `sensor_registry.py`: exact sensor identity migration
- `legacy_migration.py`: isolated compatibility for published older option schemas

The sensor update coordinator refreshes all six values as one consistent snapshot and marks API-dependent values unavailable after a failed refresh instead of publishing false zero values. Version discovery remains isolated in `scripts/read_version.py` and does not import runtime modules.

The reconciliation version limits one-time migration bookkeeping only. Saved visibility is enforced after every platform setup and reload, including when the media-player platform has not yet rebuilt local entity maps. Entity removal requires exact domain, platform, config-entry, and unique-ID ownership. Disallowed entities are removed from the entity platform, state machine, and registry without changing Emby server history. Playing and paused clients remain protected, and current no-op reconciliation results refresh diagnostics without scheduling another reload.
