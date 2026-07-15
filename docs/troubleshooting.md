# Troubleshooting

## Integration lädt nicht

Prüfen:

- Home-Assistant-Log auf `emby`, `EMBi`, `ConfigEntryNotReady` und `ConfigEntryAuthFailed`
- Host, Port und HTTPS
- normalen EMBi-Verbindungsschlüssel
- Erreichbarkeit von `/System/Info` und `/Devices`
- ob eine zweite Custom Component dieselbe Domain `emby` verwendet

## Wartungsspeicher nicht verfügbar

Symptome:

- Persistent Notification „EMBi-Wartung angehalten“
- Automatik nicht geplant
- `maintenance_storage_available: false` in Diagnostics

Vorgehen:

1. keine Wartungsaktion auslösen
2. Home-Assistant-Dateisystem und freien Speicher prüfen
3. Logs auf Storage-Korruption oder Write-Fehler prüfen
4. Backupzustand prüfen
5. nicht manuell in `.storage` editieren
6. bei Bedarf auf `v0.3.0-rc3` und Backup zurückrollen

## `registry_pending` nach Neustart

Das ist ein bewusst fail-safe behandelter Zustand. EMBi führt keine verspätete Registry-Änderung aus. Der Bericht wird als `interrupted` markiert. Serverergebnisse bleiben im Bericht erhalten; die Registry-Nachbereitung muss später mit einem neuen kontrollierten Testobjekt erneut geprüft werden.

## `queued` größer als `removed`

Das ist nicht automatisch ein Fehler. Mögliche Gründe:

- Entity nie vorhanden: `missing`
- aktiver State: protected
- verbleibende gleiche Historie: protected
- falscher Config Entry oder Plattform: protected
- Unique ID verändert oder mehrdeutig: protected

Nur ein tatsächlicher `registry.async_remove()` erhöht `removed`.

## Automatik läuft nach 120 Sekunden nicht

Prüfen:

- Master-Schalter und Automatik wurden final per Apply gespeichert
- Store ist verfügbar
- Config Entry ist `loaded`
- `next_run_at` liegt nicht noch in der Zukunft
- kein manueller oder anderer automatischer Lauf hält den gemeinsamen Lock
- die Automatik wurde während der Grace Period nicht wieder deaktiviert

## Termin verschiebt sich bei Reload oder Neustart

Ein gültiger Zukunftstermin darf sich nicht verschieben. Diagnosedaten und „Letzter Bereinigungslauf“ vergleichen. Bei Abweichung keine Wartungsaktion auslösen und Logs sichern.

## Custom 364 erscheint

Das ist korrekt. Stable migriert 364 nicht automatisch auf 365. Die bewusste Auswahl von 365 erfolgt erst im Live-Test über den Options Flow.

## Optionen scheinbar nicht gespeichert

Unterseiten ändern nur den Entwurf. Am Ende **Änderungen übernehmen** bestätigen. **Änderungen verwerfen** oder Schließen über X schreibt nichts.

## Wartungsmenüs fehlen

Bei ungespeicherten Entwurfsänderungen sind kritische Aktionen absichtlich gesperrt. Entwurf zuerst übernehmen oder verwerfen. Die manuelle Serverbereinigung ist außerdem nur sichtbar, wenn der Master-Schalter bereits angewendet ist.

## Media-Player fehlen oder haben andere IDs

Sofort stoppen und vergleichen:

- erwartete Anzahl 29
- Config-Entry-Zuordnung
- Entity-ID
- Unique ID
- individueller Name
- Disabled-/Restored-/Orphan-Status

Keine Registry-Nachbereitung starten. Bei Identitätsabweichung Rollback auf rc3 vorbereiten.

## HACS bietet Stable nicht an

Vor der öffentlichen Veröffentlichung ist das korrekt. Das unveröffentlichte Testpaket ist ein Actions-Artefakt und kein HACS-Release. Stable erscheint erst nach Merge nach `main`, Tag `v0.3.0` und GitHub Stable Release.
