# EMBi Project State

## Production

- Production version: EMBi 0.2.0
- Production Home Assistant: Core 2026.7.2
- Config entry: `01KXDH0G0CK724G1STHY69B22A`
- Production state: loaded
- Media-player entities: 28
- Legacy YAML: none
- Active repairs: none
- Stale or restored entities: none

## Development

- Development branch: `develop`
- Development version: `0.3.0-rc1`
- Live-test status: not installed in production yet
- Merge status: blocked until Home Assistant live tests and explicit approval by Gerry

## Known remaining work

- UI and theme quality assurance
- Installation through the private HACS repository
- Live migration test from EMBi 0.2.0 to 0.3.0-rc1
- Server-cleanup safety test
- Final changelog review and release decision

## Release safety gate

The pull request from `develop` to `main` must remain a draft. Do not merge, publish a stable release, perform server-side cleanup, or install this release candidate in production without a new explicit approval from Gerry after the documented live tests.
