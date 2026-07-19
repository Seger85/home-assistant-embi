# Stable release checklist

- All final pull-request checks pass on the same head commit.
- Manifest and runtime versions match.
- The release-equivalent package contains the integration files at the archive root, without an additional repository directory.
- `embi.zip.sha256` verifies the published ZIP.
- `BUILD_COMMIT` matches the exact source commit during package validation.
- HACS validation and Hassfest pass.
- The merged release workflow creates an annotated tag, a non-prerelease latest release, and exactly the documented assets.
- The implementation branch is removed only after release verification.
