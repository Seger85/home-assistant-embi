## Scope

- Change type: product / maintenance / documentation
- Target version, when applicable:
- Branch:
- Migration impact:

## Validation

- [ ] Python 3.13 and 3.14 tests pass.
- [ ] Ruff, format, MyPy, compileall, JSON, and YAML checks pass.
- [ ] Legacy migration, stable, and repository contracts pass.
- [ ] Privacy and secret scan passes.
- [ ] Deterministic test package passes.
- [ ] HACS Validation and Hassfest pass.
- [ ] UI changes were checked on desktop, iPhone, and iPad or documented as a post-installation check.

## Safety

- [ ] Playing and paused players remain protected.
- [ ] Entity removal checks exact domain, platform, config entry, and unique ID.
- [ ] Emby server history is not modified by Home Assistant visibility reconciliation.
- [ ] Existing entity IDs, names, areas, labels, and aliases remain unchanged unless explicitly migrated.
- [ ] No direct `.storage` edits.
- [ ] No credentials, production identifiers, patch-transfer files, or temporary workflows are included.

## Repository impact

Document what was deleted, consolidated, updated, and intentionally retained.

Stable releases must follow [RELEASING.md](../../RELEASING.md).
