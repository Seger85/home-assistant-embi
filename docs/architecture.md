# Architektur

## Zielbild

EMBi ersetzt die eingebaute Home-Assistant-Komponente `emby` über dieselbe Domain. Es gibt genau einen Config Entry pro Emby-Server und ausschließlich einen Config-Entry-basierten Laufzeitpfad.

```text
Config Flow / Reconfigure
          │
          ▼
Config Entry (Verbindung + Options)
          │
          ├── EmbyApiClient ── REST /System/Info, /Devices
          │
          └── pyemby.EmbyServer ── Push-Status und Fernsteuerung
                         │
                         ▼
                 MediaPlayerEntity
```

## Verantwortlichkeiten

### `api.py`

- schlanker asynchroner REST-Client
- Validierung der Verbindung
- Lesen der Emby-Gerätehistorie
- Löschen eines ausdrücklich ausgewählten Historieneintrags
- Normalisierung in `EmbyDeviceRecord`

### `models.py`

`EmbiRuntimeData` hält pro Config Entry:

- REST-Client
- zuletzt beim Setup gelesene Gerätehistorie
- laufende pyemby-Instanz

Die Daten liegen über `ConfigEntry.runtime_data`, nicht in einem untypisierten globalen `hass.data`-Dictionary.

### `config_flow.py`

- Erstkonfiguration
- Rekonfiguration
- Gerätefilter
- sichere Sammelaktionen
- Registry-Bereinigung
- optionale Serverbereinigung
- About/Credits

### `media_player.py`

- pyemby-Laufzeitverbindung
- dynamische Anlage und Verfügbarkeit von Media-Playern
- Erhalt der bestehenden Unique ID
- Steuerbefehle und Medienattribute

### `diagnostics.py`

- Integrationsversion
- redigierte Verbindung und Optionen
- Laufzeitstatus
- redigierte Geräteübersicht
- Fehler der Geräteabfrage

## Identitätsmodell

Der entscheidende Architekturpunkt ist die Trennung zweier Emby-IDs.

| Feld | Bedeutung | Verwendung |
|---|---|---|
| `Id` | serverseitiger Historieneintrag | Auswahl und Parameter für `DELETE /Devices` |
| `ReportedDeviceId` | vom Client gemeldete stabile Identität | pyemby-/HA-Unique-ID, Auswahl und Ignorierregeln |
| `ReportedDeviceId.AppName` | konkrete Client-/App-Kombination | anzuzeigende Geräte |
| `ReportedDeviceId` | gesamter physischer/logischer Client | dauerhafte Ignorierregel über App-Varianten hinweg |

EMBi verändert vorhandene Unique IDs nicht.

## Entity-Lifecycle

1. pyemby meldet seine bekannten Geräte.
2. EMBi prüft zuerst die Ignorierliste.
3. Danach wird der gewählte Modus ausgewertet.
4. Erlaubte neue Geräte werden als Entität angelegt.
5. Nicht mehr erlaubte oder stale Geräte werden nicht aus der Registry gelöscht, sondern zunächst als nicht verfügbar geführt.
6. Eine bewusste Registry-Bereinigung ist separat möglich.

## Options-Migration 0.2 → 0.3

0.2 speicherte wegen einer fehlerhaften Zuordnung teilweise numerische `/Devices.Id`-Werte. Beim Setup von 0.3 werden bekannte alte Werte anhand der aktuellen Gerätehistorie umgewandelt:

- Positivliste: `Id` → `ReportedDeviceId.AppName`
- Ignorierliste: `Id` → `ReportedDeviceId`

Nicht mehr auflösbare Werte bleiben erhalten, damit eine Migration keine Benutzerentscheidung stillschweigend verwirft.

## Abhängigkeiten

- Home Assistant 2026.7 oder neuer als initiale Zielversion
- im Home-Assistant-Core-Image vorhandenes `pyemby`
- lokaler HTTP- oder HTTPS-Zugriff auf den Emby-Server

Vor einer Absenkung der Mindestversion müssen Config-Entry-Runtime-Daten, Selektoren und Flow-APIs gegen die jeweilige Home-Assistant-Version geprüft werden.
