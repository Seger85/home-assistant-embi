# EMBi Project State

## Production

- Installed version: `v0.3.0-rc1` through the public HACS custom repository
- Home Assistant: Core 2026.7.2
- Existing config entry: retained and loaded
- Media-player entities: 28
- Base reported client identities behind the players: 25
- Historical device records observed during live analysis: 74
- Existing entity IDs, unique IDs, and individual names: retained
- Push updates and active-playback detection: working
- Legacy YAML: none
- Active repairs: none
- Stale, restored, or orphaned EMBi entities: none
- Optional server maintenance: disabled

No raw private device identifiers, credentials, diagnostics, or internal config-entry identifiers are stored in this document.

## Published releases

- `v0.3.0-rc2`: immutable public prerelease on commit `f69224ff6dc6609f2923e391dda428dd0b91bf69`
- `v0.3.0-rc3`: public prerelease on commit `0d776720b527d1285b258159edc8f30b933385ca`

For rc3, both Quality versions, HACS validation, Hassfest, archive generation, checksum generation, prerelease classification, non-latest classification, and tag-target verification completed successfully. The temporary release-request branch was removed by the workflow.

## Repository state

- public repository
- default branch: `main`
- integration branch: `develop`
- protected pull-request workflow with stable required checks
- validated release-request automation
- rc3 implementation merged through PR #16 using Squash and merge
- stable `0.3.0` has not been released

## 0.3.0-rc3 scope

- manual maintenance filtered by last-activity age
- default threshold: 365 days
- separate automatic-maintenance switch, default off
- explicit warning and activation phrase
- one initial run 120 seconds after conscious activation
- recurring run every 24 hours
- no per-run candidate cap
- active players and records without a valid timestamp are excluded
- independent per-record result handling
- optional Home Assistant registry follow-up after successful server maintenance and fresh server revalidation
- aggregate diagnostics without private identities

## Identity contract

- `Id`: one historical server record
- `ReportedDeviceId`: durable raw client identity and device-wide ignore rule
- `ReportedDeviceId.AppName`: pyemby player key and existing Home Assistant unique ID

No entity-ID or unique-ID migration is introduced.

## Remaining live gate

Before stable `0.3.0`, rc3 requires controlled HACS installation with backup, verification that the existing config entry and all entity identities remain unchanged, UI and screenshot review, confirmation that automatic maintenance is disabled by default, deliberate validation of the 120-second first-run behavior, log and diagnostics review, and a tested rollback path.
