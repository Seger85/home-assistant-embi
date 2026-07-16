# Bereinigung

## Getrennte Aufgaben in einem Bereich

EMBi 0.9.0 zeigt zwei unterschiedliche Wartungsaufgaben gemeinsam an, hält ihre Daten und Sicherheitsentscheidungen jedoch strikt getrennt:

- **Emby-Server-Gerätehistorie:** historische Datensätze auf dem Emby-Server
- **Home-Assistant-Player:** EMBi-Entities in Home Assistant

Eine Aktion an einem Home-Assistant-Player verändert keine Serverhistorie. Eine Serverhistorien-Aktion verändert nicht automatisch die normale Player-Sichtbarkeit.

## Übersicht

Der Bereich zeigt getrennt:

- Serverhistorien-Datensätze
- Home-Assistant-Player
- zusätzliche historische Datensätze
- aktuell bearbeitbare Player
- durch Wiedergabe geschützte Player
- letzten Lauf, Ergebnis und nächsten Termin

## Alterswerte

Manuelle und automatische Alterswerte sind getrennt. Verfügbar sind 7, 30, 90, 180 und 365 Tage sowie ein benutzerdefinierter Wert.

Der numerische Wert bleibt die Quelle der Wahrheit. Ein vorhandener Wert `364` bleibt `364`; `365` bleibt `365`.

## Schutzregeln

Serverrecords und Home-Assistant-Player bleiben geschützt, wenn:

- der Player `playing` ist
- der Player `paused` ist
- der Wiedergabestatus nicht sicher bestimmt werden kann
- ein Aktivitätszeitpunkt fehlt oder ungültig ist
- die exakte Zugehörigkeit zu Config Entry, Domain, Plattform oder Unique ID nicht bestätigt werden kann

Zeitgrenzen gelten strikt als „älter als“. Exakt am Cutoff bleibt ein Datensatz geschützt.

## Manuelle Serverprüfung

EMBi liest die Serverdaten frisch, trennt sichere Kandidaten von geschützten Records und zeigt nur zulässige Kandidaten zur Auswahl. Gibt es keine Kandidaten, erscheint kein leerer Mehrfachselektor und es wird nichts verändert.

Eine bestätigte Serveraktion betrifft keine Emby-Benutzer, Medien, Bibliotheken oder Wiedergabeverläufe. Pro destruktiver Aktion gibt es genau eine abschließende Bestätigung.

## Automatische Serverbereinigung

- bei Neuinstallationen standardmäßig aus
- bestehende Stellung bleibt bei Migration erhalten
- persistentes absolutes `next_run_at`
- 120-Sekunden-Catch-up bei Erstaktivierung, überfälligem Termin oder Migration ohne Termin
- danach 24 Stunden nach Abschluss des vorherigen Versuchs
- gültiger Zukunftstermin bleibt bei Reload und Neustart unverändert
- gemeinsamer Lock mit manuellen Wartungsaktionen
- Store- oder Runtime-Unklarheit führt fail-safe zum Abbruch

## Registry-Ergebnisse nach Serverwartung

- `queued`: Identität wurde zur Prüfung vorgemerkt
- `matched`: exakte Registry-Entity wurde gefunden
- `removed`: Registry-Operation wurde tatsächlich ausgeführt
- `missing`: keine passende Entity war vorhanden
- `protected`: Änderung wurde bewusst blockiert

`queued` ist niemals gleichbedeutend mit `removed`.

## Home-Assistant-Player verwalten

Nicht spielende EMBi-Player können unabhängig von der Serverhistorie in EMBi verborgen und anschließend kontrolliert aus Home Assistant entfernt werden.

Vor einer Registry-Änderung werden aktuelle Emby-Daten, Home-Assistant-States und Registry-Metadaten erneut geprüft. Die exakte Hidden-Regel wird zuerst gespeichert. Danach werden Reload und Ergebnisprüfung durchgeführt, damit ein Player nicht unbeabsichtigt zurückkehrt.

Ein zuvor verborgener oder entfernter Player kann über **Geräte & Player** wiederhergestellt werden. EMBi lädt die Integration neu und prüft die resultierende Entity.

Eine deaktivierte, weiterhin gültige Entity ist kein Orphan. Beim Aktivieren bleiben Identität und Metadaten erhalten.

## Referenzfall 74 → 69

- 74 Serverdatensätze vor dem Test
- fünf Kandidaten bei bewusst gewählten 364 Tagen
- fünf erfolgreiche Serveraktionen
- null Serverfehler
- 69 verbleibende Datensätze
- fünf Registry-Keys queued
- null Matches
- null Registry-Entfernungen
- fünf missing

Der Fall belegt Serverbereinigung und fehlende passende Registry-Entities, nicht fünf entfernte Home-Assistant-Player.

## Backup und Rollback

Vor einer Live-Abnahme:

- vollständiges Home-Assistant-Backup
- Emby-Wiederherstellungsweg
- Entity-IDs, Unique IDs, Namen, Aliase, Areas, Labels und disabled state dokumentieren

Primärer Rollbackweg ist die erneute Installation von `v0.3.0` oder die Wiederherstellung des vollständigen Backups. Direkte Änderungen an `.storage`-Dateien sind nicht zulässig.
