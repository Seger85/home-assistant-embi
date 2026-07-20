# Contributing to EMBi

## Development principles

- Preserve existing entity IDs and unique IDs unless an explicit, tested migration requires a change.
- Destructive operations require an exact selection, fresh validation, and partial-result handling.
- Never edit Home Assistant `.storage` files directly.
- Never commit credentials, private diagnostics, production identifiers, patch-transfer files, chat briefings, or temporary workflows.
- Keep `strings.json`, English, and German translations schema-identical.
- Keep historical upgrade logic inside `custom_components/emby/legacy_migration.py` and historical tests inside `tests/migration/`.

## Supported development environments

CI runs on Python 3.13 and Python 3.14. Changes must pass on both versions.

## Local setup and validation

Run the commands from the repository root in this order:

```bash
python -I scripts/read_version.py
python -m pip install --upgrade pip -r requirements_test.txt

python -m json.tool custom_components/emby/manifest.json >/dev/null
python -m json.tool custom_components/emby/strings.json >/dev/null
python -m json.tool custom_components/emby/translations/de.json >/dev/null
python -m json.tool custom_components/emby/translations/en.json >/dev/null
python -m json.tool hacs.json >/dev/null

python -m compileall -q custom_components/emby scripts tests
mypy --ignore-missing-imports --follow-imports=skip \
  custom_components/emby/options_model.py \
  custom_components/emby/player_context.py \
  custom_components/emby/options_runtime.py \
  custom_components/emby/registry_state.py \
  custom_components/emby/player_actions.py \
  custom_components/emby/player_reconciliation.py \
  custom_components/emby/sensor_registry.py
ruff check .
ruff format --check .
pytest -q
python scripts/validate_legacy_migration_contract.py
python scripts/validate_stable_contract.py
python scripts/validate_repository_references.py
python scripts/secret_scan.py

rm -rf dist
python scripts/build_package.py \
  --output-dir dist \
  --expected-version "$(python -I scripts/read_version.py)" \
  --commit "$(git rev-parse HEAD)"
(cd dist && sha256sum --check embi.zip.sha256)
```

Before dependency installation, do not import EMBi, Home Assistant, or `pyemby`. The version must first be read only through `python -I scripts/read_version.py`.

## Pull requests

- Use a focused branch and exactly one pull request against `main`.
- Describe behavior, migration impact, safety impact, tests, and repository cleanup.
- Keep the final PR head immutable while required checks run.
- Merge by squash only after all required checks pass.
- Release commits use `Signed-off-by: Seger <Seger85@users.noreply.github.com>`.
- Product UI changes require desktop, iPhone, and iPad verification or a clearly documented post-installation check.

The only supported stable release process is documented in [RELEASING.md](RELEASING.md).
