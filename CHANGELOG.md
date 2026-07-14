# Changelog

Alle wesentlichen Änderungen an EMBi werden in dieser Datei dokumentiert. Das Projekt folgt Semantic Versioning.

## [Unreleased]

### Remaining

- kontrolliertes HACS-Liveupgrade von rc1 beziehungsweise rc2 auf 0.3.0-rc3
- visuelle Prüfung der neuen manuellen und automatischen Bereinigungsdialoge
- kontrollierter produktiver Test mit Backup und bewusst ausgewählten alten Datensätzen
- Entscheidung über einen weiteren Release Candidate oder die stabile 0.3.0

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
- aktive Player und Datensätze ohne gültigen letzten Aktivitätszeitpunkt sind von manueller und automatischer Altersbereinigung ausgeschlossen
- das Deaktivieren der übergeordneten Serverbereinigung deaktiviert ebenfalls die Automatik
- manuelle Serverbereinigung kann erfolgreich gelöschte HA-Media-Player zusätzlich entfernen

### Security

- ein HA-Registry-Eintrag wird nur nach erfolgreicher Emby-Löschung berücksichtigt
- eine frische `/Devices`-Abfrage muss bestätigen, dass kein verbleibender Datensatz dieselbe `ReportedDeviceId.AppName`-Identität verwendet
- die Registry-Entfernung erfolgt erst nach einem kontrollierten Config-Entry-Reload und nur ohne vorhandenen Entity-State
- aktive Wiedergaben (`playing`/`paused`) werden bereits vor der Serverlöschung ausgeschlossen
- unbekannte oder nicht parsebare Aktivitätszeitpunkte werden fail-closed übersprungen
- Logs und Diagnostics enthalten nur aggregierte Zähler, keine privaten Geräte-IDs

## [0.3.0-rc2] - Runtime-, Safety- und UI-Härtung

### Changed

- Sammelaktionen zählen und speichern nur eindeutige Client-/App- beziehungsweise Client-Identitäten
- Serverbereinigungs-Einträge zeigen App, Version, letzte Aktivität und eine kurze Datensatz-ID
- Rekonfiguration und Serverbereinigung zeigen gespeicherte API-Schlüssel nicht mehr als Passwortfeld-Standardwert
- deutsche und englische Hinweise erklären das sichere Beibehalten vorhandener Schlüssel

### Fixed

- „Alle aktuellen Geräte auswählen“ konnte durch mehrere historische `/Devices`-Datensätze doppelte Allowlist-Werte erzeugen
- aktive Legacy-YAML- oder ignorierte Entitäten konnten als Registry-Bereinigungskandidaten erscheinen
- Registry-Kandidaten werden unmittelbar vor dem Entfernen erneut validiert
- gleichnamige historische Emby-Datensätze waren im Serverbereinigungs-Selektor nicht eindeutig unterscheidbar

### Security

- bestehende Verbindungs- und Bereinigungs-API-Schlüssel werden nicht an das Frontend zurückgegeben
- aktive Entity-States sind unabhängig vom Registry- oder Ignorierstatus von der Registry-Bereinigung ausgeschlossen
- Diagnostics-Redaktion und bestehende Entity-/Unique-ID-Verträge bleiben unverändert

## [0.3.0-rc1] - Release Candidate

### Added

- stabiles internes Gerätemodell mit getrennter Historien- und Client-ID
- automatische Migration alter numerischer 0.2-Auswahlwerte
- Runtime-Dataclass über `ConfigEntry.runtime_data`
- Sammelaktionen für Geräteauswahl und Ignorierliste
- standardmäßig deaktivierte optionale Serverbereinigung
- optionaler separater API-Schlüssel für Serverbereinigung
- zweistufige Löschbestätigung mit dynamischem Bestätigungstext
- Teilerfolgsauswertung bei mehreren serverseitigen Löschungen
- sichere Vorfilterung der Registry-Bereinigung
- erweiterte, stärker redigierte Diagnosedaten
- vollständige deutsche und englische Texte
- Tests, Dokumentation und CI-Grundstruktur

### Changed

- „Freigegebene Geräte“ heißt verständlicher „Anzuzeigende Geräte“
- Manifest verweist auf `Seger85/home-assistant-embi`
- Credits lauten „Projekt: Seger“
- Ignorierregeln verwenden die stabile gemeldete Client-ID

### Removed

- kompletter Legacy-YAML-Setup-Pfad aus `media_player.py`
- temporäre Legacy-Warnlogik

### Fixed

- Gerätefilter nutzten in 0.2 teilweise die serverseitige `/Devices`-Historien-ID statt `ReportedDeviceId`
- erfolgreich gelöschte Geräte werden anhand ihrer stabilen Client-ID ignoriert

### Live verification

- HACS-Installation von `v0.3.0-rc1` erfolgreich
- bestehender Config Entry erhalten
- 28 Media-Player sowie Entity-IDs, Unique IDs und individuelle Namen erhalten
- Live-Wiedergabestatus und Push-Updates erfolgreich
- keine EMBi-Laufzeitfehler oder Duplicate-Unique-ID-Meldungen
- Diagnostics redigieren Zugangsdaten und Geräteidentitäten

## [0.2.0] - Produktive Baseline

- Config Flow und Reconfigure Flow
- Options Flow für Geräte, Registry-Bereinigung, Serverbereinigung und About
- Migration vorhandener Media-Player auf einen Config Entry
- Erhalt der bestehenden Entity-IDs und Unique IDs
- Deutsch/Englisch und Diagnostics
