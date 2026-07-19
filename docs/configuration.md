# Configuration

## Connection

Each Emby server is configured as a Home Assistant config entry with a display name, host, port, HTTPS setting, and API key. Credentials are redacted from diagnostics.

## Options flow

The root menu provides:

1. **Home Assistant players**
2. **Emby sensors**
3. **Automatic server cleanup**
4. **Delete individual Emby server records**
5. **Review changes** when the draft differs from the saved options

Non-destructive pages update only the in-memory draft. Permanent storage occurs exclusively through **Review changes → Apply changes**. Closing the flow without applying does not change the config entry.

## Home Assistant players

Global controls define playback-only visibility, automatic discovery, and technical-client visibility. Player groups contain direct per-player switches. Known access timestamps are sorted oldest first and unknown timestamps remain at the end.

Player removal requires exact EMBi ownership and a safely inactive playback state. Playing, paused, and unknown states remain protected.

## Emby sensors

The six sensor switches are enabled by default. Applying a disabled sensor removes only the matching sensor entity that belongs to the same EMBi config entry, platform, and unique ID.

The documented entity IDs are:

- `sensor.emby_movie_count`
- `sensor.emby_tv_series_count`
- `sensor.emby_tv_episode_count`
- `sensor.emby_album_count`
- `sensor.emby_song_count`
- `sensor.emby_users_watching`

Remove existing YAML sensors with these entity IDs and restart Home Assistant before enabling the EMBi sensors. EMBi does not migrate or adopt YAML entities and does not implement automatic collision handling.

## Automatic server cleanup

Automatic cleanup retains its enabled state, exact age threshold, scheduler state, next-run timestamp, and safe registry follow-up option. The last-run report includes deleted, protected, failed, and not-yet-due records.

## Manual server cleanup

Manual selection is independent of the automatic age threshold. It lists only unequivocally safe inactive records, oldest first, and retains explicit preview and confirmation.

## Backups and rollback

Create a full Home Assistant backup before changing integration versions. Roll back through HACS or restore the backup; do not edit `.storage` directly.
