# Entwicklung

## Branches

- `main`: freigegebene Versionen
- `develop`: integrierter Entwicklungsstand
- `feature/*`: einzelne Funktionen
- `fix/*`: Fehlerkorrekturen

## Lokale Qualitätsprüfung

```bash
python -m compileall -q custom_components/emby
python -m json.tool custom_components/emby/manifest.json >/dev/null
python -m json.tool custom_components/emby/strings.json >/dev/null
python -m json.tool custom_components/emby/translations/de.json >/dev/null
python -m json.tool custom_components/emby/translations/en.json >/dev/null
ruff check .
ruff format --check .
pytest -q
```

Die reinen Unit-Tests laden `api.py`, `const.py` und `helpers.py` ohne vollständige Home-Assistant-Testumgebung. Config-Flow- und Plattformtests gehören langfristig zusätzlich in eine vollständige Home-Assistant-Pytest-Umgebung.

## Releaseprozess

1. Versionsnummer in `const.py` und `manifest.json` angleichen.
2. Übersetzungsplatzhalter prüfen.
3. Changelog aktualisieren.
4. CI vollständig grün.
5. Testinstallation auf nicht-produktivem Home Assistant.
6. technische Prüfung und visuelle QA.
7. Pull Request nach `main`.
8. Tag `vX.Y.Z`.
9. HACS-Update auf einer zweiten Instanz testen.
10. erst danach produktive Installation aktualisieren.

## Tests für destruktive Pfade

Mindestens abzudecken:

- keine Auswahl
- Bestätigungsschalter aus
- falscher Bestätigungstext
- ein erfolgreicher Eintrag
- ein fehlgeschlagener Eintrag
- gemischter Teilerfolg
- Ignorierliste nur um erfolgreiche Client-IDs erweitern
- API-Key in Diagnostics redigiert
