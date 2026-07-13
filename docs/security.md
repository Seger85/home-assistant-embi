# Sicherheitsarchitektur

## Grundprinzipien

- lokale Kommunikation
- keine direkte `.storage`-Manipulation
- Least Privilege, soweit Emby dies zulässt
- destruktive Funktionen standardmäßig aus
- konkrete Auswahl statt pauschaler Löschaktion
- zweistufige Bestätigung
- Teilerfolge transparent melden
- sensible Werte in Diagnostics redigieren

## Redigierte Felder

- primärer `api_key`
- optionaler `server_cleanup_api_key`
- serverseitige Geräte-Historien-ID
- gemeldete Client-ID
- daraus gebildeter Player-Key
- Gerätename
- letzter Benutzername

App-Name, App-Version und letzter Aktivitätszeitpunkt bleiben für die technische Diagnose sichtbar.

## API-Schlüsselrotation

Nach einer vermuteten Offenlegung:

1. betroffenen Schlüssel auf dem Emby-Server widerrufen
2. neuen Schlüssel erzeugen
3. EMBi über „Verbindung bearbeiten“ bzw. „Serverbereinigung einrichten“ aktualisieren
4. Diagnostics und Logs auf Authentifizierungsfehler prüfen
5. alte Backups und Skripte auf Klartextschlüssel untersuchen

## Repository-Hygiene

Verboten im Repository:

- echte API-Schlüssel
- Home-Assistant-Long-Lived-Access-Tokens
- echte interne IPs in Test-Fixtures, soweit nicht ausdrücklich anonymisiert
- vollständige private Diagnostics
- `.storage`, Datenbanken oder Backups
