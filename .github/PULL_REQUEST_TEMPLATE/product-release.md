## Scope

- Target version:
- Implementation branch:
- Supported migration baseline:

## Requirement evidence

- [ ] Product behavior is covered by current behavior tests.
- [ ] Published upgrade paths are covered under `tests/migration`.
- [ ] German and English UI copy are complete and schema-identical.
- [ ] Desktop and mobile visual QA is attached or explicitly marked as a post-installation check.
- [ ] HACS and release contracts are covered.

## Safety

- [ ] Playing and paused players cannot be removed.
- [ ] Saved visibility remains enforced after setup, reload, and restart.
- [ ] Entity removal checks exact domain, platform, config entry, and unique ID.
- [ ] Emby server history is not modified by Home Assistant visibility reconciliation.
- [ ] Existing entity IDs, names, areas, labels, and aliases are preserved where applicable.
- [ ] No direct `.storage` edits.

## Release readiness

- [ ] Python 3.13 and 3.14 quality jobs pass.
- [ ] HACS Validation and Hassfest pass.
- [ ] Manifest, runtime, tag, and release versions agree.
- [ ] `embi.zip` and `embi.zip.sha256` are published and byte-verified.
- [ ] Release is stable, latest, not draft, and not prerelease.

## Repository cleanup

Document what was deleted, consolidated, updated, and intentionally retained.
