# 08 – Security and Safety Contract

## 1. Fail closed

When ownership, playback state, server identity or reload verification is uncertain, EMBi must not delete.

## 2. Ownership checks

Before removing a Home Assistant entity, verify freshly:

- config entry equals the active EMBi entry,
- platform/domain belongs to EMBi,
- unique identity matches the selected player,
- target did not change since preview.

## 3. Playback checks

Immediately before mutation:

- refresh current state,
- block playing,
- block paused,
- treat unknown playback as protected until resolved.

Do not stop playback automatically.

## 4. Server-history deletion checks

Before deleting a server record:

- refresh Emby data,
- verify the record still exists,
- verify threshold with strict date comparison,
- protect active clients,
- protect records without a reliable activity date,
- verify selection still maps to the same record.

## 5. Home Assistant removal transaction

1. lock the selected logical identity,
2. revalidate,
3. write the hidden rule durably,
4. unload/reload through supported APIs,
5. remove the registry entity only when still owned and safe,
6. reload,
7. verify absence,
8. release lock,
9. report result.

Never edit `.storage` directly.

## 6. Partial failure

If the hidden rule is stored but entity removal fails, keep the player hidden to prevent recreation, report partial failure, offer restore or retry and record the failed phase in diagnostics.

If the hidden rule fails to store, do not remove the entity.

## 7. Restore safety

Restore removes only the intended hidden rule, preserves unrelated rules, reloads, verifies creation and preserves custom registry metadata where possible.

## 8. Destructive confirmation

Exactly one final confirmation with count, friendly names, effect, what is not deleted and restore availability where applicable.

## 9. Concurrency

Use a per-config-entry maintenance lock. Block or queue simultaneous manual cleanup, automatic cleanup during manual cleanup, player removal during cleanup and options apply during destructive work.

## 10. Secrets

Never expose API keys, auth tokens, credentials or user secrets. Technical IDs may appear only in diagnostics and should be redacted where appropriate for public reports.

## 11. Live-test safety

Before destructive acceptance tests, create a Home Assistant backup, prefer disposable records and verify rollback. Do not delete production Emby history merely to satisfy a test.
