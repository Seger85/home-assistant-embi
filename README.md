# EMBi – Emby Integration for Home Assistant

EMBi is a Home Assistant custom integration for local Emby servers. It provides media-player lifecycle management, safe cleanup of historical clients, and optional library and playback sensors.

## Features

### Media players

- Keep players permanently available or expose them only while playing or paused.
- Automatically include newly discovered clients.
- Manage technical API clients through an independent master switch and exact exceptions.
- Group clients by user, shared, unassigned, technical, or unclear ownership.
- Enforce saved visibility after setup, config-entry reload, and Home Assistant restart.
- Remove only safely inactive EMBi-owned entities from the entity platform, state machine, and entity registry.
- Restore hidden players with their existing stable unique IDs.

Playing and paused clients are protected. Unknown playback is revalidated for the exact client before removal. EMBi does not rewrite custom names, areas, labels, aliases, or unrelated entities, and player visibility never deletes Emby server history.

### Sensors

All six sensors are enabled by default and can be selected in the integration options:

- `sensor.emby_movie_count`
- `sensor.emby_tv_series_count`
- `sensor.emby_tv_episode_count`
- `sensor.emby_album_count`
- `sensor.emby_song_count`
- `sensor.emby_users_watching`

`sensor.emby_users_watching` counts each actively playing user once. Paused sessions are not counted.

Disabling a sensor remains part of the Options Flow draft until final apply. After apply, only the exact EMBi-owned registry entity is removed. Re-enabling restores the same unique ID and the documented entity ID when that target is free.

> Remove conflicting YAML sensors before enabling the corresponding EMBi sensor and restart Home Assistant. EMBi never adopts, renames, or deletes unrelated YAML entities.

### Server-history cleanup

Automatic cleanup uses a persistent schedule and an age threshold. Manual cleanup lists unequivocally safe inactive records independently of that threshold. Playing, paused, ambiguous, and temporally unverifiable records remain protected. Server-history deletion and Home Assistant entity removal are separate, freshly revalidated operations.

## Installation through HACS

1. Add `Seger85/home-assistant-embi` as a custom **Integration** repository.
2. Install **Emby Integration - EMBi**.
3. Restart Home Assistant.
4. Add or configure EMBi under **Settings → Devices & services**.

Stable releases contain exactly `embi.zip` and `embi.zip.sha256`.

## Configuration and safety

Normal option pages update an in-memory draft. **Review changes** appears only when a semantic change exists. **Apply changes** writes once and schedules one planned reload plus explicitly justified lifecycle or cleanup follow-up. Closing the dialog does not save.

Credentials are stored by Home Assistant and redacted from diagnostics. Registry deletion requires exact domain, platform, config-entry, and unique-ID ownership. Direct `.storage` edits are unsupported.

Published upgrade paths are handled only by the isolated migration module and the tests under `tests/migration/`. Current runtime modules, normal tests, workflows, and user documentation remain version-neutral.

## Documentation

- [Configuration](docs/configuration.md)
- [Server cleanup](docs/server-cleanup.md)
- [Architecture](docs/architecture.md)
- [Security](docs/security.md)
- [Troubleshooting](docs/troubleshooting.md)
- [UI quality assurance](docs/ui-qa.md)
- [Contributing](CONTRIBUTING.md)
- [Stable release process](RELEASING.md)

## Credits and license

- Project: Seger
- Based on the Home Assistant Emby integration and pyemby
- License: Apache-2.0
