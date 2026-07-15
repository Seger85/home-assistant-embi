# Sicherheit

## Grundprinzipien

- lokale Kommunikation zum konfigurierten Emby-Server
- offizieller Home-Assistant-Config-Entry und offizieller `Store`
- keine direkten Änderungen an `.storage`
- keine versteckten Wartungsentities
- kritische Wartungsaktionen nur nach expliziter Aktivierung und Bestätigung
- fail-closed bei unklarem Zustand

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
- versioniert
- pro Config Entry getrennt
- frei von Record-IDs, ReportedDeviceIds, Player-Keys, Benutzernamen und Zugangsdaten

Ein erwarteter, aber fehlender oder beschädigter Store stoppt automatische Wartungsläufe. Ein neuer leerer Store wird nur bei eindeutiger Erstinitialisierung angelegt.

## Serveraktionen

- Master-Schalter standardmäßig aus
- Automatik standardmäßig aus
- Warnseite und Pflichtbestätigung
- manuelle Aktion zusätzlich mit dynamischem Bestätigungstext
- aktive und undatierte Datensätze geschützt
- frische Revalidierung vor jedem Lauf
- kein automatisches Erzeugen einer Ignore-Regel

## Registry-Schutz

Registry-Änderungen erfordern exakte Gleichheit. Unzulässig sind:

- Wildcards
- Präfix-Matches
- Teilstring-Matches
- ungeprüfte Entity-IDs
- Wiederaufnahme nach Neustart
- Änderung bei vorhandenem State
- Änderung bei verbleibender gleicher Serverhistorie

HA-Mitbereinigung ist bei neuen Aktivierungen aus. Bestehende Werte bleiben bewusst erhalten, um Migrationen nicht stillschweigend zu verändern.

## Datenschutz

Diagnostics und Laufberichte enthalten nur:

- Integrationsversion
- aggregierte Geräteanzahl
- Schedulerstatus
- Zeitpunkte
- Statuscodes
- aggregierte Server- und Registry-Zähler

Private Identitäten werden weder gekürzt noch gehasht persistiert; sie werden vollständig weggelassen.

## Backup und Rollback

Vor jedem Live-Test erforderlich:

- vollständiges Home-Assistant-Backup
- belastbarer Emby-Backup- oder Wiederherstellungsweg
- dokumentierter Ausgangsstand der 29 Media-Player
- verfügbare Installationsquelle von `v0.3.0-rc3`

Der Rollback der Integration stellt keine zuvor veränderten Emby-Historieneinträge wieder her. Dafür ist der separate Emby-Wiederherstellungsweg erforderlich.
