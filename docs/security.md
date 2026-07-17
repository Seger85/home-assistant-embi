# Sicherheit

## Grundprinzipien

- lokale Kommunikation zum konfigurierten Emby-Server
- offizieller Home-Assistant-Config-Entry
- offizielle Config-, Options-, Entity-Registry- und Storage-APIs
- keine direkten Änderungen an `.storage`
- keine versteckten Wartungsentities
- fail-safe bei unklarem Zustand
- ein gemeinsamer Lock für manuelle und automatische Wartung
- genau eine abschließende Bestätigung je destruktiver Aktion

## Zugangsdaten

EMBi speichert genau den normalen Verbindungsschlüssel im Config Entry. Es gibt kein zweites Cleanup-Feld. Der Wert wird:

- nicht als Passwortfeld-Default an das Frontend zurückgegeben
- in Diagnostics redigiert
- nicht im Laufbericht oder Store gespeichert
- nicht in Logs oder Notifications ausgegeben

## Persistenter Store

Der Maintenance-Store ist:

- privat
- atomar geschrieben
- intern versioniert
- pro Config Entry getrennt
- kompatibel zum bisherigen Home-Assistant-Store-Envelope
- frei von vollständigen Record-IDs, ReportedDeviceIds, Player-Keys, Benutzernamen und Zugangsdaten

Ein erwarteter, aber fehlender oder beschädigter Store stoppt automatische destruktive Läufe. Migrationsergebnisse, Cleanup-Zähler und Player-Aktionsberichte enthalten ausschließlich aggregierte Werte und kategorisierte Fehler.

## Client-Klassifizierung

Technische Zugriffe werden nicht anhand eines Produktnamens allein klassifiziert. Zulässig sind ausschließlich:

- explizite Capability-Daten
- expliziter API-/Service-/Integrationstyp
- ausreichend eindeutiges wiederholtes Nicht-Wiedergabe-Verhalten

Bei unzureichender Evidenz bleibt der Client unter **Unklare Clients**. Unsicherheit führt nicht zu einer versteckten technischen Klassifizierung.

## Sichtbarkeit und Entwurf

- exakte Player-Regeln
- exakte Geräte-Regeln
- Benutzer-Master nur für ausschließlich diesem Benutzer zugeordnete Player
- keine Wildcards, Präfixe oder Teilstrings
- normale Unterseiten schreiben nicht
- Review zeigt semantische Vorher-/Nachher-Angaben
- Apply schreibt Optionen genau einmal
- Discard und Schließen über X schreiben nichts
- laufende und pausierte Player können im Entwurf nicht ausgeblendet werden

Normales Ausblenden ist keine Registry-Entfernung. Die Entity bleibt technisch erhalten, bis eine separate bestätigte Home-Assistant-Player-Aktion ausgeführt wird.

## Serverhistorien-Schutz

- Automatik bei Neuinstallation aus
- bestehende Stellung bei Migration unverändert
- strikt älter als UTC-Cutoff
- exakt am Cutoff geschützt
- fehlende oder ungültige Aktivität geschützt
- `playing` und `paused` geschützt
- frische Revalidierung vor jeder Aktion
- Einzelfehler stoppt nicht automatisch den restlichen Lauf
- kein automatisches Erzeugen einer neuen Hidden-/Ignore-Regel
- keine unsichere Wiederholung nach Prozessabbruch

## Home-Assistant-Player-Schutz

Vor einer Registry-Änderung sind erforderlich:

- frische Emby-Daten
- aktueller Home-Assistant-State
- exakter Config Entry
- Domain `media_player`
- Plattform `emby`
- exakte Unique ID
- sicherer nicht spielender Status
- gespeicherte exakte Hidden-Regel
- kontrollierter Reload
- kein verbleibender Entity-State
- Ergebnisprüfung nach der Aktion

`playing`, `paused` und unklarer Wiedergabestatus sind nicht auswählbar. Eine deaktivierte, weiterhin gültige Entity wird nicht als Orphan behandelt.

Eine Home-Assistant-Player-Aktion verändert keine Emby-Serverhistorie. Eine Serverhistorien-Aktion verändert keine normale Player-Sichtbarkeit.

## TOCTOU und Parallelität

- Ziele werden unmittelbar vor der Aktion erneut gelesen
- ein veralteter Options-Flow-Entwurf darf keine alte Zielentscheidung erzwingen
- Runtime-Wechsel, Unload oder fehlender Store führen zum Abbruch
- manuelle und automatische Wartung laufen nicht parallel
- doppelter Schedulercallback startet keinen zweiten Lauf
- ein unklarer Zwischenzustand führt nicht zu verspäteter Registry-Änderung

## Datenschutz

Diagnostics und Berichte enthalten nur:

- Integrations- und Schemaversion
- aggregierte Serverhistorien- und HA-Player-Zähler
- Gruppen- und Klassifizierungszähler
- Sichtbarkeitszähler
- Schedulerstatus und Zeitpunkte
- Statuscodes und kategorisierte Fehler
- aggregierte Removal-/Restore-Ergebnisse

Private Identitäten werden weder gekürzt noch gehasht persistiert; sie werden vollständig weggelassen.

## Backup und Rollback

Vor der privaten 0.9.0-Live-Abnahme erforderlich:

- vollständiges Home-Assistant-Backup
- belastbarer Emby-Wiederherstellungsweg
- dokumentierter Ausgangsstand der 29 EMBi-Media-Player
- Entity-IDs, Unique IDs, Namen, Aliase, Areas, Labels und disabled state sichern
- stabile Installationsquelle `v0.3.0` verfügbar halten

Primärer Rollbackweg ist die erneute Installation von `v0.3.0` oder die vollständige Backup-Wiederherstellung. Veränderte Emby-Serverhistorie benötigt den separaten Emby-Wiederherstellungsweg.
