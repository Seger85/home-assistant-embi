# Release-Checkliste

## Code und Metadaten

- [ ] `const.py` und `manifest.json` tragen dieselbe Version
- [ ] Manifest verweist auf das richtige Repository und den richtigen Codeowner
- [ ] `strings.json` und `translations/en.json` sind identisch
- [ ] deutsche Übersetzung vollständig
- [ ] Changelog aktualisiert
- [ ] keine Secrets oder internen Diagnosedaten im Diff

## Automatische Tests

- [ ] Python-Kompilierung erfolgreich
- [ ] Ruff-Lint erfolgreich
- [ ] Ruff-Formatprüfung erfolgreich
- [ ] Unit-Tests erfolgreich
- [ ] JSON-Validierung erfolgreich
- [ ] Hassfest erfolgreich
- [ ] HACS-Validierung erfolgreich

## Testinstallation

- [ ] Backup erstellt
- [ ] Installation über HACS-Custom-Repository
- [ ] Config Entry lädt
- [ ] 28 bzw. erwartete Entity-IDs unverändert
- [ ] aktive Wiedergabe korrekt
- [ ] Unload/Reload korrekt
- [ ] Neustart ohne EMBi-Fehler
- [ ] keine Repairs

## Options Flow

- [ ] alle Geräte anzeigen
- [ ] nur aktive Wiedergaben
- [ ] nur ausgewählte Geräte
- [ ] Ignorierliste hat Vorrang
- [ ] alle auswählen
- [ ] Auswahl leeren
- [ ] alle ignorieren mit Warnung
- [ ] Ignorierliste leeren
- [ ] sichere Registry-Kandidaten
- [ ] Serverbereinigung standardmäßig verborgen
- [ ] separater Cleanup-Key validiert
- [ ] Bestätigungstext lokalisiert
- [ ] Teilerfolg korrekt

## Visuelle QA

- [ ] iPhone
- [ ] iPad
- [ ] Desktop
- [ ] helles und dunkles Standardtheme als Referenz
- [ ] produktives Seger-Theme
- [ ] Mehrfachselektor geöffnet/geschlossen
- [ ] Schalter an/aus
- [ ] Fehlerzustände
- [ ] lange Gerätenamen

## Rollback

- [ ] vorheriges Release installierbar
- [ ] Backup-ID dokumentiert
- [ ] Optionsmigration verändert keine Entity-ID
- [ ] Rollback-Anleitung aktuell
