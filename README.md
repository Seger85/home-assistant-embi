# EMBi – Emby Integration for Home Assistant

EMBi connects a local Emby server to Home Assistant. It provides controllable media-player entities, safe management of historical Emby device records, and optional library and playback statistics.

## Features

### Home Assistant players

- Show players permanently or only while playing or paused.
- Automatically expose newly discovered players.
- Include or exclude technical API clients.
- Manage players by user and device group.
- Remove safely inactive Home Assistant player entities without deleting their Emby server record.
- Restore previously removed players while preserving stable identities.

Playing, paused, and ambiguous players are protected from destructive actions. Existing player entity IDs, unique IDs, names, areas, labels, and aliases are not migrated or rewritten.

### Emby sensors

All six sensors are enabled by default and can be switched individually in the integration options:

- `sensor.emby_movie_count`
- `sensor.emby_tv_series_count`
- `sensor.emby_tv_episode_count`
- `sensor.emby_album_count`
- `sensor.emby_song_count`
- `sensor.emby_users_watching`

Library counters use Emby's `/Items/Counts` endpoint. The users-watching sensor uses `/Sessions` and counts unique users with active playback; paused sessions are not counted.

Disabling a sensor and applying the options removes that EMBi-owned entity from the Home Assistant entity registry. Re-enabling it creates the sensor again with the same EMBi unique ID and the documented entity ID when that entity ID is free.

> Existing YAML sensors using these entity IDs must be removed before enabling the EMBi sensors. Restart Home Assistant after removing the YAML definitions. EMBi never adopts, migrates, or deletes unrelated YAML sensors.

### Safe server-history cleanup

EMBi can remove obsolete device-history records from the Emby server.

- Automatic cleanup uses a configurable age threshold and persistent schedule.
- Manual cleanup lists safe inactive records independently of the automatic age threshold.
- Active, paused, ambiguous, and temporally unverifiable records remain protected.
- A matching Home Assistant player is removed only after successful server deletion and fresh ownership, platform, unique-ID, remaining-history, and playback validation.

The automatic report distinguishes records that are not yet due from protected or failed records.

## Installation through HACS

1. Open HACS.
2. Add `Seger85/home-assistant-embi` as a custom **Integration** repository.
3. Install **Emby Integration - EMBi**.
4. Restart Home Assistant.
5. Add or configure EMBi under **Settings → Devices & services**.

EMBi is distributed through stable GitHub releases. HACS installs `embi.zip`; `embi.zip.sha256` contains the published checksum.

## Configuration

The connection and all runtime options are managed through the Home Assistant UI. Normal option pages update an in-memory draft; permanent changes are written only through **Review changes → Apply changes**.

Direct edits to `.storage` are neither required nor supported.

## Security model

- Credentials are stored by Home Assistant and redacted from diagnostics.
- Registry deletion requires exact config-entry, domain, platform, and unique-ID ownership.
- Server-history deletion is explicit and revalidated immediately before execution.
- EMBi does not delete media, libraries, users, or playback history.
- No blanket registry cleanup is performed.

## Documentation

- [Configuration](docs/configuration.md)
- [Server cleanup](docs/server-cleanup.md)
- [Architecture](docs/architecture.md)
- [Security](docs/security.md)
- [Troubleshooting](docs/troubleshooting.md)
- [UI quality assurance](docs/ui-qa.md)

## Credits

- Project: Seger
- Based on the Home Assistant Emby integration and pyemby

License: Apache-2.0
