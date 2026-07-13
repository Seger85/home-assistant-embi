# Optionale Emby-Serverbereinigung

## Zweck

Die Funktion entfernt historische Einträge aus der Geräteübersicht des lokalen Emby-Servers. Sie löscht keine Filme, Serien, Benutzer oder Bibliotheken.

## Standardzustand

Die Funktion ist ausgeschaltet und das Löschmenü ist ausgeblendet.

## API-Schlüssel

EMBi kann verwenden:

- den normalen Verbindungsschlüssel oder
- einen optional hinterlegten separaten Bereinigungsschlüssel

Der separate Schlüssel wird beim Speichern gegen `/System/Info` validiert. Ob der Schlüssel auch löschen darf, lässt sich ohne destruktiven Test nicht zuverlässig vorab beweisen; ein fehlendes Recht wird deshalb als Fehler des jeweiligen Eintrags behandelt.

## Ablauf

1. Funktion ausdrücklich aktivieren.
2. Historieneinträge auswählen.
3. Entscheiden, ob erfolgreich gelöschte Clients zusätzlich ignoriert werden.
4. zweiten Bestätigungsdialog öffnen.
5. Schalter aktivieren.
6. exakten dynamischen Text eingeben.
7. EMBi löscht jeden Eintrag einzeln.
8. Ergebnis zeigt erfolgreiche und fehlgeschlagene Einträge.

## Teilerfolg

Mehrere Löschungen werden unabhängig behandelt. Ein Fehler bei einem Eintrag stoppt nicht die übrigen Löschungen.

Nur erfolgreich gelöschte Einträge werden – sofern aktiviert – über ihre stabile `ReportedDeviceId` zur Ignorierliste hinzugefügt.

## Grenzen und Rollback

- Eine serverseitige Löschung ist aus Home Assistant nicht rückgängig zu machen.
- Ein Emby-Server-Backup ist der einzige vollständige Rollback-Weg.
- Ein später verwendeter Client kann sich erneut registrieren.
- Das Ignorieren in EMBi verhindert nur die erneute HA-Entity-Erzeugung, nicht die Registrierung auf Emby.
