# Server cleanup

Server-history cleanup and Home Assistant player lifecycle are separate operations.

Automatic cleanup uses the configured age threshold and persistent schedule. Its persisted report includes `skipped_recent` for entries that are not yet automatically due. Manual selection is independent of that age threshold and lists all unequivocally safe inactive records.

Before server deletion EMBi revalidates identity, activity, and playback. A matching Home Assistant entity is considered only after successful server deletion and exact ownership checks.

Playing, paused, ambiguous, and records without reliable activity remain protected. EMBi never deletes media, libraries, users, or playback history.
