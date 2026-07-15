# Entwicklung

## Unterstützte Umgebung

- Python 3.13 und 3.14
- Home Assistant 2026.7.2 als aktuelle Live-Basis
- Ruff
- Pytest
- HACS Validation
- Hassfest

## Lokale Prüfung

```bash
python -m pip install --upgrade pip -r requirements_test.txt
python -m json.tool custom_components/emby/manifest.json >/dev/null
python -m json.tool custom_components/emby/strings.json >/dev/null
python -m json.tool custom_components/emby/translations/de.json >/dev/null
python -m json.tool custom_components/emby/translations/en.json >/dev/null
python -m compileall -q custom_components/emby scripts tests
ruff check .
ruff format --check .
pytest -q
python scripts/validate_stable_contract.py
python scripts/secret_scan.py
```

Releasegleichen Paketbau prüfen:

```bash
rm -rf dist
python scripts/build_package.py \
  --output-dir dist \
  --expected-version 0.3.0 \
  --commit "$(git rev-parse HEAD)"
(cd dist && sha256sum --check embi.zip.sha256)
test "$(cat dist/BUILD_COMMIT)" = "$(git rev-parse HEAD)"
```

## Architekturregeln

- keine neue Plattform ohne neuen freigegebenen Scope
- keine Wartungsentity
- bestehende Unique-ID-Logik nicht verändern
- `Id` nur für exakte Serverhistorie und den zugehörigen `/Devices`-Aufruf
- Registry nur über exakte `ReportedDeviceId.AppName`-Identität
- keine zusätzlichen Cleanup-Anmeldedaten
- keine automatische Ignore-Regel nach Serverbereinigung
- keine direkten `.storage`-Änderungen
- Schedulertermine absolut und persistent
- manuell und automatisch teilen einen Lock
- Store-Fehler fail-closed

## Testanforderungen

Änderungen an Maintenance-Code benötigen Tests für:

- Persistenz und Schema
- Store-Lese- und Schreibfehler
- Scheduler, Catch-up, Reload und Neustart
- Lock und doppelte Callbacks
- Kandidaten-Cutoff, aktive und undatierte Datensätze
- Teilerfolg und kein Batchlimit
- Registry-Queue, Match, tatsächliche Entfernung, Missing und Schutzfälle
- exakte Identitäten ohne Präfix- oder Teilstring-Match
- Options Draft, Apply, Discard und Dirty-Sperre
- Migration und unveränderte Custom-Werte
- Logging, Notifications und Datenschutz
- Stable-, HACS- und Paketvertrag

## Übersetzungen

`strings.json` ist die englische Quelle und muss byteinhaltlich mit `translations/en.json` übereinstimmen. Die deutsche Datei muss dieselbe rekursive Schlüsselstruktur besitzen. Private IDs oder Live-Systemwerte gehören nie in Übersetzungen oder Dokumentation.

## Paketvertrag

`scripts/build_package.py` ist der gemeinsame Builder für Quality, Test package und Release. Das ZIP enthält ausschließlich Dateien aus `custom_components/emby` direkt im ZIP-Root.

Erforderlich:

- `__init__.py`
- `manifest.json`
- `strings.json`
- `translations/de.json`
- `translations/en.json`

Unzulässig:

- Tests
- Dokumentation
- `.github`
- Repositorymetadaten
- `__pycache__`, `.pyc`, `.pyo`
- private Daten

## Scope Freeze 0.3.0

Nicht in 0.3.0 ergänzen:

- Report-only-Modus
- Bibliothekssensoren
- Medien- und Benutzerstatistiken
- neue Plattformen
- Premium-Code
- zusätzliche Produktvisionen
