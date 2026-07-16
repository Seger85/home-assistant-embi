# Entwicklung

## Aktiver Implementierungsstand

- Repository: `Seger85/home-assistant-embi`
- Frozen Contract: `docs/specs/0.9.0/`
- Implementierungsbranch: `feature/embi-0.9.0`
- Implementierungs-PR: #29 nach `develop`
- Zielversion: `0.9.0`
- `main` bleibt bis zur dokumentierten privaten Abnahme auf Stable `v0.3.0`

## Unterstützte Umgebung

- Python 3.13 und 3.14
- Home Assistant 2026.7.2 als aktuelle Live-Basis
- Ruff und Ruff Format
- Pytest
- HACS Validation
- Hassfest

## Vollständige lokale Prüfung

```bash
python -m pip install --upgrade pip -r requirements_test.txt
python -m json.tool custom_components/emby/manifest.json >/dev/null
python -m json.tool custom_components/emby/strings.json >/dev/null
python -m json.tool custom_components/emby/translations/de.json >/dev/null
python -m json.tool custom_components/emby/translations/en.json >/dev/null
python -m json.tool hacs.json >/dev/null
python -m compileall -q custom_components/emby scripts tests
ruff check .
ruff format --check .
pytest -q
python scripts/validate_spec_contract.py
python scripts/validate_stable_contract.py
python scripts/secret_scan.py
```

Releasegleichen privaten Paketbau prüfen:

```bash
rm -rf dist
python scripts/build_package.py \
  --output-dir dist \
  --expected-version 0.9.0 \
  --commit "$(git rev-parse HEAD)"
(cd dist && sha256sum --check embi.zip.sha256)
test "$(cat dist/BUILD_COMMIT)" = "$(git rev-parse HEAD)"
```

## Architekturregeln

- keine neue Plattform ohne neuen freigegebenen Scope
- ausschließlich `media_player`
- keine Wartungsentity
- bestehende Unique-ID-Logik nicht verändern
- Entity-IDs und Registry-Metadaten migrationsstabil halten
- `Id` nur für den exakten Serverhistorieneintrag
- ReportedDeviceId und interne Schlüssel nicht als primäre UI-Labels verwenden
- technische Klassifizierung nicht allein über Produktnamen
- unklare Clients bleiben unklar
- Serverhistorie und Home-Assistant-Player-Aktion strikt trennen
- `playing` und `paused` schützen
- exakte Hidden-Rule vor einer Registry-Aktion speichern
- Erfolg erst nach Reload- und Zustandsprüfung melden
- keine zusätzlichen Cleanup-Anmeldedaten
- keine direkten `.storage`-Änderungen
- Schedulertermine absolut und persistent
- manuell und automatisch teilen einen Lock
- bei unklarem Zustand fail-safe abbrechen

## Testanforderungen

Änderungen an Runtime-, Options- oder Maintenance-Code benötigen passende Nachweise für:

- Identitäts- und Registry-Erhalt
- Benutzer-, Shared-, Unassigned-, Technical- und Unknown-Gruppierung
- disabled-valid versus orphaned
- Draft, Review, Apply, Discard, Back und X
- exakt einen Optionswrite und höchstens einen Reload
- exakte Werte `364` und `365`
- Erhalt der Automatikstellung und des Schedulerzustands
- Wiedergabeschutz für `playing` und `paused`
- Hidden-Rule-, Reload- und Wiederkehrprüfung
- Restore-Verifikation
- Serverhistorien- und HA-Player-Trennung
- Persistenz und Storage-Fehler
- Scheduler, Catch-up, Reload und Neustart
- Lock und doppelte Callbacks
- Teilerfolg und kein Batchlimit
- Logging, Diagnostics und Datenschutz
- Stable-, HACS- und Paketvertrag

Jede Blocker-ID aus `requirements.yaml` muss in der Akzeptanzmatrix eine Implementierungs- und Testreferenz besitzen.

## Übersetzungen

`strings.json` ist die englische Quelle und muss inhaltlich mit `translations/en.json` übereinstimmen. Deutsch und Englisch müssen dieselbe rekursive Schlüsselstruktur besitzen. Private IDs oder Live-Systemwerte gehören nie in Übersetzungen oder Dokumentation.

## Paketvertrag

`scripts/build_package.py` ist der gemeinsame Builder für Quality, Test package und Release. Das Installations-ZIP enthält ausschließlich Dateien aus `custom_components/emby` direkt im ZIP-Root.

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

## Scope Freeze 0.9.0

Nicht in 0.9.0 ergänzen:

- Bibliotheks- oder Statistik-Sensoren
- zusätzliche Plattformen
- Premium-Code
- öffentliche Beta-, Dev- oder RC-Versionen
- Funktionen, die ausdrücklich für 1.0.0 reserviert sind

Alle Implementierungs- und Abnahmefixes bleiben bis zur privaten Live-Abnahme auf `feature/embi-0.9.0` und in PR #29.
