# Changelog

Alle wesentlichen Änderungen an EMBi werden in dieser Datei dokumentiert. Das Projekt folgt Semantic Versioning.

## [Unreleased]

### Remaining before public 0.3.0

- kontrollierte Home-Assistant-Liveabnahme des unveröffentlichten Testartefakts
- visueller Options-Flow-Test auf iPhone, iPad und Desktop
- gezielter tatsächlicher Registry-Removal-Test mit sicherem Testobjekt
- Rollbackprüfung auf `v0.3.0-rc3`
- Promotion von `develop` nach `main` erst nach Gerrys Freigabe

## [0.3.0] - Stable vorbereitet, noch nicht veröffentlicht

### Added

- versionierter, privater und atomarer Wartungsstatus über Home Assistants `Store`
- persistenter absoluter Scheduler mit `next_run_at`
- 120-Sekunden-Grace-Period für Erstaktivierung, überfällige Termine und rc3-Migration
- strukturierter Laufbericht mit getrennten Server-, Registry- und Schutz-Zählern
- zentraler Lock gegen parallele manuelle und automatische Läufe
- zusammenhängender Options-Flow-Entwurf mit finalem Apply und Discard
- getrennte app-spezifische und geräteweite Ignorierregeln
- sichtbare Aufbewahrung nicht eindeutig migrierbarer Ignore-Altwerte
- getrennte manuelle und automatische Alterswerte mit Presets 7, 30, 90, 180 und 365 Tage plus Custom
- unveröffentlichtes, releasegleiches Testartefakt mit SHA-256 und `BUILD_COMMIT`

### Changed

- vollständige Erfolge, null Kandidaten und erwartete Schutzfälle werden als INFO protokolliert
- Teilerfolge werden als WARNING und vollständige technische Fehler als ERROR protokolliert
- Persistent Notifications erscheinen nur bei Teilerfolg oder Fehler
- Folgeplanung erfolgt 24 Stunden nach Abschluss des vorherigen Laufversuchs
- HA-Mitbereinigung ist für neue Aktivierungen standardmäßig aus; vorhandene Werte bleiben erhalten
- Diagnostics enthalten ausschließlich aggregierte Wartungsdaten und redigierte Optionen
- HACS verwendet `zip_release: true` und `filename: embi.zip`

### Removed

- zweiter separater Cleanup-API-Schlüssel
- einzutippender Aktivierungssatz für die Automatik
- automatische Ignorierung nach einer Serverlöschung
- gemischte `ignored_device_ids`-Liste als aktives Datenmodell
- sofortige Optionswrites und Reloads nach jeder normalen Unterseite

### Regression test

Der korrigierte 74-zu-69-Fall ist als synthetischer Vertragstest abgebildet: fünf Datensätze sind strikt älter als 364 Tage, fünf Serverlöschungen sind erfolgreich, null schlagen fehl, 69 bleiben übrig, fünf Registry-Keys werden queued, null Entities werden gematcht oder entfernt und fünf werden als missing gezählt.

## [0.3.0-rc3] - Finale Gerätebereinigung

### Added

- manuelle Altersfilterung vor der Auswahl historischer Emby-Geräte
- Standard-Altersfilter von 365 Tagen
- separat aktivierbare automatische Serverbereinigung
- bewusste Erstaktivierung per Warnschalter und exaktem Bestätigungstext
- erster automatischer Lauf 120 Sekunden nach der bewussten Erstaktivierung
- Wiederholung der Automatik alle 24 Stunden
- sichere Nachlaufbereinigung zugehöriger Home-Assistant-Media-Player
- aggregierte, identitätsfreie Laufzeitdiagnose der Automatik

### Changed

- automatische Bereinigung verarbeitet bewusst alle zulässigen Datensätze ohne maximale Löschzahl pro Lauf
- aktive Player und Datensätze ohne gültigen letzten Aktivitätszeitpunkt sind ausgeschlossen
- das Deaktivieren der übergeordneten Serverbereinigung deaktiviert ebenfalls die Automatik
- manuelle Serverbereinigung kann erfolgreich gelöschte HA-Media-Player zusätzlich entfernen

### Security

- ein HA-Registry-Eintrag wird nur nach erfolgreicher Emby-Löschung berücksichtigt
- eine frische `/Devices`-Abfrage muss bestätigen, dass kein verbleibender Datensatz dieselbe `ReportedDeviceId.AppName`-Identität verwendet
- die Registry-Entfernung erfolgt erst nach einem kontrollierten Config-Entry-Reload und nur ohne vorhandenen Entity-State
- aktive Wiedergaben werden vor der Serverlöschung ausgeschlossen
- unbekannte oder nicht parsebare Aktivitätszeitpunkte werden fail-closed übersprungen
- Logs und Diagnostics enthalten nur aggregierte Zähler, keine privaten Geräte-IDs

## [0.3.0-rc2] - Runtime-, Safety- und UI-Härtung

### Changed

- Sammelaktionen zählen und speichern nur eindeutige Client-/App- beziehungsweise Client-Identitäten
- Serverbereinigungs-Einträge zeigen App, Version, letzte Aktivität und eine kurze Datensatz-ID
- Rekonfiguration und Serverbereinigung zeigen gespeicherte API-Schlüssel nicht als Passwortfeld-Standardwert

### Fixed

- doppelte Allowlist-Werte durch mehrere historische `/Devices`-Datensätze
- aktive Registry-Kandidaten
- fehlende unmittelbare Registry-Revalidierung
- nicht eindeutig beschriftete historische Emby-Datensätze

## [0.3.0-rc1] - Release Candidate

- stabiles internes Gerätemodell mit getrennter Historien- und Client-ID
- automatische Migration alter numerischer 0.2-Auswahlwerte
- Runtime-Dataclass über `ConfigEntry.runtime_data`
- Sammelaktionen für Geräteauswahl und Ignorierliste
- standardmäßig deaktivierte optionale Serverbereinigung
- zweistufige Löschbestätigung
- Teilerfolgsauswertung
- vollständige deutsche und englische Texte
- Legacy-YAML-Setup-Pfad entfernt

## [0.2.0] - Produktive Baseline

- Config Flow und Reconfigure Flow
- Options Flow für Geräte, Registry-Bereinigung, Serverbereinigung und About
- Migration vorhandener Media-Player auf einen Config Entry
- Erhalt bestehender Entity-IDs und Unique IDs
- Deutsch/Englisch und Diagnostics
