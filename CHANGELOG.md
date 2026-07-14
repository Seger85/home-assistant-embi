# Changelog

Alle wesentlichen Änderungen an EMBi werden in dieser Datei dokumentiert. Das Projekt folgt Semantic Versioning.

## [Unreleased]

### Geplant

- Live-Upgrade und UI-Prüfung von 0.3.0-rc2 in Home Assistant
- kontrollierte Prüfung der Registry- und Serverbereinigungsdialoge ohne unbeabsichtigte Löschung
- Entscheidung über einen weiteren Release Candidate oder die stabile 0.3.0

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

- Gerätefilter nutzten in 0.2 fälschlich die serverseitige `/Devices`-Historien-ID statt `ReportedDeviceId`; dadurch konnten Auswahl- und Ignorierregeln die tatsächlichen pyemby-Unique-IDs verfehlen
- erfolgreich gelöschte Geräte werden anhand ihrer stabilen Client-ID ignoriert, nicht anhand der nur für den Löschendpunkt gültigen Historien-ID

## [0.2.0] - Produktive Baseline

- Config Flow und Reconfigure Flow
- Options Flow für Geräte, Registry-Bereinigung, Serverbereinigung und About
- Migration vorhandener Media-Player auf einen Config Entry
- Erhalt der bestehenden Entity-IDs und Unique IDs
- Deutsch/Englisch und Diagnostics
- temporäre Legacy-YAML-Unterstützung für die kontrollierte Migration
