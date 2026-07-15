# 10 – Test and Acceptance Matrix

## 1. Evidence rule

Every blocker in `requirements.yaml` needs implementation location, automated test, CI result, required live result, required visual result, final status and evidence link or SHA.

No blocker may be marked not applicable without an approved reason.

## 2. Required format

| ID | Implementation | Automated test | CI | Live | Visual | Status | Evidence |
|---|---|---|---|---|---|---|---|
| DEV-001 | pending | pending | pending | pending | pending | pending | pending |

The implementation PR updates this file or publishes an equivalent generated report.

## 3. Automated test groups

### Unit tests

- identity normalization,
- user aggregation,
- shared-user grouping,
- technical and unknown classification,
- display-name priority,
- search indexing,
- removal eligibility,
- playback protection,
- exact age thresholds,
- hidden-rule persistence,
- migration mapping,
- diagnostics redaction.

### Options-flow tests

- root with and without draft,
- Devices & players,
- Cleanup,
- Review changes,
- Back preserves draft,
- X discards draft,
- Apply persists,
- Discard resets,
- destructive actions hidden with draft,
- zero-candidate state,
- one confirmation only.

### Integration tests

- entity creation,
- disabled entity remains valid,
- hide and remove,
- reload verification,
- restore,
- server deletion preview and success,
- API failure,
- partial failure,
- scheduler run,
- last-run persistence.

## 4. Migration fixtures

Required fixtures or equivalents:

- `v030_default`
- `v030_all_devices`
- `v030_selected_devices`
- `v030_active_only`
- `v030_app_ignore`
- `v030_device_ignore`
- `v030_unresolved_legacy`
- `v030_cleanup_364`
- `v030_cleanup_365`
- `v030_disabled_valid_entity`
- `v030_custom_entity_names`
- `v030_technical_clients`

## 5. Live acceptance scenarios

### L-01 Baseline

Record config-entry state, HA player count, server-history count, repairs and diagnostics.

### L-02 Disabled valid entity

Disable a valid EMBi entity, reload, verify it is shown as disabled rather than orphaned, re-enable and verify the same entity ID.

### L-03 Hide non-playing player

Choose an idle test player, remove from HA, verify hidden rule, verify entity removal, reload and verify no return.

### L-04 Restore

Restore L-03 and verify entity returns with expected ID and name behavior.

### L-05 Playback protection

Verify playing blocked, paused blocked, stopped becomes removable.

### L-06 Zero-candidate server cleanup

Verify no empty selector, correct counts and no change.

### L-07 Scheduler

Disabled means no next run; controlled enable schedules one run; disable removes schedule; no duplicate schedule.

### L-08 Draft behavior

Back preserves, X discards, Apply saves, Discard resets and semantic review is correct.

## 6. Desktop visual acceptance

Minimum 1440×900. Check no clipped heading, no UUID as primary label, entity ID readable/copyable, short root menu, coherent Cleanup page, Last run once, usable search, unambiguous buttons, no empty selector and no DE/EN overflow.

## 7. Mobile final check

No horizontal overflow, buttons reachable, long IDs safe, dialogs fit and no destructive button hidden.

## 8. Release blockers

- player returns after verified removal,
- playing/paused player removable,
- migration changes entity IDs,
- disabled valid entity appears orphaned,
- automatic cleanup changes state during migration,
- translation mismatch,
- stale prerelease wording,
- release ZIP mismatch,
- failing CI,
- missing blocker evidence.
