# EMBi – Emby Integration for Home Assistant

EMBi connects a local Emby server to Home Assistant. It provides controllable media-player entities, exact lifecycle management for historical clients, and optional library and playback statistics.

## Home Assistant players

- Show players permanently or only while playing or paused.
- Automatically expose newly discovered players.
- Include or exclude technical API clients with an independent master switch.
- Manage exact player exceptions inside user, shared, unassigned, technical, and unclear groups.
- Remove safely inactive EMBi entities from the entity platform, state machine, and registry without deleting Emby server history.
- Restore a hidden player with the same stable unique ID.

Playing and paused clients are protected. Unknown playback is freshly revalidated for the specific client; it is not a permanent group-wide blocker. Names, areas, labels, aliases, and unrelated entities are never rewritten by player cleanup.

## Emby sensors

All six sensors are enabled by default and can be selected in the integration options:

- `sensor.emby_movie_count`
- `sensor.emby_tv_series_count`
- `sensor.emby_tv_episode_count`
- `sensor.emby_album_count`
- `sensor.emby_song_count`
- `sensor.emby_users_watching`

Disabling a sensor changes only the draft until final apply. After apply, only the exact EMBi-owned registry entity is removed. Re-enabling it restores the same unique ID and documented entity ID when that target is free.

> Remove conflicting YAML sensors before enabling the corresponding EMBi sensor and restart Home Assistant. EMBi never adopts, renames, or deletes unrelated YAML entities.

## Safe server-history cleanup

Automatic cleanup uses a persistent schedule and age threshold. Manual cleanup lists unequivocally safe inactive records independently of that threshold. Playing, paused, ambiguous, and temporally unverifiable records remain protected. Server deletion and Home Assistant entity removal are separate, freshly revalidated operations.

## Installation through HACS

1. Add `Seger85/home-assistant-embi` as a custom **Integration** repository.
2. Install **Emby Integration - EMBi**.
3. Restart Home Assistant.
4. Add or configure EMBi under **Settings → Devices & services**.

Stable releases provide exactly `embi.zip` and `embi.zip.sha256`.

## Configuration and safety

Normal option pages update an in-memory draft. **Review changes** appears only when a semantic change exists; **Apply changes** writes once and schedules one planned reload plus explicitly justified lifecycle or cleanup follow-up. Closing the dialog does not save.

Credentials are stored by Home Assistant and redacted from diagnostics. Registry deletion requires exact domain, platform, config-entry, and unique-ID ownership. Direct `.storage` edits are unsupported.

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
