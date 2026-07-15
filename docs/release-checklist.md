# Release-Checkliste 0.3.0

## Code und Metadaten

- [x] `const.py` und `manifest.json` tragen `0.3.0`
- [x] Plattform ausschließlich `media_player`
- [x] bestehende Unique-ID-Logik unverändert
- [x] `strings.json` und `translations/en.json` identisch
- [x] deutsche Übersetzung strukturell synchron
- [x] `hacs.json`: `zip_release: true`, `filename: embi.zip`
- [x] keine zusätzlichen Cleanup-Anmeldedaten
- [x] keine Aktivierungsphrase
- [x] keine automatische Ignore-Regel nach Serverbereinigung
- [x] keine Wartungsentity
- [x] Dokumentation auf Stable-Vertrag aktualisiert
- [x] bestehende Tags und Releases unverändert

## Automatische Tests

- [ ] Quality Python 3.13 auf finalem PR-Head grün
- [ ] Quality Python 3.14 auf finalem PR-Head grün
- [ ] JSON und YAML grün
- [ ] Compileall grün
- [ ] Ruff und Ruff-Format grün
- [ ] vollständiger Pytest-Lauf grün
- [ ] Stable-Vertrag grün
- [ ] Secret-/Privacy-Scan grün
- [ ] Übersetzungssynchronität grün
- [ ] HACS Validation grün
- [ ] Hassfest grün
- [ ] releasegleicher Paketbau grün
- [ ] SHA-256 grün
- [ ] `BUILD_COMMIT` grün

## Persistenz und Scheduler

- [x] leerer Store, Load, Save und Schema getestet
- [x] beschädigter, fehlender und nicht lesbarer Store fail-safe getestet
- [x] Write-Fehler vor und nach der Serverphase getestet
- [x] keine privaten Identitäten im Store getestet
- [x] Erstaktivierung nach 120 Sekunden getestet
- [x] Deaktivierung in Grace Period getestet
- [x] Zukunftstermin über Reload/Neustart erhalten
- [x] überfälliger Termin erhält einmaligen Catch-up
- [x] 24 Stunden nach Abschluss getestet
- [x] Lock und doppelter Callback geschützt

## Cleanup und Registry

- [x] 74 → 69 mit fünf Erfolgen und null Serverfehlern getestet
- [x] aktive und undatierte Datensätze geschützt
- [x] Einzelfehler stoppt restlichen Lauf nicht
- [x] kein Batchlimit
- [x] keine automatische Ignorierung
- [x] queued, matched, removed, missing und protected getrennt
- [x] wrong entry, platform, unique ID und State geschützt
- [x] kein Präfix-, Wildcard- oder Teilstring-Match
- [x] Neustart bei `registry_pending` führt nicht zu Removal

## Options Flow und Migration

- [x] Draft und Discard als Pure Unit getestet
- [x] Apply-/Dirty-/Reload-Vertrag im Repositoryvertrag geprüft
- [x] Presets 7, 30, 90, 180 und 365 getestet
- [x] Custom 364 und weitere Custom-Werte getestet
- [x] keine 364-zu-365-Migration
- [x] getrennte App- und Geräte-Ignorierregeln getestet
- [x] unresolved Altwerte bleiben erhalten
- [x] rc3-Werte und HA-Mitbereinigung bleiben erhalten
- [x] obsolete rc3-Felder werden entfernt

## Merge und Artefakt

- [ ] PR #18 aus Draft nehmen
- [ ] PR #18 per Squash nach `develop` mergen
- [ ] exakten Squash-Merge-Commit erfassen
- [ ] CI auf Develop-Merge-Commit grün
- [ ] `Test package` auf exaktem Develop-Merge-Commit erfolgreich
- [ ] Artefakt-ID und Name erfassen
- [ ] ZIP herunterladen und entpacken
- [ ] Manifest und interne Version `0.3.0`
- [ ] deutsche und englische Übersetzung vorhanden
- [ ] keine Tests, Docs oder `.github` im Installations-ZIP
- [ ] SHA-256 geprüft
- [ ] `BUILD_COMMIT` entspricht Develop-Merge-Commit
- [ ] Draft-Promotion-PR `develop` → `main` erstellt und gesperrt

## Live-Abnahme

- [ ] Home-Assistant-Backup
- [ ] Emby-Backup oder belastbarer Wiederherstellungsweg
- [ ] unveröffentlichtes Testpaket installiert
- [ ] Config Entry geladen
- [ ] 29 Media-Player
- [ ] Entity-IDs, Unique IDs und Namen unverändert
- [ ] aktive Wiedergabe und Push-Updates
- [ ] 364 zunächst als Custom erhalten
- [ ] bewusste Auswahl 365 geprüft
- [ ] Catch-up und `next_run_at`
- [ ] Reload und Neustart
- [ ] Apply, unveränderter Apply, Discard und X
- [ ] iPhone, iPad und Desktop
- [ ] tatsächliche sichere Registry-Nachbereitung
- [ ] keine Repairs oder neuen Fehler
- [ ] Rollback auf `v0.3.0-rc3`

## Veröffentlichungssperre

- [ ] Promotion-PR erst nach Gerry-Freigabe mergen
- [ ] erst danach Tag `v0.3.0`
- [ ] erst danach Stable Release und `latest`
- [ ] erst danach öffentliche HACS-Stable-Version
