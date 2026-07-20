# Autonomous maintenance and stable release process

This is the single authoritative maintenance and release procedure for EMBi.

## Operating model

EMBi is maintained without routine manual approval:

- Dependabot checks GitHub Actions every day at 03:00 Europe/Berlin.
- Dependabot checks Python development dependencies every day at 03:15 Europe/Berlin.
- All update levels, including major updates, are eligible for automatic integration.
- A Dependabot pull request is squash-merged only after every required validation succeeds.
- A scheduled hourly sweep picks up validated Dependabot pull requests that were not merged during their initial event run.
- Failed required workflows are retried once automatically. A persistently failing update remains open and cannot reach `main` or a release.

No routine review, confirmation, release branch, release pull request, or manual merge is required.

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

## Required pull-request validation

Every Dependabot or implementation pull request must pass:

- Pytest on Python 3.13 and 3.14
- Ruff check and Ruff format check
- MyPy and compileall
- JSON and YAML validation
- translation parity
- legacy migration, stable, and repository contracts
- privacy and secret scan
- HACS Validation and Hassfest
- deterministic unpublished package build

The automatic merge workflow requires successful runs named:

- `Quality`
- `Test package`
- `HACS validation`
- `Hassfest`

No failing or incomplete pull request is merged.

## Autonomous stable publication

Every accepted push to `main` starts the stable publisher. A five-minute debounce bundles closely spaced Dependabot merges into one patch release. A newer `main` push cancels the older pending publisher and becomes the only release candidate.

The publisher supports two paths:

1. If the version in `manifest.json` and `const.py` has no existing tag, publish that prepared version.
2. If the current version is already tagged and `main` contains newer validated changes, increment the patch version automatically with `scripts/prepare_automatic_release.py`.

The publisher must:

1. verify that the checked-out commit is still the latest `main`
2. resolve the current version dependency-free
3. verify that the current release tag is an ancestor of the new candidate
4. prepare the next patch identity and dated changelog section when required
5. create a local immutable candidate commit before validation
6. run the complete quality, contract, HACS, and Hassfest validation
7. build deterministic `embi.zip` and `embi.zip.sha256` for the exact candidate commit
8. push the candidate commit to `main` only after all validation succeeds
9. create an annotated `vX.Y.Z` tag on that exact commit
10. publish a regular, non-draft, non-prerelease release marked as Latest
11. publish exactly `embi.zip` and `embi.zip.sha256`
12. download both assets again and verify SHA-256 and byte identity
13. verify the tag target and Latest release

A failed validation stops before the candidate commit, tag, or release is published.

## Rollback and retention

HACS can install an earlier tagged EMBi version at any time. Old stable releases are intentionally retained until they are removed manually as part of long-term release housekeeping.
