# Architektur

## Zielbild

EMBi ersetzt die eingebaute Home-Assistant-Komponente `emby` über dieselbe Domain. Es gibt genau einen Config Entry pro Emby-Server und ausschließlich einen Config-Entry-basierten Laufzeitpfad.

```text
Config Flow / Reconfigure
          │
          ▼
Config Entry (Verbindung + Options)
          │
          ├── EmbyApiClient ── REST /System/Info, /Devices, DELETE /Devices
          │
          ├── pyemby.EmbyServer ── Push-Status und Fernsteuerung
          │
          └── Maintenance Scheduler
                    │
                    ├── Alters- und Aktivitätsprüfung
                    ├── sequenzielle, unlimitierte Datensatzverarbeitung
                    ├── erneute /Devices-Prüfung
                    └── vorgemerkte Registry-Bereinigung beim Reload
```

## Verantwortlichkeiten

### `api.py`

- asynchroner REST-Client
- Validierung der Verbindung
- Lesen der Emby-Gerätehistorie
- Löschen eines ausdrücklich ausgewählten Historieneintrags
- Normalisierung in `EmbyDeviceRecord`
- robuste UTC-Normalisierung von Emby-Aktivitätszeitpunkten, einschließlich siebenstelliger Bruchteile

### `cleanup.py`

- reine, testbare Alters- und Sicherheitsplanung
- Ausschluss aktiver Player
- Ausschluss unbekannter oder ungültiger Aktivitätszeitpunkte
- keine Begrenzung der Kandidatenzahl
- unabhängige Verarbeitung aller Datensätze
- Ermittlung, welche `ReportedDeviceId.AppName`-Identitäten nach der Löschung keinen verbleibenden Serverdatensatz mehr besitzen

### `maintenance.py`

- Aufbau des Cleanup-API-Clients
- Ermittlung aktuell spielender oder pausierter Player
- Zeitplanung: einmalig 120 Sekunden nach Erstaktivierung, danach 24 Stunden
- automatische Bereinigung unter einem Laufzeit-Lock
- aggregierte Laufzeitstatistik
- Queue für sichere HA-Registry-Nachbereitung
- tatsächliche Registry-Entfernung erst während des nächsten Config-Entry-Setups

### `models.py`

`EmbiRuntimeData` hält pro Config Entry:

- REST-Client
- zuletzt gelesene Gerätehistorie
- laufende pyemby-Instanz
- Cleanup-Lock
- Scheduler-Status
- aggregierte Ergebnisse des letzten automatischen Laufs

### `config_flow.py`

- Erstkonfiguration und Rekonfiguration

### `options_flow.py`

- Gerätefilter und Sammelaktionen
- manuelle Registry-Bereinigung
- Menüführung und About/Credits

### `maintenance_flow.py`

- Master-Schalter und Cleanup-API-Schlüssel
- manueller Altersfilter, Auswahl und Bestätigung
- separat bestätigte automatische Bereinigung

### `media_player.py`

- pyemby-Laufzeitverbindung
- dynamische Anlage und Verfügbarkeit von Media-Playern
- Erhalt der bestehenden Unique ID
- Steuerbefehle und Medienattribute

### `diagnostics.py`

- Integrationsversion
- redigierte Verbindung und Optionen
- Runtime- und Schedulerstatus
- aggregierte Cleanup-Zähler
- redigierte Geräteübersicht

## Identitätsmodell

| Feld | Bedeutung | Verwendung |
|---|---|---|
| `Id` | serverseitiger Historieneintrag | Auswahl und Parameter für `DELETE /Devices` |
| `ReportedDeviceId` | stabile rohe Client-Identität | geräteweite Ignorierregel |
| `ReportedDeviceId.AppName` | konkrete Client-/App-Kombination | pyemby-/HA-Unique-ID und präzise Registry-Nachbereitung |

EMBi verändert vorhandene Unique IDs nicht.

## Entity-Lifecycle nach Serverlöschung

1. Datensatz muss den Altersfilter erfüllen und darf nicht aktiv sein.
2. `DELETE /Devices` muss erfolgreich sein.
3. EMBi liest `/Devices` erneut.
4. Existiert noch ein Datensatz mit derselben `ReportedDeviceId.AppName`, bleibt der HA-Player erhalten.
5. Andernfalls wird ausschließlich dieser Player-Key für die Registry-Nachbereitung vorgemerkt.
6. EMBi lädt den Config Entry kontrolliert neu.
7. Nach dem Unload darf kein Entity-State mehr vorhanden sein.
8. Nur eine zum selben Config Entry gehörende `media_player`-Registry-Entität mit exakt passender Unique ID wird entfernt.
9. Nutzt der Client Emby später erneut, kann er sich registrieren und wieder als Entity erscheinen.

## Scheduler

Die Automatik ist nur aktiv, wenn sowohl der Master-Schalter der Serverbereinigung als auch der separate Automatik-Schalter gesetzt sind.

- initialer Lauf: einmalig 120 Sekunden nach der bewussten Erstaktivierung
- der abgeschlossene Erstversuch wird intern in den Config-Entry-Optionen markiert
- Folgeintervall: 24 Stunden
- ein normaler Reload oder Neustart startet den 120-Sekunden-Erstlauf nicht erneut; das 24-Stunden-Intervall wird neu geplant
- Laufzeit-Lock verhindert parallele Bereinigungen
- alle Löschungen bleiben altersbasiert, revalidiert und pro Datensatz unabhängig
- es gibt bewusst kein Maximum pro Lauf

## Options-Migration 0.2 → 0.3

Alte numerische `/Devices.Id`-Werte werden anhand der aktuellen Gerätehistorie umgewandelt:

- Positivliste: `Id` → `ReportedDeviceId.AppName`
- Ignorierliste: `Id` → `ReportedDeviceId`

Nicht mehr auflösbare Werte bleiben erhalten.

## Abhängigkeiten

- Home Assistant 2026.7 oder neuer
- im Home-Assistant-Core-Image vorhandenes `pyemby`
- lokaler HTTP- oder HTTPS-Zugriff auf den Emby-Server
