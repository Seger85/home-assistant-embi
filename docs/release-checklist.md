# Release-Checkliste 0.9.0

## Code und Metadaten

- [x] `const.py` und `manifest.json` tragen `0.9.0`
- [x] Config-Entry-Schema 4.0 und Optionsschema 2
- [x] Plattform ausschließlich `media_player`
- [x] bestehende Unique-ID-Logik unverändert
- [x] `strings.json` und `translations/en.json` identisch
- [x] deutsche Übersetzung strukturell synchron
- [x] `hacs.json`: `zip_release: true`, `filename: embi.zip`
- [x] keine zusätzlichen Cleanup-Anmeldedaten
- [x] keine direkte `.storage`-Bearbeitung
- [x] Serverhistorie und HA-Player-Entfernung getrennt
- [x] keine öffentliche Vorabversion angelegt
- [x] bestehende Tags und Releases unverändert

## Automatische Tests auf dem finalen Feature-Commit

- [ ] Quality Python 3.13 grün
- [ ] Quality Python 3.14 grün
- [ ] JSON und YAML grün
- [ ] Compileall grün
- [ ] Ruff und Ruff-Format grün
- [ ] vollständiger Pytest-Lauf grün
- [ ] Specification Contract grün
- [ ] Stable Contract grün
- [ ] Secret-/Privacy-Scan grün
- [ ] Übersetzungssynchronität grün
- [ ] HACS Validation grün
- [ ] Hassfest grün
- [ ] privater releasegleicher Paketbau grün
- [ ] SHA-256 grün
- [ ] `BUILD_COMMIT` entspricht dem finalen Feature-Commit

## Frozen-Contract-Nachweise

- [x] bekannte Benutzer, Shared, Unassigned, Technical und Unknown modelliert
- [x] technische Klassifizierung nicht nur anhand eines Produktnamens
- [x] disabled-valid Entity ist kein Orphan
- [x] `playing` und `paused` bei Sichtbarkeit und Removal geschützt
- [x] exakte Hidden-Rule vor Registry-Entfernung gespeichert
- [x] Removal-Erfolg erst nach Reload- und Registry-/State-Verifikation
- [x] Restore nach Reload anhand exakter Ownership verifiziert
- [x] exakte Werte `364` und `365` migrationsstabil
- [x] Automatikstellung und Schedulerzustand migrationsstabil
- [x] normale Änderungen als Draft mit semantischem Review
- [x] Apply schreibt Optionen einmal und lädt höchstens einmal neu
- [x] Discard und X ohne Write oder Reload
- [x] Diagnostics redigieren API-Schlüssel und Serververbindungsdaten
- [x] jede Requirement-ID in der Akzeptanzmatrix nachvollziehbar

## Finales privates Artefakt

- [ ] exakten finalen Feature-Commit erfassen
- [ ] `Test package` auf exakt diesem Commit erfolgreich
- [ ] Artefaktname `embi-test-<vollständiger SHA>`
- [ ] Artefakt-ID erfassen
- [ ] Actions-Artefakt herunterladen und öffnen
- [ ] äußere Dateien: `embi.zip`, `embi.zip.sha256`, `BUILD_COMMIT`
- [ ] inneres Installations-ZIP öffnet erfolgreich
- [ ] Manifestversion exakt `0.9.0`
- [ ] erwartete Home-Assistant-/HACS-Struktur direkt im ZIP-Root
- [ ] keine Tests, Docs, `.github`, Caches oder Repositorymetadaten im Installations-ZIP
- [ ] SHA-256 des exakten `embi.zip` geprüft und dokumentiert
- [ ] `BUILD_COMMIT` entspricht dem vollständigen finalen Feature-SHA
- [ ] PR #29 mit finaler Evidenz aktualisiert
- [ ] PR #29 bleibt Draft, offen und ungemergt

## Private Home-Assistant-Abnahme

Verifizierte Ausgangsbasis:

- EMBi `0.3.0`
- Config Entry geladen
- 69 Emby-Server-Historieneinträge
- 30 aktivierte und geladene EMBi-Media-Player
- kein Registry-Orphan
- automatische Bereinigung deaktiviert
- manuelle und automatische Schwelle jeweils 365 Tage

Abnahmepunkte:

- [ ] vollständiges Home-Assistant-Backup
- [ ] belastbarer Emby-Wiederherstellungsweg
- [ ] finales privates Testpaket installiert
- [ ] Manifest und Runtime melden `0.9.0`
- [ ] Config Entry bleibt geladen
- [ ] 69 Historieneinträge und 30 Media-Player, sofern keine reale Clientänderung unmittelbar vor dem Test dokumentiert wurde
- [ ] Entity-IDs und Unique IDs unverändert
- [ ] individuelle Namen, Aliase, Areas, Labels und disabled state unverändert
- [ ] Benutzer-, Shared-, Unassigned-, Technical- und Unknown-Gruppen korrekt
- [ ] keine internen IDs als primäre UI-Labels
- [ ] Automatik weiterhin aus; Schwellen weiterhin 365/365
- [ ] Apply, unveränderter Apply, Discard, Back und X geprüft
- [ ] semantisches Review geprüft
- [ ] iPhone-, iPad- und Desktop-QA
- [ ] `playing` und `paused` als geschützt nachgewiesen
- [ ] einen sicher idle Player separat aus Home Assistant entfernt
- [ ] exakte Hidden-Rule vor Removal nachgewiesen
- [ ] Player kehrt nach zusätzlichem Reload nicht zurück
- [ ] Emby-Serverhistorie bei HA-Player-Removal unverändert
- [ ] denselben Player wiederhergestellt und resultierende Entity verifiziert
- [ ] Serverhistorien-Aktion separat und mit eigener finaler Bestätigung geprüft
- [ ] Scheduler, `next_run_at`, Reload und Neustart geprüft
- [ ] keine neuen Repairs, Orphans oder Laufzeitfehler
- [ ] Rollback auf `v0.3.0` oder vollständige Backup-Wiederherstellung demonstriert

## Veröffentlichungssperre

Bis zur dokumentierten privaten Abnahme:

- [ ] PR #29 nicht nach `develop` mergen
- [ ] `develop` nicht nach `main` promoten
- [ ] keinen Tag `v0.9.0` erstellen
- [ ] keinen Draft-, Pre- oder Stable-Release erstellen
- [ ] keine öffentliche HACS-Version 0.9.0 veröffentlichen
