# Development

Contributions should use a focused branch and a pull request against `main`.

Before opening a pull request, run the repository-configured Ruff formatting and fixes, the Python commands from `.github/workflows/quality.yml`, the complete test suite, `scripts/validate_legacy_migration_contract.py`, `scripts/validate_stable_contract.py`, `scripts/validate_repository_references.py`, and `scripts/secret_scan.py`.

Historical upgrade fixtures are intentionally isolated under the legacy migration contract. New runtime code, normal tests and current documentation must use version-neutral names.

Do not commit build output, local secrets, patch-transfer files, obsolete release-request records, or temporary workflow files. Preserve stable player and sensor unique-ID contracts and add regression coverage for lifecycle changes.
