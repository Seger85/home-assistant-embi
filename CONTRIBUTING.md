# Mitwirken an EMBi

## Grundsätze

- bestehende Entity-IDs und Unique IDs dürfen ohne zwingenden Migrationsgrund nicht verändert werden
- destruktive Funktionen benötigen explizite Auswahl, Bestätigung und nachvollziehbare Ergebnisbehandlung
- keine direkten Änderungen an Home Assistants `.storage`-Dateien
- native Config-/Options-Flows und Selektoren vor eigenen Frontend-Hacks
- Zugangsdaten niemals in Issues, Tests, Fixtures, Logs oder Commits aufnehmen
- Deutsch und Englisch bei jeder UI-Änderung gemeinsam pflegen

## Entwicklungsablauf

1. Feature- oder Fix-Branch von `develop` erstellen.
2. Änderung klein und nachvollziehbar halten.
3. Tests ergänzen oder anpassen.
4. `ruff check`, `ruff format --check`, `compileall` und `pytest` ausführen.
5. Manifest- und Übersetzungs-JSON validieren.
6. Pull Request mit Risiko-, Migrations- und Testbeschreibung erstellen.

## Commit-Konvention

Empfohlene Präfixe:

- `feat:` neue Funktion
- `fix:` Fehlerkorrektur
- `docs:` Dokumentation
- `test:` Tests
- `refactor:` interne Struktur ohne beabsichtigte Funktionsänderung
- `chore:` Wartung, CI oder Repository-Struktur

## Pull-Request-Prüfpunkte

- [ ] keine Secrets enthalten
- [ ] bestehende Entity-IDs bleiben erhalten
- [ ] Deutsch und Englisch vollständig
- [ ] Diagnostics redigieren neue sensible Felder
- [ ] destruktive Pfade besitzen Bestätigung und Teilerfolgsauswertung
- [ ] technische Tests erfolgreich
- [ ] visuelle Prüfung dokumentiert oder als noch offen gekennzeichnet
