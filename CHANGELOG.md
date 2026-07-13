# Changelog

Alle wesentlichen Änderungen an EMBi werden in dieser Datei dokumentiert. Das Projekt folgt Semantic Versioning.

## [Unreleased]

### Geplant

- vollständige Laufzeitprüfung von 0.3.0 auf einer separaten Testinstanz
- visuelle Prüfung aller Config-/Options-Flows auf iPhone, iPad und Desktop
- HACS- und Hassfest-Validierung über GitHub Actions

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
