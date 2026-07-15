# 09 – Diagnostics and Logging

## 1. Diagnostics goals

Diagnostics must expose integration version, schema version, effective options, client-class counts, user-group counts, registry counts, runtime counts, playback counts, hidden-rule counts, scheduler state, last cleanup, last player removal, last restore and migration result.

## 2. Structure

```text
integration
config_entry
options
migration
runtime
classification
registry
visibility
cleanup
last_cleanup_run
last_player_action
issues
```

## 3. Redaction

Redact API keys, auth headers, tokens, secrets and full server credentials. Hash or truncate internal client identifiers when full values are not needed.

## 4. Status language

UI uses Successful, Partially successful, Failed, Protected, Removed and Restored.

Diagnostics may use stable machine values such as completed, partial, failed, protected_playback, verification_failed and rollback_completed.

## 5. Logging levels

### INFO

- integration loaded,
- migration completed,
- successful automatic or manual cleanup,
- successful player removal,
- successful restore.

### WARNING

- partial cleanup,
- safe-state verification failure,
- unresolved legacy rule,
- unknown client classification,
- candidate skipped because state changed.

### ERROR

- setup failure,
- migration failure,
- storage corruption,
- inconsistent state after rollback attempt,
- unrecoverable API failure.

Successful zero-deletion runs are INFO, not WARNING.

## 6. Last action records

Store bounded summaries for cleanup, HA player removal and restore, including timestamps, requested count, successful count, protected count, failed count, stable reason codes and next scheduled run where applicable.

## 7. Repairs

Create a Home Assistant repair for failed storage migration, corrupted maintenance storage, repeated scheduler failure, persistent verification failure or unresolved state requiring user action. Do not create repairs for normal zero-candidate cleanup.
