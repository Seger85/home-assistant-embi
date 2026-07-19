# Architecture

EMBi is a Home Assistant config-entry integration built around four explicit boundaries:

- `EmbyApiClient` handles authenticated local Emby REST requests.
- `PlayerContext` derives player identity, visibility, lifecycle, and protection state.
- The options flow keeps a single in-memory draft and applies it once.
- The maintenance store persists scheduler and cleanup-report state through Home Assistant's supported storage API.

## Platforms

- `media_player` exposes Emby playback clients using the existing stable player unique-ID contract.
- `sensor` exposes six optional numeric statistics through one update coordinator per config entry.

The sensor coordinator requests `/Items/Counts` and `/Sessions` together. Failed or malformed API responses fail the update instead of publishing fabricated zero values.

## Entity ownership

Player and sensor registry operations require the exact config entry, domain, platform, and unique ID. Suggested sensor object IDs provide the documented entity IDs when those IDs are free. EMBi does not adopt YAML entities or implement automatic collision migration.

## Options lifecycle

Normal pages write only to the draft. Final apply stores options, closes the flow, reloads the config entry, removes disabled EMBi-owned sensor entities, reconciles safely inactive hidden players, and optionally runs newly changed automatic cleanup.
