# 10 – Test and Acceptance Matrix

## 1. Evidence rule

Every blocker in `requirements.yaml` needs an implementation location, automated-test evidence, CI evidence, required live result, required visual result and final status.

The automated evidence below is bound to the exact pull-request head by the permanent Quality, Specification Contract, HACS, Hassfest and Test package workflows. The private Home Assistant and visual acceptance remains deliberately open until the exact final artifact is installed.

## 2. Correct private-acceptance baseline

The verified pre-upgrade baseline for the private 0.9.0 acceptance is:

- EMBi `0.3.0`
- one loaded Config Entry
- `69` Emby server device-history records
- `30` enabled and loaded EMBi `media_player` entities
- no current registry orphan
- automatic cleanup disabled
- manual cleanup threshold `365` days
- automatic cleanup threshold `365` days

A different entity count is acceptable only when a real Emby-client change is documented immediately before the live test.

## 3. Automated test groups

### Unit and model tests

- `tests/test_device_identity.py`
- `tests/test_player_context_090.py`
- `tests/test_options_model_090.py`
- `tests/test_options_review_090.py`
- `tests/test_player_actions_090.py`
- `tests/test_active_visibility_safety_090.py`

### Options-flow, lifecycle and integration-contract tests

- `tests/test_options_flow.py`
- `tests/test_options_flow_contract.py`
- `tests/test_entry_lifecycle.py`
- `tests/test_update_listener_suppression_090.py`

### Repository, privacy and release-contract tests

- `tests/test_repository_contract.py`
- `tests/test_package_contract.py`
- `tests/test_spec_implementation_090.py`
- `tests/test_no_temporary_workflows_090.py`
- `scripts/validate_spec_contract.py`
- `scripts/validate_stable_contract.py`
- `scripts/secret_scan.py`

## 4. Blocker traceability

<!-- EMBI-0.9-EVIDENCE-START -->

| ID | Implementation evidence | Automated evidence | Live / visual evidence | Status before private acceptance |
|---|---|---|---|---|
| `ROOT-001` | `options_flow.py` | `test_options_flow.py` | Root menu on desktop/mobile | Automated; live pending |
| `ROOT-002` | `options_flow.py`, `options_runtime.py` | `test_options_flow.py` | Counts against 69/30 baseline | Automated; live pending |
| `ROOT-003` | `options_flow.py`, translations | `test_spec_implementation_090.py` | Root menu screenshot | Automated; live pending |
| `DEV-001` | `player_context.py`, `options_devices.py` | `test_player_context_090.py` | Known-user groups | Automated; live pending |
| `DEV-002` | `player_context.py`, `options_devices.py` | `test_player_context_090.py` | Shared users named | Automated; live pending |
| `DEV-003` | `player_context.py`, `options_devices.py` | `test_player_context_090.py` | Without user assignment | Automated; live pending |
| `DEV-004` | `player_context.py` | `test_player_context_090.py` | Technical-access group | Automated; live pending |
| `DEV-005` | `player_context.py` | `test_player_context_090.py` | Unknown client remains unknown | Automated; live pending |
| `DEV-006` | `player_context.py`, `options_runtime.py` | `test_player_context_090.py` | Friendly context, HA name and full entity ID | Automated; live pending |
| `DEV-007` | `player_context.py`, translations | `test_player_context_090.py`, `test_spec_implementation_090.py` | No UUID as primary label | Automated; live pending |
| `DEV-008` | `player_context.py`, `options_devices.py` | `test_player_context_090.py` | Search all required fields | Automated; live pending |
| `DEV-009` | `options_devices.py`, `options_model.py` | `test_options_flow.py`, `test_options_model_090.py` | Single playback-only switch | Automated; live pending |
| `DEV-010` | `options_devices.py`, `options_model.py` | `test_options_flow.py`, `test_active_visibility_safety_090.py` | Automatically show new players | Automated; live pending |
| `DEV-011` | `options_devices.py`, `options_model.py` | `test_options_model_090.py` | User master preserves child rules | Automated; live pending |
| `DEV-012` | `options_devices.py`, `options_flow.py`, `player_context.py` | `test_active_visibility_safety_090.py`, `test_player_actions_090.py` | Playing and paused controls blocked | Automated; live pending |
| `DEV-013` | `player_actions.py` | `test_player_actions_090.py` | Restore and entity verification after reload | Automated; live pending |
| `DEV-014` | `media_player.py`, registry-preserving flow | `test_device_identity.py`, `test_repository_contract.py` | Custom HA name unchanged | Automated; live pending |
| `DEV-015` | `options_model.py` | `test_options_model_090.py` | New-install default only | Automated; live not required |
| `CLN-001` | `options_cleanup.py`, `options_flow.py` | `test_options_flow.py` | One Cleanup root item | Automated; live pending |
| `CLN-002` | `options_cleanup.py` | `test_options_flow.py` | Last run appears once | Automated; live pending |
| `CLN-003` | `options_cleanup.py`, `options_ha_cleanup.py`, `player_actions.py` | `test_player_actions_090.py`, `test_options_flow.py` | Separate server/HA actions | Automated; live pending |
| `CLN-004` | `options_cleanup.py` | `test_options_flow.py` | Zero-candidate page has no empty selector | Automated; live pending |
| `CLN-005` | `options_cleanup.py`, `maintenance_cycle.py` | `test_options_flow.py`, repository cleanup tests | Fresh server data | Automated; live pending |
| `CLN-006` | `cleanup.py`, `player_context.py` | `test_player_actions_090.py` | Playing/paused server records protected | Automated; live pending |
| `CLN-007` | `options_cleanup.py` | `test_options_flow_contract.py` | One final server-deletion confirmation | Automated; live pending |
| `CLN-008` | `options_ha_cleanup.py`, `options_runtime.py` | `test_options_flow.py` | All EMBi players listed | Automated; live pending |
| `CLN-009` | `player_actions.py`, `player_remove.py` | `test_player_actions_090.py` | Idle player hide and removal | Automated; live pending |
| `CLN-010` | `player_actions.py`, `player_remove.py` | `test_player_actions_090.py` | Playing/paused removal blocked | Automated; live pending |
| `CLN-011` | `player_actions.py`, `player_remove.py` | `test_player_actions_090.py` | Server history remains intact | Automated; live pending |
| `CLN-012` | `player_remove.py` | `test_player_actions_090.py` | Removed player does not return after reload | Automated; live pending |
| `CLN-013` | `options_ha_cleanup.py` | `test_options_flow_contract.py` | One final HA-removal confirmation | Automated; live pending |
| `CLN-014` | `player_context.py`, `options_ha_cleanup.py` | `test_player_context_090.py` | Disabled valid entity not orphaned | Automated; live pending |
| `CLN-015` | `player_context.py`, `options_ha_cleanup.py` | `test_player_context_090.py` | Fresh missing-server-match orphan check | Automated; live pending |
| `CLN-016` | `options_cleanup.py`, `options_model.py` | `test_options_flow.py`, `test_options_model_090.py` | Manual remains available with automation off | Automated; live pending |
| `CLN-017` | `options_cleanup.py`, `options_model.py` | `test_options_model_090.py`, `test_options_flow.py` | Exact 364/365 values | Automated; live pending |
| `CLN-018` | `options_model.py` | `test_options_model_090.py` | Upgrade preserves HA-removal setting | Automated; live not required |
| `NAV-001` | `options_flow.py`, `options_draft.py` | `test_options_flow.py`, `test_options_flow_contract.py` | Draft persists until Apply | Automated; live pending |
| `NAV-002` | `options_review.py`, `options_flow.py` | `test_options_review_090.py` | Semantic before/after review | Automated; live pending |
| `NAV-003` | `options_draft.py`, `options_flow.py` | `test_options_flow.py` | Discard resets complete draft | Automated; live pending |
| `NAV-004` | in-memory draft lifecycle | `test_options_flow.py` | X closes without write/reload | Automated; live pending |
| `NAV-005` | `options_flow.py`, mixins | `test_options_flow_contract.py` | Back preserves draft | Automated; live pending |
| `NAV-006` | `options_flow.py`, translations | `test_options_flow.py`, `test_spec_implementation_090.py` | No normal confirmation toggle | Automated; live pending |
| `NAV-007` | `options_cleanup.py`, `options_ha_cleanup.py` | `test_options_flow.py` | Destructive actions blocked with dirty draft | Automated; live pending |
| `MIG-001` | `options_model.py`, `entry_setup.py`, `entry_lifecycle.py` | `test_options_model_090.py`, `test_entry_lifecycle.py` | Effective behavior preserved | Automated; live pending |
| `MIG-002` | unchanged media-player unique-ID contract | `test_device_identity.py`, `test_repository_contract.py` | Same entity IDs/unique IDs | Automated; live pending |
| `MIG-003` | no registry metadata rewrite in migration | `test_options_model_090.py`, `test_repository_contract.py` | Names, aliases, areas, labels, disabled state | Automated; live pending |
| `MIG-004` | `options_model.py` | `test_options_model_090.py`, `test_options_flow.py` | 364 and 365 preserved exactly | Automated; live pending |
| `MIG-005` | `options_model.py`, `entry_setup.py` | `test_options_model_090.py` | Automatic cleanup remains disabled | Automated; live pending |
| `MIG-006` | migration has no registry removal/disable operation | `test_options_model_090.py`, `test_repository_contract.py` | No entity deletion or disabling | Automated; live pending |
| `MIG-007` | `options_model.py` | `test_options_model_090.py` | Technical visibility preserved | Automated; live pending |
| `MIG-008` | schema version 4.0 / options schema 2 | `test_entry_lifecycle.py`, `test_options_model_090.py` | Not required | Automated |
| `SAFE-001` | `player_actions.py`, `player_remove.py`, `player_context.py` | `test_player_actions_090.py`, `test_active_visibility_safety_090.py` | Unknown ownership/playback fails closed | Automated; live pending |
| `SAFE-002` | exact ownership helper and registry checks | `test_player_actions_090.py` | Config entry/platform/unique ID verified | Automated; live pending |
| `SAFE-003` | `player_remove.py` stores exact hidden rule before registry remove | `test_player_actions_090.py` | Hidden rule inspected before removal | Automated; live pending |
| `SAFE-004` | post-reload registry/state verification | `test_player_actions_090.py` | Success only after verification | Automated; live pending |
| `SAFE-005` | `PlayerActionResult`, persistent aggregate summary | `test_player_actions_090.py` | Partial result and safe hidden state | Automated; live pending |
| `SAFE-006` | official Config/Options/Registry/Store APIs only | `test_spec_implementation_090.py`, `secret_scan.py` | Not required | Automated |
| `LOG-001` | maintenance logging severity contract | `test_repository_contract.py` | Zero-deletion success logs INFO | Automated; live pending |
| `LOG-002` | `diagnostics.py`, `models.py` | `test_repository_contract.py`, `test_player_actions_090.py` | Diagnostics fields inspected | Automated; live pending |
| `LOG-003` | `diagnostics.py` redacts API key and host/title context | `test_active_visibility_safety_090.py`, `secret_scan.py` | Live diagnostics redaction | Automated; live pending |
| `TXT-001` | `strings.json`, `translations/en.json`, `translations/de.json` | `test_spec_implementation_090.py`, `validate_stable_contract.py` | Not required | Automated |
| `TXT-002` | final DE/EN copy and user-facing labels | `test_spec_implementation_090.py` | UI terminology screenshot | Automated; live pending |
| `DOC-001` | product-oriented `README.md` | `test_spec_implementation_090.py` | README visual review | Automated; visual pending |
| `DOC-002` | README and supporting docs | `test_spec_implementation_090.py` | Documentation review | Automated; visual pending |
| `REL-001` | `manifest.json`, `const.py`, package workflows | `test_package_contract.py`, `validate_stable_contract.py` | Not required | Automated |
| `REL-002` | no 0.9 dev/RC/public-release workflow action | `test_repository_contract.py`, `test_no_temporary_workflows_090.py` | Not required | Automated |
| `REL-003` | shared package builder and version validators | `test_package_contract.py`, `validate_stable_contract.py` | Runtime 0.9.0 in private HA test; tag/release later | Automated pre-release; live pending |
| `REL-004` | release workflow stable flags | `test_repository_contract.py`, `validate_stable_contract.py` | Publication only after acceptance | Automated pre-release; publication pending |
| `REL-005` | release workflow publishes ZIP and checksum | `test_package_contract.py`, `validate_stable_contract.py` | Publication only after acceptance | Automated pre-release; publication pending |
| `REL-006` | `hacs.json`, deterministic ZIP builder | HACS validation, `test_package_contract.py` | Private artifact installation and later HACS release | Automated; live pending |
| `REL-007` | this matrix plus specification validator | `test_spec_implementation_090.py`, Specification Contract workflow | Not required | Automated once final CI is green |

<!-- EMBI-0.9-EVIDENCE-END -->

## 5. Required migration fixtures or equivalents

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

The corresponding behaviors are covered by `test_options_model_090.py`, `test_entry_lifecycle.py`, `test_device_identity.py`, `test_player_context_090.py` and `test_repository_contract.py`.

## 6. Exact private live acceptance

### L-01 Baseline and upgrade

1. Create a full Home Assistant backup and confirm the Emby restore path.
2. Record the exact pre-upgrade Config Entry state, `69` server-history records, `30` enabled/loaded EMBi media players, registry-orphan count, repairs and diagnostics.
3. Verify artifact checksum and `BUILD_COMMIT` before installation.
4. Install the exact private `0.9.0` artifact and restart Home Assistant.
5. Confirm the existing Config Entry is loaded and manifest/runtime report `0.9.0`.
6. Confirm the same 30 entity IDs and unique IDs unless an immediately documented real client change occurred.
7. Confirm custom names, aliases, areas, labels and enabled/disabled state are unchanged.
8. Confirm cleanup thresholds remain `365` and automatic cleanup remains disabled.

### L-02 Disabled valid entity

Disable one valid EMBi entity, reload, verify it is shown as disabled rather than orphaned, re-enable it and verify the same entity ID and metadata.

### L-03 Hide and remove an idle player

Choose one safely idle test player. Confirm it is neither `playing` nor `paused`. Execute the separate Home Assistant player-removal action, verify the exact hidden rule exists before registry removal, verify the entity is absent, reload again and verify it does not return. Confirm the Emby server-history count is unchanged.

### L-04 Restore

Restore the player from L-03 and verify after reload that exactly one expected entity exists with the expected identity and name behavior.

### L-05 Playback protection

Verify one `playing` player and one `paused` player cannot be hidden or removed. Verify a stopped/idle player becomes eligible only after fresh state evaluation.

### L-06 Server-history separation and zero-candidate state

Open the server-history check with no eligible candidates or a controlled threshold. Confirm no empty selector appears. Any destructive server-history test requires its own final confirmation and must not alter normal player visibility.

### L-07 Scheduler

With automatic cleanup disabled, confirm no next run is scheduled. In a controlled test, enable and Apply once, confirm one schedule and no duplicate callback, then disable and Apply once and confirm the schedule is removed. Restore the production setting to disabled.

### L-08 Draft and semantic review

Verify Back preserves the draft, X discards without write/reload, Discard resets all draft changes, Apply performs one options write and at most one reload, unchanged Apply performs neither, and Review changes shows semantic before/after values.

## 7. Visual acceptance

Minimum coverage:

- desktop 1440×900
- iPhone portrait
- iPad portrait or Split View

Check:

- short root menu
- no clipped headings or horizontal overflow
- no UUID, Config Entry ID or ReportedDeviceId as primary user-facing labels
- full entity ID remains readable
- shared users are named
- search is usable
- Cleanup is coherent and Last run appears once
- no empty selector
- destructive buttons and confirmations are unambiguous and reachable
- German and English copy does not overflow

## 8. Release blockers

- player returns after verified removal
- `playing` or `paused` player is removable
- migration changes entity IDs, unique IDs or registry metadata
- disabled valid entity appears orphaned
- automatic cleanup state or exact thresholds change during migration
- server-history and HA-player actions are coupled
- diagnostics expose API key or server connection details
- translation mismatch
- stale prerelease wording
- release ZIP or checksum mismatch
- failing final CI
- missing final artifact evidence
- missing live or visual acceptance evidence

**Noch nicht als bestanden markiert:** private Home Assistant acceptance, visual acceptance, promotion, tag, public release and HACS stable publication.
