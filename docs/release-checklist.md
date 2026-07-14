# Release-Checkliste

## Code und Metadaten

- [ ] `const.py` und `manifest.json` tragen dieselbe Version
- [ ] Manifest verweist auf Repository und Codeowner
- [ ] `strings.json` und `translations/en.json` sind identisch
- [ ] deutsche Übersetzung vollständig
- [ ] Changelog, Roadmap und Projektstatus aktualisiert
- [ ] keine Secrets oder privaten Diagnosedaten im Diff
- [ ] rc2-Tag wurde nicht verschoben oder ersetzt

## Automatische Tests

- [ ] Python-Kompilierung erfolgreich
- [ ] Ruff-Lint und Format erfolgreich
- [ ] JSON- und YAML-Validierung erfolgreich
- [ ] Unit-Tests erfolgreich
- [ ] HACS-Validierung erfolgreich
- [ ] Hassfest erfolgreich
- [ ] Test: 250+ Löschungen ohne Laufbegrenzung
- [ ] Test: Standard-Altersfilter 365 Tage
- [ ] Test: aktive Player übersprungen
- [ ] Test: ungültige Zeitstempel übersprungen
- [ ] Test: doppelter Player-Key verhindert vorzeitige Registry-Entfernung
- [ ] Test: Registry-Key erst nach letztem Serverdatensatz zulässig

## Testinstallation

- [ ] Home-Assistant-Backup erstellt
- [ ] Emby-Backup beziehungsweise belastbarer Wiederherstellungsweg vorhanden
- [ ] Installation über HACS-Prerelease
- [ ] Config Entry lädt
- [ ] erwartete Entity-IDs und Unique IDs unverändert
- [ ] aktive Wiedergabe korrekt
- [ ] Neustart ohne EMBi-Fehler
- [ ] keine Repairs

## Manuelle Bereinigung

- [ ] Master-Schalter standardmäßig aus
- [ ] Standard-Altersfilter 365 Tage
- [ ] aktive Player nicht auswählbar
- [ ] unbekannte Zeitstempel nicht auswählbar
- [ ] Auswahl unmittelbar vor Löschung revalidiert
- [ ] Teilerfolg korrekt
- [ ] HA-Registry-Entfernung nur nach letzter gleicher Player-Identität

## Automatische Bereinigung

- [ ] separater Schalter standardmäßig aus
- [ ] erstmalige Aktivierung benötigt Warnschalter und exakten Text
- [ ] erster Lauf nach 120 Sekunden
- [ ] Folgeintervall 24 Stunden
- [ ] keine maximale Löschzahl
- [ ] paralleler Lauf blockiert
- [ ] aggregierte Diagnose ohne IDs
- [ ] Master aus deaktiviert Automatik
- [ ] keine automatische geräteweite Ignorierung

## Visuelle QA

- [ ] iPhone
- [ ] iPad
- [ ] Desktop
- [ ] produktives Seger-Theme
- [ ] lange Labels
- [ ] Warnung „keine maximale Löschzahl“
- [ ] leere Passwortfelder
- [ ] Bestätigungsdialoge

## Rollback

- [ ] vorheriges Prerelease installierbar
- [ ] Backup-ID dokumentiert
- [ ] Emby-Backup geprüft
- [ ] Config-Entry- und Entity-Baseline dokumentiert
- [ ] Rollback-Anleitung aktuell
