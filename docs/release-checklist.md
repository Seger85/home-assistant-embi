# Release-Checkliste 0.9.1

## Unveränderliche Basis

- [x] Manifest und Runtime tragen `0.9.1`.
- [x] Config-Entry- und Unique-ID-Vertrag bleiben kompatibel.
- [x] Der bestehende Stable-Tag `v0.9.0` bleibt unverändert.
- [x] Es gibt keine Dev-, Beta- oder RC-Veröffentlichung.
- [x] HACS verwendet `zip_release: true`, `filename: embi.zip` und `hide_default_branch: true`.

## UX und Sicherheit

- [x] Hauptmenü: Home-Assistant-Player und Emby-Server bereinigen.
- [x] Änderungen prüfen erscheint nur bei offenem Entwurf.
- [x] Zurück erhält den Entwurf; X und Verwerfen schreiben nichts.
- [x] Unverändertes Apply schreibt und lädt nicht neu.
- [x] Geändertes Apply schreibt einmal und lädt höchstens einmal neu.
- [x] Fehler bleiben inline auf der aktiven Seite.
- [x] Kurze Playerlabels enthalten keine internen IDs oder Rohstatus.
- [x] Benutzergruppen, Shared, Unassigned, Technical und Unknown sind getrennt.
- [x] Disabled-valid, Server-missing und echte HA-Orphans sind getrennt.
- [x] Playing, paused und unklare Wiedergabezustände sind geschützt.
- [x] Serverhistorie, HA-Removal und Restore bleiben getrennte Aktionen.

## Migration

- [x] 0.9.0 nach 0.9.1 ist idempotent.
- [x] Entity-IDs, Unique IDs, Namen, Aliase, Areas, Labels und disabled state bleiben erhalten.
- [x] Sichtbarkeit, Cleanup-Schalter, Alterswerte, Scheduler und Laufbericht bleiben erhalten.

## CI auf dem finalen PR-Head

- [ ] Quality Python 3.13 und Python 3.14 grün.
- [ ] JSON, YAML, Compileall, Mypy, Ruff und Ruff-Format grün.
- [ ] Vollständiger Pytest-Lauf grün.
- [ ] Specification Contract und Stable Contract grün.
- [ ] Secret-/Privacy-Scan grün.
- [ ] HACS Validation und Hassfest grün.
- [ ] Releasegleicher Paketbau, SHA-256 und `BUILD_COMMIT` grün.

## Merge und Release

- [ ] PR #30 ist auf einem exakten Head vollständig grün und ohne offene Reviewthreads.
- [ ] Squash-Merge nach `main`; finalen Merge-SHA erfassen.
- [ ] Tag exakt `v0.9.1` auf dem finalen Main-Commit.
- [ ] Release-Titel `EMBi 0.9.1`, nicht Draft, nicht Prerelease, als Latest.
- [ ] Assets ausschließlich `embi.zip` und `embi.zip.sha256`.
- [ ] Veröffentlichte Assets erneut laden, SHA-256, ZIP-Struktur und Manifest `0.9.1` prüfen.
- [ ] HACS erkennt `v0.9.1` als Stable und installiert das Releaseasset.

Die visuelle Home-Assistant-Prüfung auf iPhone, iPad und Desktop erfolgt nachgelagert und blockiert den GitHub-Release nicht.
