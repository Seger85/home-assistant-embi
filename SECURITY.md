# Security Policy

## Unterstützte Versionen

Während der Vorabphase wird nur die jeweils neueste EMBi-Version sicherheitsseitig gepflegt.

## Sicherheitslücken melden

Bitte keine Zugangsdaten oder vollständigen Diagnosedateien in öffentliche Issues einstellen. Sicherheitsrelevante Hinweise zunächst privat an den Repository-Eigentümer `Seger85` melden.

## Vertrauliche Daten

EMBi behandelt insbesondere folgende Werte als vertraulich:

- primärer Emby-API-Schlüssel
- optionaler API-Schlüssel für Serverbereinigung
- Geräte-Historien-ID
- gemeldete Client-ID
- Client-/Gerätename
- letzter Benutzername

Diagnostics redigieren diese Werte. Vor einer Veröffentlichung sollte eine Diagnosedatei dennoch manuell geprüft werden.

## Destruktive Funktionen

Die serverseitige Gerätebereinigung ist standardmäßig deaktiviert. Sie benötigt eine konkrete Auswahl und einen zweiten Bestätigungsschritt. Eine erfolgreiche Löschung kann nicht durch Home Assistant rückgängig gemacht werden; ein Emby-Server-Backup bleibt der einzige vollständige Rollback-Weg.
