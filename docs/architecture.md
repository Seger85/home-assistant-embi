# Architecture

EMBi 1.0 uses canonical unversioned runtime modules:

- `options_flow.py`: one draft/apply controller
- `options_devices.py`: one player/group UI implementation
- `options_sensors.py`: one serializable sensor selector
- `player_context.py`: the canonical `PlayerContext` classification and playback-safety model
- `player_actions.py`: exact manual and post-commit player actions
- `player_reconciliation.py`: bounded startup and visibility reconciliation
- `registry_state.py`: state-removal safety predicates
- `sensor.py`: the Home Assistant sensor platform backed by one update coordinator
- `sensor_registry.py`: exact sensor identity migration

The sensor update coordinator refreshes all six values as one consistent snapshot and marks API-dependent values unavailable after a failed refresh instead of publishing false zero values. Version discovery remains isolated in `scripts/read_version.py` and does not import runtime modules.

Migration code remains in `options_model.py`; normal runtime does not emulate old release-specific classes. Entity removal requires exact domain, platform, config-entry, and unique-ID ownership. Disallowed entities are removed from the entity platform, state machine, and registry rather than retained indefinitely as managed `unavailable` entities.
