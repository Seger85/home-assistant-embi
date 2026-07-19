# Security

## Credentials and diagnostics

The Emby API key is stored in the Home Assistant config entry. Diagnostics redact credentials, host details, and identity-bearing option values. Cleanup reports contain aggregate counters rather than device record IDs, player keys, or usernames.

## Destructive operations

Every destructive operation is constrained to an exact EMBi config entry and revalidated against current state.

Sensor registry removal requires:

- domain `sensor`
- platform `emby`
- the same config-entry ID
- the expected EMBi sensor unique ID
- the sensor being disabled in the applied options

Player and server-history removal additionally preserve playing, paused, unknown, ambiguous, and remaining-history protection.

## Storage

EMBi uses Home Assistant APIs and performs no direct changes to `.storage`. Users should not edit `.storage` manually.

## Scope

EMBi does not delete media, libraries, user accounts, or watch history. It never removes unrelated or merely similarly named Home Assistant entities.
