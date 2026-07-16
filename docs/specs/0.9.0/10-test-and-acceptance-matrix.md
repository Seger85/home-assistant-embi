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

<!-- EMBI-0.9-EVIDENCE-START -->
## Implementierungs- und automatisierte Nachweise

Diese Tabelle ergänzt die unveränderten Akzeptanzszenarien. `Automatisiert` bedeutet, dass der Nachweis im Repository vorhanden ist und in Quality/Spec Contract ausgeführt wird. Reale Home-Assistant- und visuelle Nachweise bleiben bis zur privaten Abnahme ausdrücklich offen.

| Blocker-ID | Implementierung | Automatisierter Nachweis | Verbleibender Live-Nachweis |
|---|---|---|---|
| `CLN-001` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-002` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-003` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-004` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-005` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-006` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-007` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-008` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-009` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-010` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-011` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-012` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-013` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-014` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-015` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-016` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-017` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `CLN-018` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-001` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-002` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-003` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-004` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-005` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-006` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-007` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-008` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-009` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-010` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-011` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-012` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-013` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-014` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DEV-015` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DOC-001` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `DOC-002` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `LOG-001` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `LOG-002` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `LOG-003` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `MIG-001` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `MIG-002` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `MIG-003` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `MIG-004` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `MIG-005` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `MIG-006` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `MIG-007` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `MIG-008` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `NAV-001` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `NAV-002` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `NAV-003` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `NAV-004` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `NAV-005` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `NAV-006` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `NAV-007` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `REL-001` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `REL-002` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `REL-003` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `REL-004` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `REL-005` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `REL-006` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `REL-007` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `ROOT-001` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `ROOT-002` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `ROOT-003` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `SAFE-001` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `SAFE-002` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `SAFE-003` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `SAFE-004` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `SAFE-005` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `SAFE-006` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `TXT-001` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |
| `TXT-002` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_options_flow.py` | Live: upgrade, 29-player identity and metadata baseline |

### CI-Gates für diese Evidenz

- Quality Python 3.13 und 3.14
- vollständiger Pytest-Lauf
- Ruff und Ruff Format
- JSON, YAML und Compileall
- Specification Contract und Stable Contract
- Secret-/Privacy-Scan
- HACS Validation und Hassfest
- releasegleicher privater Paketbau mit SHA-256 und `BUILD_COMMIT`

### Noch nicht als bestanden markiert

- Migration im produktiven Home Assistant
- 29-Player-Identitäts- und Metadatenbaseline
- visuelle Prüfung auf iPhone, iPad und Desktop
- kontrollierte Entfernung und Wiederherstellung eines normalen nicht spielenden Players
- separate Serverhistorien-Aktion
- Scheduler-, Reload-, Neustart- und Rollbacknachweis
<!-- EMBI-0.9-EVIDENCE-END -->
