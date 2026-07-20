# Stable release process

This is the single authoritative release procedure for EMBi.

## Preparation

1. Start `release/x.y.z` from the current `main`.
2. Update the version only in the canonical runtime and manifest sources.
3. Move the relevant notes from `Unreleased` to a dated `x.y.z` section in `CHANGELOG.md`.
4. Use exactly one implementation pull request against `main`.

Do not commit patch-transfer files, chat briefings, release-request records, test ZIPs, RC-only helpers, retry workflows, operations PRs, or finalizer PRs.

## Dependency-safe validation order

Every build and release workflow must use this order:

1. Check out the exact source commit.
2. Set up Python.
3. Read the version with:

   ```bash
   python -I scripts/read_version.py
   ```

4. Install test and Home Assistant dependencies.
5. Import or test integration code.

Before dependencies are installed, no module from EMBi, Home Assistant, or `pyemby` may be imported.

## Pull-request validation

The final unchanged PR head must pass:

- Pytest on Python 3.13 and 3.14
- Ruff check and Ruff format check
- MyPy and compileall
- JSON and YAML validation
- translation parity
- legacy migration, stable, and repository contracts
- privacy and secret scan
- HACS Validation and Hassfest
- deterministic unpublished package build

Merge only by squash and include:

```text
Signed-off-by: Seger <Seger85@users.noreply.github.com>
```

## Automated publication

The stable publisher runs only when a merged pull request:

- targets `main`
- originates from this repository
- uses the exact branch `release/x.y.z`

The publisher must:

1. check out the exact squash-merge commit
2. resolve the version dependency-free
3. verify that `main` contains the exact release commit and that the changelog contains the version
4. reject an existing tag or release
5. rerun the complete quality, contract, HACS, and Hassfest validation
6. build the deterministic package for the merge commit
7. create an annotated `vX.Y.Z` tag on that exact commit
8. publish a regular, non-draft, non-prerelease release marked as Latest
9. publish exactly `embi.zip` and `embi.zip.sha256`
10. download both assets again
11. verify SHA-256 and byte identity
12. verify the tag target and Latest release
13. delete the release branch only after all verification succeeds

A normal stable release does not use a release-request PR, finalizer, retry workflow, operations PR, test release, RC, or prerelease.
