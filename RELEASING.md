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

Every Dependabot, automated release, or implementation pull request must pass:

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

## Protected autonomous stable publication

The stable publisher runs every six hours and also supports an internal workflow dispatch. It never pushes a generated version commit directly to protected `main`.

The publisher supports two phases:

1. If the current version is already tagged and `main` contains newer validated changes, it prepares the next patch version on `release/automatic-vX.Y.Z`, creates or reopens a release pull request, and dispatches the autonomous merge workflow.
2. The autonomous merge workflow dispatches all four required validations for that exact release branch, retries transient failures, applies deterministic Ruff repair when possible, and squash-merges only after complete success.
3. After the protected release pull request is merged, the merge workflow dispatches the publisher again.
4. If the version on `main` has no tag, the publisher validates that exact protected merge commit, builds the assets, creates the tag, and publishes the stable release.

The publisher must:

1. verify that the checked-out commit is still the latest `main`
2. resolve the current version dependency-free
3. verify that the current release tag is an ancestor of the new candidate
4. prepare the next patch identity and dated changelog section on an automation-owned branch
5. create or reopen a protected release pull request instead of bypassing repository rules
6. require Quality, Test package, HACS validation, and Hassfest on the exact release candidate
7. merge the release candidate through the normal protected-branch pull-request path
8. revalidate the resulting `main` commit before publication
9. build deterministic `embi.zip` and `embi.zip.sha256` for that exact merge commit
10. create an annotated `vX.Y.Z` tag on that exact commit
11. publish a regular, non-draft, non-prerelease release marked as Latest
12. publish exactly `embi.zip` and `embi.zip.sha256`
13. download both assets again and verify SHA-256 and byte identity
14. verify the tag target and Latest release

A failed validation stops before merge, tag, or release publication. Transient failures are retried automatically. A persistent semantic failure remains safely isolated in its pull request and cannot reach `main`.

## HACS delivery

HACS discovers the newest regular GitHub release and installs `embi.zip` because `hacs.json` declares `zip_release: true` and `filename: embi.zip`. A successfully verified release therefore appears as an EMBi update in Home Assistant without an additional repository action.

## Rollback and retention

HACS can install an earlier tagged EMBi version at any time. Old stable releases are intentionally retained until they are removed manually as part of long-term release housekeeping.
