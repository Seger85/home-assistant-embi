# Development

Contributions should use a focused branch and a pull request against `main`.

Before opening a pull request, run the repository-configured Ruff formatting and fixes, the Python commands from `.github/workflows/quality.yml`, the complete test suite, `scripts/validate_spec_contract.py`, `scripts/validate_stable_contract.py`, and `scripts/secret_scan.py`.

Do not commit build output, local secrets, patch-transfer files, or temporary workflow files. Preserve stable player and sensor unique-ID contracts and add regression coverage for lifecycle changes.
