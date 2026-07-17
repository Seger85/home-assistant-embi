# Troubleshooting

## Integration lädt nicht

Prüfen:

- Home-Assistant-Log auf `emby`, `EMBi`, `ConfigEntryNotReady` und `ConfigEntryAuthFailed`
- Host, Port und HTTPS
- normalen EMBi-Verbindungsschlüssel
- Erreichbarkeit von `/System/Info` und `/Devices`
- ob eine zweite Custom Component dieselbe Domain `emby` verwendet
- ob Manifest und Runtime beide `0.9.0` melden

## Wartungsspeicher nicht verfügbar

Bei `maintenance_storage_available: false` keine Wartungsaktion starten. Dateisystem, freien Speicher, Logs und Backup prüfen. `.storage` niemals direkt bearbeiten. Der sichere Rückfallpunkt ist Stable `v0.3.0` oder das vollständige Home-Assistant-Backup.

## Ein Client erscheint unter „Unklare Clients“

Das ist kein Fehler. EMBi klassifiziert einen technischen Zugriff nur anhand belastbarer Capability-, Typ- oder Verhaltensdaten. Ein Produktname allein reicht nicht. Fehlt diese Evidenz, bleibt der Eintrag bewusst unter **Unklare Clients**.

## Eine gültige deaktivierte Entity wird angezeigt

Eine deaktivierte, weiterhin zum EMBi-Config-Entry gehörende und auf dem Emby-Server bekannte Entity ist gültig. Sie darf nicht als Orphan klassifiziert werden. Beim erneuten Aktivieren müssen Entity-ID, Unique ID und Registry-Metadaten erhalten bleiben.

## Ein Player ist geschützt

`playing` und `paused` sind geschützt. Auch ein unklarer Wiedergabestatus arbeitet fail-safe. Eine Änderung ist erst zulässig, wenn frische Emby- und Home-Assistant-Daten einen sicher nicht spielenden Zustand bestätigen.

## Sichtbarkeit und Home-Assistant-Registry unterscheiden sich

Normales Ausblenden in EMBi und eine Änderung der Home-Assistant-Registry sind getrennte Vorgänge. Serverhistorie und Home-Assistant-Player bleiben ebenfalls getrennt. Dadurch verändert eine normale Sichtbarkeitsregel keine Emby-Serverhistorie.

## Wiederherstellung schlägt fehl

EMBi entfernt nur die exakte Hidden-Rule und lädt den Config Entry neu. Danach muss genau eine zum selben Config Entry gehörende `media_player`-Entity mit der erwarteten Unique ID vorhanden sein. Mehrdeutigkeit oder eine fehlende Entity wird als Fehler gemeldet.

## Automatische Bereinigung läuft nicht

Prüfen:

- Automatik wurde final per Apply gespeichert
- Wartungsspeicher ist verfügbar
- Config Entry ist `loaded`
- `next_run_at` liegt nicht noch in der Zukunft
- kein Lauf hält den gemeinsamen Lock

In der aktuellen produktiven Ausgangsbasis ist die automatische Bereinigung bewusst deaktiviert.

## Termin verschiebt sich bei Reload oder Neustart

Ein gültiger Zukunftstermin darf sich nicht verschieben. Diagnostics und letzten Laufbericht vergleichen. Bei Abweichung keine Wartungsaktion auslösen und Logs sichern.

## Custom 364 erscheint

Das ist korrekt. EMBi migriert `364` nicht automatisch auf `365`. Der numerische Wert bleibt die Quelle der Wahrheit. Ein vorhandener Wert `365` bleibt ebenfalls exakt `365`.

## Optionen scheinbar nicht gespeichert

Unterseiten ändern nur den Entwurf. **Änderungen prüfen** zeigt semantische Vorher-/Nachher-Werte. Erst **Änderungen übernehmen** schreibt die Optionen. **Änderungen verwerfen** und Schließen über X schreiben nichts.

## Media-Player fehlen oder haben andere IDs

Der aktuell verifizierte Referenzstand vor dem privaten Upgrade ist:

- 69 Emby-Server-Historieneinträge
- 30 aktivierte und geladene EMBi-Media-Player
- kein Registry-Orphan
- automatische Bereinigung deaktiviert
- manuelle und automatische Schwelle jeweils 365 Tage

Eine abweichende Playerzahl ist nur akzeptabel, wenn unmittelbar vor dem Test eine reale Emby-Clientänderung dokumentiert wurde. Zusätzlich Entity-ID, Unique ID, individuellen Namen, Aliase, Area, Labels, disabled state, Repairs und Logs prüfen. Bei Identitätsabweichung Rollback auf `v0.3.0` oder das vollständige Backup vorbereiten.

## HACS bietet 0.9.0 noch nicht an

Vor der öffentlichen Veröffentlichung ist das korrekt. Das private `embi-test-<commit>`-Paket ist ein GitHub-Actions-Artefakt und kein HACS-Release. HACS Stable erscheint erst nach erfolgreicher privater Abnahme, Promotion nach `main`, Tag `v0.9.0` und regulärem GitHub Release.
