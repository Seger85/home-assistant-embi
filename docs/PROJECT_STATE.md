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

No raw private device identifiers or diagnostics are stored in this repository.

## Development

- Repository visibility: public
- Target branch: `develop`
- Current hardening version: `0.3.0-rc2`
- Runtime hardening branch: `fix/rc2-runtime-safety`
- Separate governance PR #10 remains open and Draft and is not part of rc2 runtime changes
- `main` must not be reset or rewritten

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

Local validation completed for the rc2 implementation candidate:

- Python compilation: passed
- Unit tests: 24 passed
- Ruff lint: passed
- Ruff formatting: passed
- JSON parsing: passed
- synthetic test identities only

GitHub CI, HACS validation, and Hassfest must pass on the Draft PR before any merge consideration.

## Release safety gate

0.3.0-rc2 is recommended instead of a stable 0.3.0 because the fixes affect runtime filtering, destructive-action candidate selection, secret handling, and maintenance UI labels.

Without a new explicit approval from Gerry:

- do not merge the rc2 Draft PR
- do not merge or change Draft PR #10
- do not create or move a tag
- do not publish a release
- do not remove entity-registry entries
- do not delete Emby server records
