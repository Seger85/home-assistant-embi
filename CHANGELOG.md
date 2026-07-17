# Changelog

Alle wesentlichen Änderungen an EMBi werden in dieser Datei dokumentiert. Das Projekt folgt Semantic Versioning.

## [0.9.1] – 2026-07-17

### UX

- neues Hauptmenü mit **Home-Assistant-Player**, **Emby-Server bereinigen** und nur bei offenem Entwurf **Änderungen prüfen**
- verlässliche Zurück-Navigation, die den aktuellen Entwurf erhält; `X` schließt weiterhin ausschließlich den gesamten Dialog
- normale Verbindungs-, Auswahl- und Entwurfsfehler bleiben als Inline-Fehler auf der aktuellen Seite
- kurze Player-Auswahltexte aus Gerät und App, Benutzer nur bei notwendiger Unterscheidung
- Benutzer- und Clientgruppen als kompakte Navigation mit Playeranzahl
- einzelne Player ausschließlich unter **Ausnahmen verwalten**, mit Suche und Seiten zu höchstens zwölf Einträgen
- technische Entity- und Statusangaben ausschließlich in der Detailansicht
- automatische Bereinigung, manuelle Prüfung und letzter Lauf als getrennte Unterseiten
- benutzerdefinierte Altersangabe nur bei Auswahl von **Benutzerdefiniert**
- Vorschau und genau eine eindeutig bezeichnete Ausführung für Server- und Home-Assistant-Bereinigung
- vollständig lokalisierte Lauf- und Playerstatus sowie korrekte Singular-/Pluralanzeige für Änderungen

### Safety und Migration

- Entity-IDs, Unique IDs, Namen, Aliase, Areas, Labels und Registry-Aktivierungszustand bleiben unverändert
- Migration von 0.9.0 bleibt idempotent und erhält effektive Sichtbarkeit, automatische Bereinigung und exakte Alterswerte
- `playing` und `paused` bleiben strikt geschützt
- Registry-Player mit aktuellem Emby-Datensatz werden als Wiedergabe-Client-Kandidaten eingeordnet
- Registry-Einträge ohne aktuellen Emby-Datensatz heißen **Nicht mehr vom Emby-Server gemeldet**; der Begriff `orphan` wird dafür nicht verwendet
- keine automatische Ausblendung oder Löschung aufgrund der verfeinerten Klassifizierung

## [0.9.0]

### Added

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

### Changed

- Root-Navigation besteht aus **Geräte & Player**, **Bereinigung** und bei offenem Entwurf **Änderungen prüfen**
- normale Einstellungen bleiben bis zum finalen Apply ausschließlich im Entwurf
- normales Apply benötigt keinen zusätzlichen Bestätigungsschalter und lädt höchstens einmal neu
- jede destruktive Aktion besitzt genau eine eigene abschließende Bestätigung
- `playing` und `paused` sind bei Ausblenden und Entfernen geschützt
- unklarer Wiedergabestatus arbeitet fail-safe
- deaktivierte, weiterhin gültige Home-Assistant-Entities gelten nicht als verwaist
- Serverhistorie und Home-Assistant-Player werden mit getrennten Zählern und Texten dargestellt
- README ist eine produktorientierte Einführung statt einer Versionschronik
- Manifest, Runtime und Paketvertrag verwenden `0.9.0`

### Migration

- Config Entry wird idempotent auf Schema 4 / Optionsschema 2 angehoben
- Entity-IDs, Unique IDs, individuelle Namen, Aliase, Areas, Labels und deaktivierter Zustand bleiben unverändert
- bestehende Sichtbarkeitsentscheidungen werden in exakte Player-, Geräte- und Benutzerregeln überführt
- nicht eindeutig auflösbare Regeln bleiben sichtbar erhalten
- automatische Bereinigung bleibt ein- oder ausgeschaltet wie zuvor
- exakte Alterswerte wie `364` und `365` werden nicht normalisiert
- persistenter Scheduler- und Laufstatus bleiben erhalten

### Safety

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
