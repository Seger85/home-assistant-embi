# Architecture

EMBi 1.0 uses canonical unversioned runtime modules:

- `options_flow.py`: one draft/apply controller
- `options_devices.py`: one player/group UI implementation
- `options_sensors.py`: one serializable sensor selector
- `player_actions.py`: exact manual and post-commit player actions
- `player_reconciliation.py`: bounded startup and visibility reconciliation
- `registry_state.py`: state-removal safety predicates
- `sensor_registry.py`: exact sensor identity migration

Migration code remains in `options_model.py`; normal runtime does not emulate old release-specific classes. Entity removal requires exact domain, platform, config-entry, and unique-ID ownership. Disallowed entities are removed from the entity platform, state machine, and registry rather than retained indefinitely as managed `unavailable` entities.
