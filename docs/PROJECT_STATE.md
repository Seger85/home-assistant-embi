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
- Server maintenance: disabled

No raw private device identifiers, credentials, diagnostics, or internal config-entry identifiers are stored in this document.

## Published release

`v0.3.0-rc2` remains an immutable public prerelease on commit `f69224ff6dc6609f2923e391dda428dd0b91bf69`. It is not marked as latest and includes the verified HACS archive and checksum.

## Repository state

- public repository
- default branch: `main`
- integration branch: `develop`
- protected pull-request workflow with stable required checks
- validated release-request automation
- no open rc2 implementation pull request

## 0.3.0-rc3 development target

The additional maintenance requirements are implemented as `0.3.0-rc3` because rc2 has already been published and will not be moved or replaced.

Scope:

- manual maintenance filtered by last-activity age
- default threshold: 365 days
- separate automatic-maintenance switch, default off
- explicit warning and activation phrase
- one initial run 120 seconds after conscious activation
- recurring run every 24 hours
- no per-run candidate cap
- active players and records without a valid timestamp are excluded
- per-record error isolation
- optional Home Assistant registry follow-up after successful server maintenance
- fresh server revalidation and exact `ReportedDeviceId.AppName` matching before registry follow-up
- registry changes only during a controlled reload and without a current entity state
- aggregate diagnostics without private identities

## Identity contract

- `Id`: historical server record used only by the server-maintenance endpoint
- `ReportedDeviceId`: durable raw client identity and device-wide ignore rule
- `ReportedDeviceId.AppName`: pyemby player key and existing Home Assistant unique ID

No entity-ID or unique-ID migration is introduced.

## Release safety gate

Before publishing rc3, both Quality versions, JSON/YAML validation, Ruff, unit tests, HACS validation, and Hassfest must pass. Tests cover uncapped processing, age filtering, active-player protection, invalid timestamps, duplicate history records, and post-operation registry eligibility. No secrets or real private device identities may exist in the diff.

After publication and before stable 0.3.0, the release requires a controlled HACS installation, backup, UI review, 120-second first-run verification, safe maintenance testing, and confirmation that all existing entity IDs and unique IDs remain stable.
