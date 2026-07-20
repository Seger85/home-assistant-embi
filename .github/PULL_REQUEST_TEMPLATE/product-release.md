## Scope

- Target version:
- Implementation branch:
- Supported upgrade baseline:
- Legacy migration fixture reference, when applicable:

## Requirement evidence

- [ ] Product behavior is covered by current regression tests and repository contracts.
- [ ] Historical upgrade translation remains isolated from normal runtime behavior.
- [ ] German and English UI copy are complete and schema-identical.
- [ ] Desktop and mobile visual QA are attached when UI behavior changes.
- [ ] Live Home Assistant QA is attached where required.
- [ ] HACS and stable-release contracts are covered.

## Safety

- [ ] Playing and paused players cannot be removed.
- [ ] Disabled but valid entities are not classified as orphans.
- [ ] Removed players remain absent after reload.
- [ ] Existing entity IDs, unique IDs and custom names are preserved.
- [ ] Unrelated entities and Emby server history remain untouched.
- [ ] No direct `.storage` edits.

## Release readiness

- [ ] Version is read dependency-free before validation dependencies are installed.
- [ ] Manifest, runtime and tag versions agree.
- [ ] Python 3.13 and 3.14 quality checks are green on the final head.
- [ ] HACS validation and Hassfest are green.
- [ ] `embi.zip` and `embi.zip.sha256` are built and verified.
- [ ] Release is stable, latest, not draft and not prerelease.

## Deviations

List any requirement not implemented exactly as specified. A safety or release blocker requires explicit approval.
