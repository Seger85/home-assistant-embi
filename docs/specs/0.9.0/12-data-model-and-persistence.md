# 12 – Data Model and Persistence

## 1. Principles

- preserve stable entity identity,
- keep user-facing grouping separate from technical identity,
- use explicit schema versioning,
- store only what cannot be recomputed safely,
- avoid duplicated sources of truth.

## 2. Persisted model

The implementation may adapt names to existing code but must represent:

```text
schema_version
global_player_mode
auto_show_new_players
technical_access_visibility
hidden_exact_players
hidden_whole_devices
user_master_visibility
unresolved_legacy_rules
server_cleanup_enabled
server_cleanup_age_days
server_auto_cleanup_enabled
server_auto_cleanup_age_days
server_auto_cleanup_remove_ha_entities
```

## 3. Runtime-derived model

Recompute current server records, logical players, known users, latest user, client class, HA entity ID, custom name, enabled state, runtime state, removal eligibility and safe server-deletion candidates.

## 4. User history

A bounded persisted history may be used only when the Emby API does not provide enough current information. Key by stable logical identity, store a bounded user set and last-seen time, never let stale history override current explicit data and support pruning.

## 5. Classification cache

May store class, confidence, reason code and last evaluation. Unknown remains unknown until evidence exists.

## 6. Hidden rules

Exact-player hide is canonical for Remove from Home Assistant. Whole-device rules may support user/device master behavior only when existing semantics are preserved. Restore must not clear unrelated rules.

## 7. Last-action storage

Use bounded maintenance storage for last cleanup, last HA removal, last restore and last migration. Corruption fails safely and raises a repair issue.
