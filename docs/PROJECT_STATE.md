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

- Repository visibility: public
- Development branch: `develop`
- Development version: `0.3.0-rc1`
- Live-test status: not installed in production yet
- Merge status: blocked until Home Assistant live tests and explicit approval by Gerry

## CI status

- Quality workflow: passed on Python 3.13 and 3.14
- Ruff lint and format checks: passed
- Unit tests: passed
- Hassfest: passed
- Official HACS action: passed against the public repository
- HACS metadata checks temporarily ignored: `brands`, `description`, `license`, and `topics`
- The metadata exceptions do not skip repository structure, `hacs.json`, integration manifest, or downloadable-content validation

## Known remaining work

- Install the release candidate through the public HACS custom repository
- Live migration test from EMBi 0.2.0 to 0.3.0-rc1
- Confirm that all 28 existing media-player entity IDs remain unchanged
- Test the options migration and all options menus
- Server-cleanup safety test
- UI and theme quality assurance on iPhone, iPad, and desktop
- Finalize repository description/topics and remove temporary HACS metadata exceptions when applicable
- Final changelog review and release decision

## Release safety gate

The pull request from `develop` to `main` must remain a draft. Do not merge, publish a stable release, perform server-side cleanup, or install this release candidate in production without a new explicit approval from Gerry after the documented live tests.
