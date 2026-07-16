# Changelog

Alle wesentlichen Änderungen an EMBi werden in dieser Datei dokumentiert. Das Projekt folgt Semantic Versioning.

## [Unreleased]

### 0.9.0 – vorbereitet für private Home-Assistant-Abnahme

#### Added

- produktorientierter Bereich **Geräte & Player**
- Gruppierung nach bekannten Emby-Benutzern
- Gruppe **Gemeinsam genutzt** mit allen bekannten Benutzern
- Gruppen **Ohne Benutzerzuordnung**, **Technische Zugriffe** und **Unklare Clients**
- verständliche Player-Zeilen mit App, Gerät, Home-Assistant-Anzeigename, vollständiger Entity-ID und Status
- Metadaten- und verhaltensbasierte Client-Klassifizierung ohne reine Produktnamen-Heuristik
- kanonische Sichtbarkeitsregeln für einzelne App-Varianten, vollständige Geräte und Benutzer
- sichtbarer Bereich für nicht eindeutig auflösbare ältere Regeln
- gemeinsamer Bereich **Bereinigung** mit weiterhin getrennten Aktionen für Emby-Serverhistorie und Home-Assistant-Player
- kontrolliertes Entfernen nicht spielender EMBi-Player aus Home Assistant
- Wiederherstellung verborgener oder entfernter Player mit anschließender Entity-Prüfung
- semantische Vorher-/Nachher-Ausgabe unter **Änderungen prüfen**
- persistente, redigierte Zusammenfassungen von Migration, Player-Entfernung und Wiederherstellung
- erweiterte aggregierte Diagnostics für Gruppen, Klassifizierung, Sichtbarkeit und Cleanup

#### Changed

- Root-Navigation besteht aus **Geräte & Player**, **Bereinigung** und bei offenem Entwurf **Änderungen prüfen**
- normale Einstellungen bleiben bis zum finalen Apply ausschließlich im Entwurf
- normales Apply benötigt keinen zusätzlichen Bestätigungsschalter und lädt höchstens einmal neu
- jede destruktive Aktion besitzt genau eine eigene abschließende Bestätigung
- `playing` und `paused` sind bei Ausblenden und Entfernen geschützt
- unklarer Wiedergabestatus arbeitet fail-safe
- deaktivierte, weiterhin gültige Home-Assistant-Entities gelten nicht als verwaist
- Serverhistorie und Home-Assistant-Player werden mit getrennten Zählern und Texten dargestellt
- README ist eine produktorientierte Einführung statt einer Versionschronik
- Manifest, Runtime, privates Testpaket und späterer Releasevertrag verwenden `0.9.0`

#### Migration

- Config Entry wird idempotent auf Schema 4 / Optionsschema 2 angehoben
- Entity-IDs, Unique IDs, individuelle Namen, Aliase, Areas, Labels und deaktivierter Zustand bleiben unverändert
- bestehende Sichtbarkeitsentscheidungen werden in exakte Player-, Geräte- und Benutzerregeln überführt
- nicht eindeutig auflösbare Regeln bleiben sichtbar erhalten
- automatische Bereinigung bleibt ein- oder ausgeschaltet wie zuvor
- exakte Alterswerte wie `364` und `365` werden nicht normalisiert
- persistenter Scheduler- und Laufstatus bleiben erhalten

#### Safety

- normales Ausblenden verändert keine Registry-Entity
- Home-Assistant-Player werden nur nach frischer Revalidierung, gespeichertem exaktem Hidden-Rule, Reload und exakter Registry-Zuordnung entfernt
- Home-Assistant-Entfernung löscht keine Emby-Serverhistorie
- Serverhistorien-Löschung entfernt keine Benutzerkonten, Medien, Bibliotheken oder Wiedergabeverläufe
- keine direkte Bearbeitung von `.storage`

## [0.3.0] – 2026-07-15

### Added

- versionierter, privater und atomarer Wartungsstatus über Home Assistants `Store`
- persistenter absoluter Scheduler mit `next_run_at`
- einmalige 120-Sekunden-Grace-Period für Erstaktivierung, überfällige Termine und rc3-Migration
- strukturierter Laufbericht mit getrennten Server-, Registry- und Schutz-Zählern
- zentraler Lock gegen parallele manuelle und automatische Läufe
- zusammenhängender Options-Flow-Entwurf mit finalem Apply und Discard
- getrennte app-spezifische und geräteweite Ignorierregeln
- sichtbare Aufbewahrung nicht eindeutig migrierbarer Ignore-Altwerte
- getrennte manuelle und automatische Alterswerte mit Presets 7, 30, 90, 180 und 365 Tage plus Custom
- unveröffentlichtes releasegleiches Testartefakt mit SHA-256 und `BUILD_COMMIT`

### Changed

- die automatische Schedulerregistrierung ist bereits während `async_setup_entry()` zulässig und verlangt noch keinen vorzeitig gesetzten `LOADED`-Status
- unmittelbar vor der automatischen Ausführung werden `LOADED`, aktueller Runtime-Bezug, Store, Cleanup-Schalter, Unload-Status, Lock und Fälligkeit erneut geprüft
- Erfolg, keine Kandidaten und erwartete Schutzfälle werden als INFO protokolliert
- Teilerfolg und unterbrochene Nachbereitung werden als WARNING protokolliert
- vollständige technische Fehler werden als ERROR protokolliert
- Persistent Notifications erscheinen nur bei Teilerfolg oder Fehler
- Folgeplanung erfolgt 24 Stunden nach Abschluss des vorherigen Laufversuchs
- ein gültiger Zukunftstermin bleibt bei Reload und Neustart unverändert
- HA-Mitbereinigung ist für neue Aktivierungen standardmäßig aus; vorhandene Werte bleiben erhalten
- Diagnostics enthalten ausschließlich aggregierte Wartungsdaten und redigierte Optionen
- HACS verwendet `zip_release: true` und `filename: embi.zip`
- Stable-Baseline für die Live-Abnahme: 29 Media-Player, keine Wartungsentity

### Removed

- zusätzliche Cleanup-Anmeldedaten neben dem normalen EMBi-Verbindungsschlüssel
- einzutippender Aktivierungssatz für die Automatik
- automatische Ignore-Regel nach einer Serverbereinigung
- gemischte `ignored_device_ids`-Liste als aktives Datenmodell
- sofortige Optionswrites und Reloads nach jeder normalen Unterseite
- unsichere Wiederaufnahme einer Registry-Nachbereitung nach Neustart

### Regression test

Der korrigierte 74-zu-69-Fall ist als Vertragstest abgebildet: fünf zulässige Serverbereinigungen, null Serverfehler, 69 verbleibende Datensätze, fünf Registry-Keys queued, null Matches, null tatsächliche Registry-Entfernungen und fünf missing.

## [0.3.0-rc3] – Finale Gerätebereinigung

- manuelle und automatische altersbasierte Bereinigung
- 120-Sekunden-Erstlauf und 24-Stunden-Rhythmus
- keine maximale Verarbeitungszahl pro Lauf
- Schutz aktiver und undatierter Datensätze
- frische `/Devices`-Revalidierung vor Registry-Nachbereitung
- aggregierte identitätsfreie Laufdiagnose

## [0.3.0-rc2] – Runtime-, Safety- und UI-Härtung

- deduplizierte Sammelaktionen
- Schutz aktiver Registry-Einträge
- Revalidierung vor Registry-Änderungen
- eindeutige Serverbereinigungs-Labels
- keine gespeicherten Zugangsdaten als Passwortfeld-Default

## [0.3.0-rc1] – Release Candidate

- stabiles Identitätsmodell
- automatische Migration alter 0.2-Auswahlwerte
- Runtime-Dataclass
- sichere Standardstellung der Serverbereinigung
- Legacy-YAML-Pfad entfernt

## [0.2.0] – Produktive Baseline

- Config Flow und Reconfigure Flow
- Options Flow
- Migration vorhandener Media-Player auf einen Config Entry
- Erhalt bestehender Entity-IDs und Unique IDs
- Deutsch/Englisch und Diagnostics
