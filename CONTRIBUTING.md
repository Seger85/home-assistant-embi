# An EMBi mitarbeiten

## Grundsätze

- Bestehende Entity-IDs und eindeutige IDs erhalten. Änderungen daran benötigen einen konkreten Nutzen und geprüfte Migrationen.
- Löschaktionen einzeln auswählen beziehungsweise regelbasiert freigeben, frisch validieren und Teilergebnisse speichern. Unklare Aktivität schützt den Client.
- Home Assistants offizielle APIs verwenden; keine direkten `.storage`-Änderungen.
- Keine Schlüssel, privaten Diagnosen, Produktionskennungen oder temporären Patchworkflows ins Repository aufnehmen.
- `strings.json`, Englisch und Deutsch strukturell gleich halten. Nutzerausgaben verständlich formulieren.
- Historische Optionsmigrationen in `legacy_migration.py` und entsprechende Tests in `tests/migration/` belassen.

## Prüfungen

Die schnellen Tests laufen in CI unter Python 3.13 und 3.14. Zusätzlich wird `tests_ha/` mit echtem Home Assistant unter Python 3.14 geprüft: mindestens die Version aus `hacs.json` (derzeit 2026.7.2) und die festgelegte aktuelle Testversion aus `requirements_test_ha.txt` (derzeit 2026.9.3).

Schnelle Prüfungen vom Repository-Hauptverzeichnis aus:

```bash
python -I scripts/read_version.py
python -m pip install --upgrade pip -r requirements_test.txt
ruff check .
ruff format --check .
pytest -q
python -m compileall -q custom_components/emby scripts tests tests_ha
python scripts/validate_legacy_migration_contract.py
python scripts/validate_stable_contract.py
python scripts/validate_repository_references.py
python scripts/secret_scan.py
mypy --ignore-missing-imports --follow-imports=skip \
  custom_components/emby/options_model.py \
  custom_components/emby/player_context.py \
  custom_components/emby/options_runtime.py \
  custom_components/emby/registry_state.py \
  custom_components/emby/player_actions.py \
  custom_components/emby/player_reconciliation.py \
  custom_components/emby/sensor_registry.py \
  custom_components/emby/session_state.py \
  custom_components/emby/player_identity.py \
  custom_components/emby/session_stream.py
```

Tests mit echtem HA in einer Python-3.14-Umgebung:

```bash
python -m pip install -r requirements_test_ha.txt
pytest tests_ha -q
```

**Die beiden Testsuiten in getrennten Prozessen starten.** `tests/conftest.py` verwendet gezielte HA-Ersatzobjekte; diese dürfen die echten HA-Tests nicht beeinflussen. Die Laufzeittests verwenden einen lokalen HTTP-/WebSocket-Testserver und greifen nicht auf einen produktiven Emby-Server zu.

Paket bauen und Prüfsumme kontrollieren:

```bash
python scripts/build_package.py \
  --output-dir dist \
  --expected-version "$(python -I scripts/read_version.py)" \
  --commit "$(git rev-parse HEAD)"
(cd dist && sha256sum --check embi.zip.sha256)
```

Vor der Installation der Abhängigkeiten nur die Version mit `python -I scripts/read_version.py` auslesen; dabei keine Integrationsmodule importieren. CI prüft zusätzlich JSON, YAML, HACS und Hassfest.

## Pull Requests

Beschreibe das konkrete Problem, das veränderte Verhalten, Tests, Migration und Rückweg. Verwende einen eigenen Branch und einen Pull Request gegen `main`. Während der abschließenden Checks bleibt der geprüfte Commit unverändert. Erst nach erfolgreichen Prüfungen wird per Squash gemergt.

Release-Commits verwenden `Signed-off-by: Seger <Seger85@users.noreply.github.com>`. Änderungen an der Oberfläche brauchen eine Prüfung auf Desktop, iPhone und iPad oder einen ausdrücklich dokumentierten noch offenen Gerätetest. Siehe [UI-Prüfung](docs/ui-qa.md).

Der verbindliche Veröffentlichungsablauf steht in [RELEASING.md](RELEASING.md).
