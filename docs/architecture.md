# Architektur

## Zielbild

EMBi ersetzt die Core-Integration unter derselben Domain `emby`, verwendet jedoch ausschließlich den Config-Entry-Laufzeitpfad. Pro Emby-Server existiert genau ein Config Entry. Die Plattform bleibt ausschließlich `media_player`.

```text
Config Flow / Reconfigure
          │
          ▼
Config Entry 3.1
          │
          ├── EmbyApiClient ── /System/Info, /Devices, DELETE /Devices
          ├── pyemby.EmbyServer ── Push-Status und Fernsteuerung
          ├── Options Draft ── Apply / Discard
          └── Maintenance Runtime
                    ├── privater atomarer Store
                    ├── persistenter Laufbericht
                    ├── absoluter Scheduler
                    ├── gemeinsamer Lock
                    └── exakte Registry-Nachbereitung
```

## Module

### `entry_setup.py`

- validiert die bestehende Verbindung mit dem normalen EMBi-Verbindungsschlüssel
- liest Gerätehistorie
- migriert rc3-Optionen idempotent
- lädt beziehungsweise initialisiert den privaten Store
- erzeugt `EmbiRuntimeData`
- markiert unterbrochene Läufe fail-safe
- verarbeitet ausschließlich eine vorhandene same-process Registry-Queue
- startet Media-Player-Plattform und Scheduler

### `entry_lifecycle.py`

- Config-Entry-Migration auf Version 3.1
- sauberer Unload der Plattform
- Abmeldung des Scheduler-Callbacks
- Stoppen von pyemby
- zentraler Update-Listener für höchstens einen Reload nach Apply

### `maintenance_store.py`

- offizieller Home-Assistant-`Store`
- `private=True`
- `atomic_writes=True`
- Schema-Version und tolerantes Laden
- fehlender erwarteter oder beschädigter Store führt zu fail-safe Anhalten der Automatik

### `models.py`

`EmbiRuntimeData` enthält:

- REST-Client
- aktuelle Gerätehistorie
- pyemby-Instanz
- gemeinsamen Cleanup-Lock
- Store und `MaintenanceState`
- Storage-Verfügbarkeitsstatus
- Scheduler-Callback

`CleanupRunReport` enthält ausschließlich aggregierte Zähler und Zeitpunkte. Private Identitäten werden nicht persistiert.

### `scheduling.py` und `maintenance_scheduler.py`

- UTC-Normalisierung
- persistentes absolutes `next_run_at`
- Zukunftstermine bleiben unverändert
- fehlende, ungültige oder überfällige Termine erhalten genau einen 120-Sekunden-Catch-up
- nach Abschluss folgt der nächste Termin 24 Stunden später
- vor dem Callback wird der Store erneut gelesen
- Reloads und parallele Tasks erzeugen keinen doppelten Lauf

### `cleanup.py` und `maintenance_cycle_execute.py`

- strikter UTC-Cutoff
- aktive und undatierte Datensätze geschützt
- kein Batchlimit
- Einzelfehler stoppen den restlichen Lauf nicht
- Save vor jeder kritischen Phase
- nach Serverbereinigung erneute `/Devices`-Abfrage
- keine automatische Ignore-Regel
- Registry-Follow-up nur bei eindeutiger Zulässigkeit

### `maintenance_registry_*`

- Queue enthält nur exakte `ReportedDeviceId.AppName`-Keys und optional eine exakte Entity-ID
- same-process Follow-up nach kontrolliertem Reload
- Neustart mit `registry_pending` führt zu `interrupted`, nicht zu verspäteter Änderung
- Revalidierung prüft Domain, Plattform, Config Entry, Unique ID, State und verbleibende Historie
- Präfix-, Wildcard- und Teilstring-Matches sind ausgeschlossen
- `removed` wird erst nach tatsächlichem `registry.async_remove()` gezählt

### `options_draft.py`, `options_flow.py` und Mixins

- alle normalen Unterseiten ändern nur den Entwurf
- Apply validiert und schreibt einmal
- unveränderter Apply beendet ohne Write
- Discard stellt den Originalzustand wieder her
- Schließen über X schreibt nichts
- kritische Aktionen sind bei Dirty Draft gesperrt
- neue Automatik startet erst nach Apply

### `diagnostics.py`

- redigierte Verbindungsdaten
- redigierte identitätsbezogene Optionen
- aggregierter Laufbericht
- keine vollständigen Geräte-, Benutzer- oder Schlüsselwerte

## Identitätsmodell

| Feld | Bedeutung | Zulässige Verwendung |
|---|---|---|
| `Id` | serverseitiger Historieneintrag | ausschließlich Auswahl und `DELETE /Devices` |
| `ReportedDeviceId` | exakte Client-Identität | geräteweite Ignore-Regel |
| `ReportedDeviceId.AppName` | exakte App-/Client-Identität | pyemby-Key, HA-Unique-ID, Registry-Follow-up |

Die bestehende Unique-ID-Logik wird nicht verändert. Das ist die Grundlage für die 29-Player-Baseline und den Erhalt manueller Entity-Namen.

## Fail-safe Reihenfolge

1. Lock erwerben.
2. Laufstatus `running` speichern.
3. Geräte frisch lesen und Kandidaten revalidieren.
4. Kandidaten und Schutzfälle speichern.
5. Serverdatensätze einzeln verarbeiten.
6. Serverergebnis speichern.
7. Geräte erneut lesen.
8. exakte Registry-Keys planen und Queue speichern.
9. kontrollierten Reload auslösen.
10. Queue bei Setup erneut exakt prüfen.
11. zulässige Registry-Änderung ausführen und tatsächliche Zähler speichern.
12. Abschlusszeit und nächsten automatischen Termin speichern.

Scheitert ein Store-Write vor einer Serveränderung, wird sie nicht ausgeführt. Scheitert ein Write danach, wird keine Registry-Nachbereitung gestartet und der Bericht bleibt als unvollständig markiert.
