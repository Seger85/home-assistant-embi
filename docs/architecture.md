# Architektur

## Zielbild

EMBi verwendet weiterhin die Domain `emby`, ausschließlich Config Entries und ausschließlich die Plattform `media_player`. Pro Emby-Server existiert ein Config Entry.

```text
Config Flow / Reconfigure
          │
          ▼
Config Entry 4.0
          │
          ├── EmbyApiClient
          │     ├── /System/Info
          │     ├── /Devices
          │     └── DELETE /Devices
          ├── pyemby.EmbyServer
          │     └── Push-Status und Fernsteuerung
          ├── Player Catalog
          │     ├── Benutzer- und Shared-Gruppen
          │     ├── technische/unklare Klassifizierung
          │     └── HA Registry, Anzeigename, Entity-ID und Status
          ├── Options Draft
          │     ├── Geräte & Player
          │     ├── Bereinigung
          │     └── semantisches Review / Apply / Discard
          └── Maintenance Runtime
                ├── offizieller privater Store
                ├── Lauf-, Migration-, Removal- und Restore-Berichte
                ├── absoluter Scheduler
                ├── gemeinsamer Lock
                └── exakte Registry-Operationen
```

## Identitäts- und Kontextmodell

### Interne Identitäten

| Feld | Bedeutung | Verwendung |
|---|---|---|
| `Id` | serverseitiger Historieneintrag | Auswahl und `DELETE /Devices` |
| `ReportedDeviceId` | rohe Client-/Geräteidentität | exakte geräteweite Sichtbarkeitsregel |
| `ReportedDeviceId.AppName` | logischer Player-Key | pyemby-Key, bestehende HA-Unique-ID, exakte Player-Regel |
| `entity_id` | Home-Assistant-Entity | sichtbarer Benutzerkontext und Registry-Aktion |

Diese Identitäten bleiben intern strikt getrennt. Die normale UI zeigt statt ReportedDeviceId, Config Entry ID und Unique ID verständliche App-/Geräteinformationen, HA-Anzeigename und die vollständige Entity-ID.

### `player_context.py`

`PlayerContext` vereinigt pro logischem Player:

- aktuelle und historische Emby-Records
- alle ausdrücklich bekannten Benutzer
- letzte Aktivität
- App- und Gerätename
- Home-Assistant-Anzeigename und Entity-ID
- Registry- und Disabled-Status
- Runtime-/Wiedergabestatus
- Sichtbarkeit und exakte Hidden-Regeln
- Orphan-, Removal- und Schutzentscheidung

Gruppierung:

1. genau ein bekannter Benutzer
2. mehrere Benutzer → **Gemeinsam genutzt**
3. kein Benutzer, Wiedergabeclient → **Ohne Benutzerzuordnung**
4. eindeutig technischer Zugriff → **Technische Zugriffe**
5. nicht sicher klassifizierbar → **Unklare Clients**

Die technische Klassifizierung verwendet explizite Capability-/Client-Type-Daten oder belastbares wiederholtes Verhalten. Produktnamen allein sind kein Klassifikationsgrund.

## Config Entry und Migration

### `entry_setup.py`

- Verbindung und API-Schlüssel validieren
- `/Devices` frisch lesen
- Optionsmigration auf Schema 2 idempotent durchführen
- Wartungs-Store laden beziehungsweise initialisieren
- Migrationsergebnis redigiert speichern
- `EmbiRuntimeData` erzeugen
- unterbrochene Wartung fail-safe markieren
- Plattform und Scheduler starten

### `entry_lifecycle.py`

- Config Entry auf Version 4.0 anheben
- Plattform und Scheduler sauber entladen
- pyemby stoppen
- genau einen Update-Listener-Reload nach externem Optionscommit ausführen

Die Migration verändert weder Unique-ID-Logik noch Entity-Registry-Metadaten. Namen, Entity-IDs, Aliase, Areas, Labels und disabled state bleiben Home Assistant überlassen und werden nicht neu geschrieben.

## Sichtbarkeit und Optionsmodell

### `options_model.py`

Kanonische Optionen:

- `global_player_mode`
- `auto_show_new_players`
- `technical_access_visibility`
- `hidden_exact_players`
- `hidden_whole_devices`
- `user_master_visibility`
- `unresolved_legacy_rules`

Alte Allow-/Ignore-Werte werden exakt migriert. Uneindeutige Altwerte bleiben in `unresolved_legacy_rules`; EMBi rät keine neue Identität.

### `media_player.py`

- pyemby-Unique-ID bleibt unverändert der bestehende Player-Key
- Sichtbarkeit wird anhand des kanonischen 0.9-Modells entschieden
- Active-only berücksichtigt `playing` und `paused`
- technische Zugriffe sind standardmäßig bei Neuinstallationen verborgen
- unklare Clients werden nicht automatisch technisch behandelt

### Options-Flow-Module

- `options_flow.py`: Root, Review, Apply, Discard
- `options_devices.py`: Benutzergruppen, Suche, Sichtbarkeit, disabled enable
- `options_cleanup.py`: gemeinsame Cleanup-Einstellungen und Serverhistorie
- `options_ha_cleanup.py`: separat bestätigte Home-Assistant-Player-Entfernung
- `options_review.py`: semantische Vorher-/Nachher-Ausgabe
- `options_runtime.py`: frischer Player Catalog und aggregierte Zähler

Normale Unterseiten verändern nur den In-Memory-Entwurf. Apply schreibt Optionen einmal, aktualisiert gegebenenfalls disabled state über die offizielle Entity Registry API und lädt die Integration höchstens einmal neu. Discard und Schließen über X schreiben nichts.

## Home-Assistant-Player entfernen und wiederherstellen

### `player_actions.py` und `player_action_common.py`

Entfernung:

1. gemeinsamen Lock erwerben
2. `/Devices`, Registry und States frisch lesen
3. exakten Config Entry, Domain, Plattform und Unique ID prüfen
4. `playing`, `paused` und unklaren Wiedergabestatus blockieren
5. exakte Hidden-Regel speichern
6. Integration neu laden und State-Abbau prüfen
7. nur die eindeutig zugehörige Registry-Entity entfernen
8. erneut laden und prüfen, dass der Player nicht zurückkehrt
9. aggregiertes Ergebnis persistieren

Wiederherstellung:

1. nur die exakte Hidden-Regel entfernen
2. Integration neu laden
3. exakt eine zugehörige Entity suchen
4. Entity-ID und Anzeigename als Ergebnis zurückgeben
5. aggregiertes Ergebnis persistieren

Serverhistorie wird durch diese Aktionen nicht gelöscht.

## Serverhistorien-Bereinigung

Bestehende Maintenance-Module bleiben zuständig für:

- strikt älter als Cutoff in UTC
- Schutz aktiver und undatierter Records
- einzelnes `DELETE /Devices` je bestätigtem Record
- kein Batchlimit
- Einzelfehler stoppen den restlichen Lauf nicht
- frische `/Devices`-Revalidierung
- exakte optionale Registry-Nachbereitung
- keine automatische neue Hidden-/Ignore-Regel

Serverhistorien-Löschung und normale Home-Assistant-Player-Entfernung sind im UI nebeneinander, technisch aber getrennte Transaktionen.

## Persistenz

### `maintenance_store.py` und `models.py`

- offizielle `homeassistant.helpers.storage.Store`-API
- `private=True`
- `atomic_writes=True`
- kompatibler Store-Envelope
- versioniertes internes Schema
- Laufbericht
- `next_run_at`
- MigrationSummary
- letzte HA-Player-Aktion
- letzte Wiederherstellung

Persistiert werden nur aggregierte Zähler, Status, Zeitpunkte und kategorisierte Fehler. Vollständige Record-IDs, ReportedDeviceIds, Player-Keys, API-Schlüssel und Benutzernamen sind ausgeschlossen.

## Scheduler

- persistentes absolutes `next_run_at`
- gültiger Zukunftstermin bleibt bei Reload/Neustart unverändert
- fehlender, ungültiger oder überfälliger Termin erhält einen 120-Sekunden-Catch-up
- Registrierung darf während Setup erfolgen
- Ausführung verlangt unmittelbar vorher `LOADED`, aktuellen Runtime-Bezug, Store, beide Schalter, keinen Unload, freien Lock und Fälligkeit
- nach Abschluss nächster Termin plus 24 Stunden
- kein Doppelcallback und keine unsichere Wiederholung destruktiver Requests

## Diagnostics und Logging

Diagnostics enthalten:

- Version und Config-Entry-Schema
- redigierte Daten/Optionen
- Migrationsstatus
- Serverhistorien- und HA-Player-Zähler
- Benutzergruppen- und Klassifizierungszähler
- Sichtbarkeitszähler
- Scheduler- und Cleanup-Status
- aggregierte Removal-/Restore-Ergebnisse

Logging:

- vollständiger Erfolg und erwartete Schutzfälle: INFO
- Teilerfolg: WARNING
- technischer Abbruch: ERROR
- Persistent Notification nur bei Warning/Error
