# Autonomous maintenance and stable release process

This is the single authoritative maintenance and release procedure for EMBi.

## Operating model

EMBi is maintained without routine manual approval:

- Dependabot checks GitHub Actions on the sixth day of every month at 03:00 Europe/Berlin.
- Dependabot checks Python development dependencies on the sixth day of every month at 03:15 Europe/Berlin.
- Security updates may still be opened outside the monthly version-update window.
- All update levels, including major updates, are eligible for automatic integration.
- Each ecosystem remains grouped, rebases automatically, and may keep up to ten pull requests open.
- A Dependabot pull request is squash-merged only after every required validation succeeds.
- A six-hourly recovery sweep picks up validated or newly updated Dependabot pull requests.
- Failed workflows are retried once. The automation then applies deterministic Ruff formatting and safe lint fixes, dispatches all required validation workflows again, and merges only after complete success.
- A semantically incompatible update that cannot be repaired mechanically remains safely unmerged. The exact failed head is marked as exhausted and is reconsidered automatically when Dependabot updates or rebases it.

No routine review, confirmation, comment, push, release branch, release pull request, or manual merge is required.

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

The stable publisher runs every six hours. It publishes only when the current `main` commit is newer than the latest matching version tag. This batches the two monthly Dependabot groups into a single stable patch release whenever they complete within the same maintenance window.

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

A failed validation stops before the candidate commit, tag, or release is published. The next scheduled run retries automatically.

## HACS delivery

HACS discovers the newest regular GitHub release and installs `embi.zip` because `hacs.json` declares `zip_release: true` and `filename: embi.zip`. A successfully verified release therefore appears as an EMBi update in Home Assistant without an additional repository action.

## Rollback and retention

HACS can install an earlier tagged EMBi version at any time. Old stable releases are intentionally retained until they are removed manually as part of long-term release housekeeping.
