# 11 – Release Contract

## 1. Target

Publish **EMBi 0.9.0** as a regular stable release.

No dev, beta, RC, prerelease, draft or alternate patch version.

## 2. Branch and PR flow

1. specification contract merged to `develop`,
2. one implementation branch from current `develop`,
3. one primary implementation PR to `develop`,
4. CI artifact used for private live acceptance,
5. acceptance fixes stay on the same branch/PR,
6. merge to `develop`,
7. promotion PR `develop` → `main`,
8. tag `v0.9.0` on the exact promoted `main` commit,
9. publish stable GitHub release.

No public development release is required.

## 3. Required checks

- manifest version 0.9.0,
- runtime version 0.9.0,
- translation contract passes,
- migration tests pass,
- acceptance matrix complete,
- HACS metadata valid,
- ZIP valid,
- checksum valid,
- tag points to exact main commit,
- release latest,
- not draft,
- not prerelease.

## 4. Assets

- `embi.zip`
- `embi.zip.sha256`

The checksum file contains the SHA-256 of the exact ZIP.

## 5. ZIP content

Only the installable custom component in HACS/Home Assistant structure. No tests, docs, `.git`, CI, caches or development artifacts.

## 6. HACS availability

Publish the regular GitHub release, verify HACS metadata and release-asset contract, verify stable resolution and record that local HACS display may update after cache refresh. Final project-chat acceptance verifies local HACS visibility and installation.

## 7. Documentation

Before tagging, README explains the whole integration, uses user-oriented examples, covers setup, player management, cleanup and safety, and contains no stale RC wording.

## 8. Execution behavior

The GitHub executor continues without intermediate handoff until implementation, tests, CI, merge, promotion, tag, stable release, assets and HACS contract are complete, unless a real permission or platform blocker exists.

## 9. Final report

Return only changes, commit SHAs, PRs, CI, release/tag, assets/checksums, HACS verification, remaining risks and next live test.
