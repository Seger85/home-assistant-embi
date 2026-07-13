# EMBi Project State

## Production

- Production version: EMBi 0.3.0-rc1
- Installation source: public HACS custom repository release `v0.3.0-rc1`
- Production Home Assistant: Core 2026.7.2
- Config entry: `01KXDH0G0CK724G1STHY69B22A`
- Production state: loaded
- Media-player entities: 28
- Existing entity IDs: preserved
- Existing unique IDs: preserved
- Individual entity names: preserved
- Legacy YAML: none
- Active EMBi repairs: none
- Stale, restored or orphaned EMBi entities: none

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

Not yet approved or executed:

- destructive server-cleanup test
- final visual and options-flow QA on iPhone, iPad and desktop
- stable 0.3.0 release

## Repository state

- Repository visibility: public
- Default branch: `main`
- Integration branch: `develop`
- Development version: `0.3.0-rc1`
- PR #1 was merged on 14 July 2026 despite its documented Draft release gate
- five Dependabot PRs were subsequently merged into `main`
- public history was intentionally not rewritten because no secret or unsafe runtime change was published
- `develop` was synchronized back with `main` through PR #9
- future Dependabot PRs target `develop`
- release and branch governance remediation is being prepared separately

## CI status

- Quality workflow: passed on Python 3.13 and 3.14
- Ruff lint and format checks: passed
- Unit tests: passed
- Hassfest: passed
- Official HACS action: passed against the public repository
- HACS metadata checks temporarily ignored: `brands`, `description`, `license`, and `topics`
- The metadata exceptions do not skip repository structure, `hacs.json`, integration manifest, or downloadable-content validation

## HACS release status

Home Assistant currently reports:

```text
installed_version: v0.3.0-rc1
latest_version: b9f6285
```

`b9f6285` is a repository commit containing CI/test dependency maintenance, not a new EMBi version. Do not install it as an application update. While only a prerelease exists, HACS beta/prerelease display must remain enabled so `v0.3.0-rc1` remains the selected release line.

## Known remaining work

- complete options-flow and responsive UI QA
- perform a controlled server-cleanup safety test only after a separate explicit approval
- finalize repository description/topics and remove temporary HACS metadata exceptions where possible
- apply GitHub rulesets for `main` and `develop`
- validate the hardened automated release workflow without publishing a stable release
- final changelog review and stable-release decision

## Release safety gate

Do not publish stable version 0.3.0, create a stable release tag, or perform server-side cleanup without a new explicit approval from Gerry after the remaining documented tests.
