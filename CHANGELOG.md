# Changelog

Alle wesentlichen Änderungen an EMBi werden in dieser Datei dokumentiert. Das Projekt folgt Semantic Versioning.

## [Unreleased]

### Added

- automatisierter Release-Workflow mit Tag-/Manifest-Abgleich
- automatische Unterscheidung von Prerelease und stabilem Release
- Release-Archiv `embi.zip` und SHA-256-Prüfsumme
- dokumentierte Repository-, Branch- und Release-Governance
- eindeutige CI-Checknamen für spätere GitHub-Rulesets

### Changed

- Dependabot-PRs zielen künftig auf `develop`
- Projektstatus und Roadmap dokumentieren den erfolgreichen 0.3.0-rc1-Livetest
- Release-Veröffentlichung wird erst nach Quality, HACS und Hassfest ausgeführt

### Fixed

- nicht destruktive Synchronisierung von `main` zurück nach `develop` nach dem vorzeitigen Merge von PR #1
- dokumentierte Abgrenzung zwischen einer veröffentlichten EMBi-Version und einem neueren Repository-Commit in HACS

### Remaining

- vollständige Options-Flow- und Screenshot-QA
- kontrollierter Server-Cleanup-Sicherheitstest
- GitHub-Rulesets für `main` und `develop`
- stabile Releaseentscheidung für 0.3.0

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
- temporäre Legacy-YAML-Unterstützung für die kontrollierte Migration
