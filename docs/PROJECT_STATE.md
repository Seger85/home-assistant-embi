# EMBi Project State

## Produktive Ausgangslage

- produktive Vorversion: `v0.3.0-rc3`
- Home Assistant: Core 2026.7.2
- bestehender Config Entry: geladen und beizubehalten
- Stable-Live-Baseline: 29 `media_player`-Entities
- zusätzliche EMBi-Wartungsentity: keine
- Entity-IDs, Unique IDs und individuelle Namen: unverändert zu erhalten
- Legacy YAML: nicht Bestandteil des Stable-Laufzeitpfads
- vorhandene Serverbereinigung und Automatik: bei der Migration zu erhalten
- vorhandene HA-Mitbereinigung: Gerrys Wert `true` ist zu erhalten
- vorhandene Alterswerte: 364 bleibt zunächst ein Custom-Wert

Keine privaten Geräteidentitäten, Zugangsdaten oder internen Config-Entry-IDs werden in diesem Dokument gespeichert.

## Repositoryzustand

- Repository: öffentlich
- `main`: veröffentlichte Linie; Stable-Promotion noch nicht gemergt
- `develop`: Ziel des Implementierungs-PRs und Quelle des finalen Testartefakts
- Implementierungsbranch: `feature/stable-0.3.0`
- Implementierungs-PR: #18
- Zielversion: `0.3.0`
- Stable-Tag und Stable-Release: nicht erstellt
- `v0.3.0-rc3` und alle bestehenden Tags/Releases: unverändert

## Stable-Vertrag

- Config-Entry-Version 3.1
- ausschließlich Plattform `media_player`
- bestehende pyemby-Unique-ID-Logik unverändert
- persistenter privater und atomarer Store
- persistenter identitätsfreier Laufbericht
- absolutes `next_run_at`
- genau ein Catch-up nach 120 Sekunden bei fehlendem, ungültigem oder überfälligem Termin
- gültiger Zukunftstermin bleibt über Reload und Neustart bestehen
- Folgeplanung 24 Stunden nach Abschluss
- gemeinsamer Lock für manuell und automatisch
- keine unsichere Registry-Wiederaufnahme nach Neustart
- Options-Entwurf, Apply und Discard
- keine zusätzlichen Cleanup-Anmeldedaten neben der normalen Verbindung
- keine Aktivierungsphrase
- keine automatische Ignore-Regel nach Serverbereinigung
- HA-Mitbereinigung bei neuen Aktivierungen standardmäßig `false`

## Korrigierter Referenztest

Der produktive rc3-Test reduzierte die Emby-Gerätehistorie von 74 auf 69 Einträge. Fünf Serverbereinigungen waren erfolgreich und keine schlug fehl. Die damalige Queue enthielt fünf Player-Identitäten; da diese nie als HA-Player vorhanden waren, ergaben sich null Matches, null tatsächliche Registry-Entfernungen und fünf missing.

Für 0.3.0 ist dieser Fall als automatisierter Vertragstest festgeschrieben. Queue und tatsächliche Entfernung werden getrennt gezählt.

## Pre-Live-Zustand

Vor der öffentlichen Stable-Veröffentlichung müssen noch erledigt werden:

- unveröffentlichtes Testartefakt auf dem exakten Develop-Merge-Commit prüfen
- Draft-Promotion-PR `develop` → `main` vorbereiten und gesperrt lassen
- Home-Assistant-Backup und Emby-Rollbackweg bestätigen
- Upgrade und Migration live prüfen
- 29 Media-Player und Identitäten prüfen
- 364 zunächst unverändert bestätigen und 365 bewusst auswählen
- Scheduler, Catch-up, Reload und Neustart prüfen
- Options Flow auf iPhone, iPad und Desktop prüfen
- eine tatsächliche sichere Registry-Nachbereitung testen
- Rollback auf `v0.3.0-rc3` prüfen

## Veröffentlichungssperre

Kein Merge nach `main`, kein Tag `v0.3.0`, kein Stable Release, kein `latest`, keine HACS-Stable-Version und kein öffentliches rc4 vor Gerrys ausdrücklicher Live-Abnahme.
