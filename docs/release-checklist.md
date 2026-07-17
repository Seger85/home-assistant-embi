# Release-Checkliste 0.9.1

## Code und Metadaten

- [x] `const.py` und `manifest.json` tragen `0.9.1`
- [x] Config-Entry-Schema und Optionsschema bleiben migrationskompatibel
- [x] Plattform ausschließlich `media_player`
- [x] bestehende Unique-ID-Logik unverändert
- [x] `strings.json` und `translations/en.json` identisch
- [x] deutsche und englische Schlüssel sowie Platzhalter synchron
- [x] `hacs.json`: `zip_release: true`, `filename: embi.zip`, `hide_default_branch: true`
- [x] keine direkte `.storage`-Bearbeitung
- [x] Emby-Serverhistorie und HA-Player-Verwaltung getrennt
- [x] keine Dev-, Beta- oder RC-Version vorgesehen

## Options-Flow-UX

- [x] Hauptmenü **Home-Assistant-Player** und **Emby-Server bereinigen**
- [x] **Änderungen prüfen** nur bei offenem Entwurf
- [x] native Zurück-Navigation auf allen Unterseiten
- [x] Zurück erhält den vollständigen Entwurf
- [x] X und Verwerfen ohne Optionswrite oder Reload
- [x] unverändertes Apply ohne Optionswrite oder Reload
- [x] geändertes Apply schreibt genau einmal und lädt höchstens einmal neu
- [x] normale Fehler bleiben inline auf der aktiven Seite
- [x] kurze Playerlabels ohne Entity-ID, Unique ID oder Rohstatus
- [x] technische Angaben ausschließlich in Detailansichten
- [x] Benutzer-Master-Schalter und Ausnahmen getrennt
- [x] Suche und Pagination für lange Listen

## Klassifizierung und Sicherheit

- [x] Benutzer-, Shared-, Unassigned-, Technical- und Unknown-Gruppen
- [x] technische Klassifizierung nicht allein anhand eines Produktnamens
- [x] Registry-backed Player mit aktuellem Serverdatensatz als Playback-Kandidat
- [x] disabled-valid Entity ist kein Orphan
- [x] Server-missing und echter Home-Assistant-Orphan getrennt
- [x] `playing`, `paused` und unklarer Wiedergabestatus geschützt
- [x] exakte Hidden-Regel vor Registry-Änderung gespeichert
- [x] Erfolg erst nach Reload- und Wiederkehrprüfung
- [x] Restore nach Reload anhand exakter Ownership verifiziert
- [x] keine automatische Sichtbarkeitsänderung durch neue Klassifizierung

## Migration

- [x] 0.9.0 → 0.9.1 idempotent
- [x] Entity-IDs und Unique IDs unverändert
- [x] Namen, Aliase, Areas, Labels und disabled state erhalten
- [x] effektive Sichtbarkeit erhalten
- [x] automatische Bereinigung bleibt ein oder aus wie zuvor
- [x] exakte Alterswerte wie `364` und `365` bleiben erhalten
- [x] Scheduler- und Laufstatus bleiben erhalten

## CI auf dem finalen PR-Head

- [ ] Quality Python 3.13 grün
- [ ] Quality Python 3.14 grün
- [ ] JSON und YAML grün
- [ ] Compileall grün
- [ ] Mypy grün
- [ ] Ruff und Ruff-Format grün
- [ ] vollständiger Pytest-Lauf grün
- [ ] Specification Contract grün
- [ ] Stable Contract grün
- [ ] Secret-/Privacy-Scan grün
- [ ] HACS Validation grün
- [ ] Hassfest grün
- [ ] releasegleicher Paketbau grün
- [ ] SHA-256 grün
- [ ] `BUILD_COMMIT` entspricht dem finalen PR-Head

## PR und Merge

- [ ] PR #30 enthält ausschließlich den freigegebenen 0.9.1-Umfang
- [ ] keine offenen Reviewthreads
- [ ] alle Pflichtchecks auf demselben Head grün
- [ ] Squash-Merge nach `main`
- [ ] finalen Main-Merge-SHA erfassen

## Stable Release

- [ ] Tag exakt `v0.9.1`
- [ ] Tagziel entspricht dem finalen Main-Merge-SHA
- [ ] Release-Titel `EMBi 0.9.1`
- [ ] Release ist nicht Draft
- [ ] Release ist nicht Prerelease
- [ ] Release ist `latest`
- [ ] Assets ausschließlich `embi.zip` und `embi.zip.sha256`
- [ ] veröffentlichte Assets erneut herunterladen
- [ ] Prüfsumme gegen das veröffentlichte ZIP verifizieren
- [ ] ZIP öffnet erfolgreich
- [ ] Manifest im ZIP meldet `0.9.1`
- [ ] Installationsdateien liegen direkt im ZIP-Root
- [ ] keine Tests, Docs, `.github`, Caches oder Repositorymetadaten im ZIP
- [ ] Build-Verifikation bindet das Paket an den finalen Main-Commit

## HACS und Home Assistant

- [ ] HACS erkennt `v0.9.1` als reguläre Stable-Version
- [ ] HACS verwendet `embi.zip` statt eines Default-Branch-Commits
- [ ] Installation beziehungsweise Update über HACS
- [ ] Home Assistant neu starten
- [ ] Config Entry, Entity-IDs, Unique IDs und Namen anschließend live prüfen

Die private visuelle Prüfung auf iPhone, iPad und Desktop ist eine nachgelagerte Home-Assistant-Abnahme und kein GitHub-Release-Blocker.
