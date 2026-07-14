# Sicherheitsarchitektur

## Grundprinzipien

- lokale Kommunikation
- keine direkte `.storage`-Manipulation
- destruktive Funktionen standardmäßig aus
- separater Master- und Automatik-Schalter
- bewusste Erstaktivierung mit Warnung und exaktem Text
- Altersfilter standardmäßig 365 Tage
- aktive Wiedergaben immer geschützt
- unbekannte Aktivitätszeitpunkte fail-closed geschützt
- keine maximale Löschzahl, aber unabhängige Fehlerbehandlung pro Datensatz
- serverseitige Löschung vor jeder Registry-Nachbereitung
- frische `/Devices`-Revalidierung nach Löschung
- Registry-Entfernung nur während eines kontrollierten Reloads ohne Entity-State
- sensible Werte in Diagnostics redigieren
- gespeicherte API-Schlüssel nie als Passwortfeld-Standardwert zurückgeben

## Sicherheitsgrenzen der Identitäten

- `Id` wird ausschließlich für einen konkreten historischen Serverdatensatz und `DELETE /Devices` verwendet.
- `ReportedDeviceId` bleibt die rohe, geräteweite Ignorieridentität.
- `ReportedDeviceId.AppName` bleibt die bestehende pyemby-/HA-Unique-ID und die einzige Identität für die präzise Registry-Nachbereitung.

Ein historischer `Id`-Wert darf niemals als HA-Unique-ID verwendet werden.

## Schutz vor falscher Registry-Löschung

Eine automatische oder manuelle Serverlöschung führt nur dann zu einer HA-Registry-Entfernung, wenn:

- der Serverdatensatz erfolgreich gelöscht wurde
- eine neue Serverabfrage keinen gleichen Player-Key mehr liefert
- der Registry-Eintrag zur Plattform und zum Config Entry gehört
- während des Reloads kein Entity-State existiert

Die vorgemerkte Queue enthält nur exakte Player-Keys und keine rohen `ReportedDeviceId`-Werte. Dadurch werden andere App-Varianten nicht mitgelöscht.

## Redigierte Felder

- primärer `api_key`
- optionaler `server_cleanup_api_key`
- serverseitige Historien-ID
- gemeldete Client-ID
- Player-Key
- Gerätename
- letzter Benutzername

Automatische Laufdiagnosen enthalten nur Zähler, Zeitpunkt, Schalterstatus und eine kategorisierte Fehlerursache.

## Repository-Hygiene

Verboten im Repository:

- echte API-Schlüssel
- Home-Assistant-Long-Lived-Access-Tokens
- private Geräte-IDs oder Benutzernamen
- vollständige private Diagnostics
- `.storage`, Datenbanken oder Backups
