# Mitwirken an EMBi

## Grundsätze

- Entity-IDs und Unique-IDs nur mit einem expliziten, getesteten Migrationsgrund ändern.
- Destruktive Pfade benötigen konkrete Auswahl, frische Validierung und Teilergebnisbehandlung.
- Keine direkten Änderungen an Home Assistants `.storage`-Dateien.
- Keine Zugangsdaten oder privaten produktiven IDs in Issues, Tests, Fixtures, Logs oder Commits.
- Deutsch, Englisch und `strings.json` bei jeder UI-Änderung schemaidentisch pflegen.

## Lokaler Ablauf

1. Branch vom aktuellen Zielbranch erstellen.
2. Python einrichten.
3. Vor jeder Abhängigkeitsinstallation ausschließlich `python -I scripts/read_version.py` ausführen; dabei niemals EMBi-, Home-Assistant- oder pyemby-Module importieren.
4. `python -m pip install -r requirements_test.txt`.
5. JSON/YAML, `compileall`, MyPy, Ruff, vollständiges Pytest, Spec Contract, Stable Contract, Repository-Referenzen und Secret Scan ausführen.
6. Mit `scripts/build_package.py` das deterministische releasegleiche ZIP erzeugen und die SHA-256 prüfen.
7. Im PR Risiko, Migration, Tests und Repositorybereinigung dokumentieren.

## Pull-Request-Prüfpunkte

- [ ] Python 3.13 und 3.14 grün
- [ ] HACS Validation und Hassfest grün
- [ ] Übersetzungsparität und echte Options-Flow-Serialisierung geprüft
- [ ] Entity Platform, State Machine, Registry und Wiederherstellung getestet
- [ ] Diagnostics bleiben privacy-safe
- [ ] gelöschte, zusammengeführte, aktualisierte und bewusst unveränderte Dateien dokumentiert
- [ ] visuelle Prüfung auf iPhone und Desktop dokumentiert oder als produktiver Restpunkt benannt
