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
- release and repository governance was merged to `develop` through PR #10
- future Dependabot PRs target `develop`
- Ruleset `Protect main and develop` is active
- required checks use stable names
- automated tag-driven release generation is present on `develop`
- no rc2 tag or release exists

## Development

- Current hardening version: `0.3.0-rc2`
- Runtime hardening branch: `fix/rc2-runtime-safety`
- Draft PR: #12
- PR #12 remains Draft and must later use Squash and merge
- `main` must not be reset or rewritten

### 0.3.0-rc2 scope

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

Completed before synchronizing PR #12 with the governance commit:

- Python compilation: passed
- Unit tests: 24 passed
- Ruff lint: passed
- Ruff formatting: passed
- JSON parsing: passed
- official HACS validation: passed
- Hassfest: passed
- synthetic test identities only

The synchronized PR #12 head is conflict-free and ready for the required full GitHub CI rerun with the stable ruleset check names.

## HACS release status

The installed release remains `v0.3.0-rc1`. A newer repository commit is not an application release. While only a prerelease exists, HACS beta/prerelease display must remain enabled so the published release line remains selected.

## Release safety gate

0.3.0-rc2 is recommended instead of a stable 0.3.0 because the fixes affect runtime filtering, destructive-action candidate selection, secret handling, and maintenance UI labels.

Without a new explicit approval from Gerry:

- do not merge PR #12
- do not create or move a tag
- do not publish a release
- do not remove entity-registry entries
- do not delete Emby server records
