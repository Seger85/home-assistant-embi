# Server cleanup

EMBi keeps four lifecycles separate:

- player visibility in the options draft
- Home Assistant entity-registry ownership
- historical device records on the Emby server
- the persistent automatic-cleanup schedule and report

## Automatic cleanup

Automatic cleanup is age based. The report records the actual age threshold and separate counts for:

- candidates
- deleted records
- failed deletions
- active or otherwise protected records
- records without a reliable activity timestamp
- records not yet automatically due (`skipped_recent`)

The options page renders the not-yet-due count as:

> Not yet due for automatic cleanup (< age threshold): count

The report is stored through Home Assistant's supported storage API and exposed in privacy-safe diagnostics.

## Manual cleanup

Manual selection is independent of the automatic cleanup age threshold. It does not display the automatic `skipped_recent` count.

The workflow is:

1. Read current Emby and Home Assistant state.
2. Offer only unequivocally safe inactive records.
3. Show the selected records in a preview.
4. Require explicit confirmation.
5. Delete each server record separately.
6. Re-read remaining server history.
7. Remove a matching Home Assistant entity only after exact ownership and playback revalidation.

Playing, paused, unknown, ambiguous, and temporally unverifiable records remain protected.

## What cleanup does not delete

EMBi does not delete Emby users, media, libraries, watch history, or unrelated Home Assistant entities. It does not perform blanket entity-registry cleanup.
