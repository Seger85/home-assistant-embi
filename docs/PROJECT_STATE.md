# EMBi Project State

## Production

- Installed version: `v0.3.0-rc1` via the public HACS custom repository
- Home Assistant: Core 2026.7.2
- Existing config entry: retained and loaded
- Media-player entities: 28
- Base `ReportedDeviceId` values behind the players: 25
- Historical `/Devices` records observed during the live analysis: 74
- Existing entity IDs, unique IDs, and individual names: retained
- Push updates and active-playback detection: working
- Legacy YAML: none
- Active repairs: none
- Stale, restored, or orphaned EMBi entities: none
- Server cleanup: disabled
- Registry or server deletions during verification: none

No raw private device identifiers, credentials, diagnostics, or internal config-entry identifiers are stored in this document.

## Live verification

The 0.2.0 to 0.3.0-rc1 upgrade was installed through HACS and verified after a Home Assistant restart.

Confirmed:

- manifest version `0.3.0-rc1`
- existing Config Entry retained
- all 28 media players remain attached to the Config Entry
- live playback state and pyemby push updates work
- `sensor.emby_users_watching` follows active playback
- separate REST library counters continue to work
- no duplicate-unique-ID errors
- no EMBi runtime exceptions
- Home Assistant configuration valid
- server cleanup disabled by default
- server deletion menu hidden while cleanup is disabled
- diagnostics redact credentials and device identities

Not executed:

- registry deletion
- Emby server-history deletion
- stable 0.3.0 release

## Repository state

- Repository visibility: public
- Default branch: `main`
- Integration branch: `develop`
- Public history was intentionally not rewritten
- `develop` was synchronized with `main` through PR #9
- release and repository governance was merged through PR #10
- EMBi 0.3.0-rc2 runtime and safety hardening was merged through PR #12
- automated release-request branches were added through PR #13
- release `latest` verification was corrected through PR #14
- future Dependabot PRs target `develop`
- Ruleset `Protect main and develop` is active
- required checks use stable names
- automated tag- and release-generation is present on `develop`

## 0.3.0-rc2 release status

- Release tag: `v0.3.0-rc2`
- Tag target: `f69224ff6dc6609f2923e391dda428dd0b91bf69`
- GitHub release: published as a prerelease
- Latest stable release: none; rc2 is not marked as `latest`
- Release assets: `embi.zip` and `embi.zip.sha256`
- Temporary release-request branch: removed automatically after verification
- Runtime code in the tag: version `0.3.0-rc2`
- HACS live upgrade from rc1 to rc2: not yet executed

## 0.3.0-rc2 scope

- deduplicate allow-all values from repeated historical device records
- count unique client identities in bulk-action UI text
- exclude every active state from Home Assistant registry cleanup, including legacy and ignored entries
- revalidate cleanup candidates immediately before registry removal
- make destructive server-record labels unambiguous with app, version, activity, and a short record ID
- never return stored connection or cleanup API keys as password-field defaults
- preserve existing keys when the user leaves the replacement field empty
- preserve the `ReportedDeviceId.AppName` entity/unique-ID contract
- keep diagnostics redaction intact

## Validation status

Completed on PR #12 and the final rc2 release verification:

- `Quality (Python 3.13)`: passed
- `Quality (Python 3.14)`: passed
- JSON parsing: passed
- YAML parsing: passed
- Python compilation: passed
- Unit tests: passed; 24 tests in the rc2 test suite
- Ruff lint: passed
- Ruff formatting: passed
- official HACS validation: passed
- Hassfest: passed
- synthetic test identities only
- release tag target: verified
- prerelease status: verified
- not-`latest` status: verified
- `embi.zip`: verified
- `embi.zip.sha256`: verified

## HACS release status

The published release line now includes `v0.3.0-rc2`. The Home Assistant installation remains on `v0.3.0-rc1` until the controlled HACS upgrade and restart are performed. HACS beta/prerelease display must remain enabled.

## Release safety gate

0.3.0-rc2 must be live-tested before any stable 0.3.0 decision because the changes affect runtime filtering, destructive-action candidate selection, secret handling, and maintenance UI labels.

Without a new explicit approval from Gerry:

- do not move or replace the `v0.3.0-rc2` tag
- do not publish stable 0.3.0
- do not remove entity-registry entries
- do not delete Emby server records
