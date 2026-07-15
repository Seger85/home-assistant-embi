# EMBi Roadmap

## 0.3.0 – Stable

Status: Implementierung und Repositoryvertrag abgeschlossen; öffentliche Veröffentlichung gesperrt, bis die Live-Gates erfüllt und der Draft-Promotion-PR ausdrücklich freigegeben ist.

Enthalten:

- persistenter Maintenance-Store und persistenter Laufbericht
- absoluter Scheduler mit 120-Sekunden-Catch-up und 24 Stunden nach Abschluss
- gemeinsamer Lock und Wiederholschutz
- getrennte Registry-Zähler queued, matched, removed, missing und protected
- fail-safe Verhalten bei Store-, API- und Revalidierungsfehlern
- Options-Flow-Entwurf mit Apply und Discard
- höchstens ein Reload nach Apply
- ein normaler EMBi-Verbindungsschlüssel, kein zweites Cleanup-Feld
- keine Aktivierungsphrase
- manuelle und automatische Alterswerte mit Presets und Custom
- getrennte App- und Geräte-Ignorierregeln
- sichtbare unresolved Altwerte
- keine automatische Ignore-Regel nach Serverbereinigung
- HA-Mitbereinigung für neue Aktivierungen standardmäßig aus
- Diagnostics-Redaktion
- keine Wartungsentity
- HACS-ZIP-Vertrag `embi.zip`

Live-Gates:

- vollständiges Home-Assistant- und Emby-Backup
- Upgradepfad `v0.3.0-rc3` → unveröffentlichtes `0.3.0`-Testpaket
- 29 Media-Player, Entity-IDs, Unique IDs und individuelle Namen unverändert
- migrierter Wert 364 bleibt zunächst Custom
- bewusste spätere Auswahl von 365 prüfen
- Catch-up, `next_run_at`, Reload und Neustart prüfen
- Apply, unveränderter Apply, Discard und Schließen über X prüfen
- tatsächliche sichere Registry-Nachbereitung verifizieren
- iPhone-, iPad- und Desktop-QA
- Rollback auf `v0.3.0-rc3`
- keine neuen Repairs, Fehler oder unbeabsichtigten Änderungen

## Nach 0.3.0

Die folgenden Themen bleiben ausdrücklich außerhalb des Stable-Scope und werden erst nach der Veröffentlichung neu priorisiert:

- Report-only-Modus
- Bibliothekssensoren
- zuletzt hinzugefügte Medien
- Benutzerstatistiken
- Wiedergabezeitstatistiken
- neue Plattformen
- Premium-Code
- weitere Produktvisionen

## 0.4.x – Wartung und Testvertiefung

- vollständige Home-Assistant-Testumgebung für Config Flow und Options Flow
- breitere Runtime-Kompatibilitätsmatrix
- weitere Fehler- und Recovery-Szenarien
- strukturierte, identitätsfreie Audit-Historie nur nach neuer Scope-Freigabe

## 1.0.0 – Langfristige Veröffentlichungsreife

- externe Beta-Tests
- dokumentierte Kompatibilitätsmatrix
- Datenschutz- und Sicherheitsreview
- stabiler Migrationspfad über mehrere Vorversionen
- klare Abgrenzung zum minimalen Home-Assistant-Core-Vorschlag
