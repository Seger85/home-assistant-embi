# Serverbereinigung

## Zweck und Grenzen

EMBi 0.3.0 verwaltet historische Geräte-Einträge des lokalen Emby-Servers. Medien, Bibliotheken, Benutzer und Wiedergabedaten sind nicht Bestandteil dieser Funktion.

## Stable-Konfiguration

- ein normaler EMBi-Verbindungsschlüssel
- kein zusätzliches Cleanup-Zugangsfeld
- getrennte manuelle und automatische Alterswerte
- Presets 7, 30, 90, 180 und 365 Tage plus Custom
- bestehende 364 Tage bleiben Custom
- neue HA-Mitbereinigung standardmäßig aus; Bestandswerte bleiben erhalten
- keine automatische Ignore-Regel nach einer Serveraktion

## Sicherheitsprüfung

Nur Einträge mit gültigem Aktivitätszeitpunkt, strikt älter als der UTC-Cutoff und ohne aktive Wiedergabe sind zulässig. Jeder Eintrag wird unmittelbar vor der Verarbeitung erneut geprüft. Einzelfehler stoppen den restlichen Lauf nicht; ein Batchlimit existiert nicht.

## Automatik

Neue Aktivierungen benötigen eine Warnseite mit Pflichtschalter, aber keinen einzutippenden Satz. Vor Apply startet kein Lauf. Ein fehlender oder überfälliger Termin erhält genau einen 120-Sekunden-Catch-up. Gültige Zukunftstermine bleiben bei Reload und Neustart bestehen. Der nächste Termin liegt 24 Stunden nach Abschluss.

## Persistenz und Lock

Manuelle und automatische Wartung teilen denselben Lock. Der private atomare Store hält `next_run_at` und den aggregierten Laufbericht. Bei einem Store-Fehler wird fail-safe angehalten.

## Registry-Vertrag

Die Nachbereitung verwendet ausschließlich exakte `ReportedDeviceId.AppName`-Identitäten. Domain, Plattform, Config Entry, Unique ID, Entity-State und verbleibende Serverhistorie werden erneut geprüft. Präfix-, Teilstring- und Wildcard-Matches sind ausgeschlossen. Eine verlorene same-process Queue wird nicht nach einem Neustart fortgesetzt.

- `queued`: vorgemerkt
- `matched`: exakte Entity gefunden
- `removed`: Registry-Operation tatsächlich ausgeführt
- `missing`: keine passende Entity vorhanden
- `protected`: bewusst blockiert

Queue und tatsächliche Registry-Operation sind getrennte Ergebnisse.

## Referenzfall 74 → 69

Fünf zulässige Serveroperationen waren erfolgreich, null schlugen fehl und 69 Datensätze blieben bestehen. Fünf Registry-Keys waren queued; null waren matched oder removed, fünf waren missing.

## Live-Test

Vor dem Test sind ein Home-Assistant-Backup und ein Emby-Wiederherstellungsweg Pflicht. Der Integrations-Rollback führt zu `v0.3.0-rc3`.
