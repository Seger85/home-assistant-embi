# EMBi – Emby in Home Assistant, ohne Gerätefriedhof

**EMBi verbindet einen lokalen Emby-Server mit Home Assistant und trennt dabei Player-Sichtbarkeit, Home-Assistant-Entities und historische Emby-Servereinträge sauber voneinander.**

## Home-Assistant-Player

Der Bereich **Home-Assistant-Player** enthält ausschließlich die globalen Schalter und die Gruppenauswahl:

- Player nur während Wiedergabe oder Pause anzeigen
- neue Player automatisch hinzufügen
- technische Zugriffe als Player anzeigen
- Gruppe öffnen

Innerhalb einer Gruppe besitzt jeder Player einen direkten Ein-/Aus-Schalter. Die Zeilen bleiben kompakt:

> Wohnzimmer · Emby TV  
> Zuletzt: 18.07.2026 14:30

Bekannte Zugriffe sind immer **älteste zuerst** sortiert. Unbekannte Zeitpunkte stehen am Ende. Suchfeld und Sortierauswahl gibt es nicht mehr.

Laufende, pausierte und nicht eindeutig bewertbare Player bleiben geschützt. Ein sicher inaktiver, ausgeschalteter Player wird erst nach **Änderungen prüfen → Änderungen übernehmen** aus der Home-Assistant-Registry entfernt. Der Emby-Servereintrag bleibt dabei bestehen und der Player kann über EMBi wiederhergestellt werden.

## Entwurf und Navigation

Nicht destruktive Unterseiten verwenden den normalen Home-Assistant-OK-Submit:

- OK übernimmt sichtbare Werte nur in den In-Memory-Entwurf und führt eine Ebene zurück.
- **Änderungen prüfen** zeigt den semantischen Unterschied zum gespeicherten Stand.
- **Änderungen übernehmen** speichert genau einmal und schließt den Options Flow sofort.
- Reload, Registry-Abgleich und gegebenenfalls sofort fällige automatische Bereinigung laufen anschließend als nachgelagerter Task.
- **Änderungen verwerfen** verwirft den Entwurf.
- Schließen über **X** speichert nichts.

## Direkte Hauptnavigation

1. **Home-Assistant-Player**
2. **Automatische Serverbereinigung**
3. **Einzelne Emby-Servereinträge löschen**
4. **Änderungen prüfen** – nur bei offenem Entwurf

Ein zusätzliches Bereinigungs-Zwischenmenü gibt es nicht mehr.

## Automatische Serverbereinigung

Die automatische Bereinigung behält die vorhandene Altersgrenze, Zeitplanung und Sicherheitslogik. Auf derselben Seite stehen:

- letzter Lauf und Modus
- verwendete Altersgrenze
- gelöschte, geschützte und fehlgeschlagene Einträge
- nächster geplanter Lauf

Änderungen werden auch hier zunächst nur in den Entwurf übernommen.

## Einzelne Emby-Servereinträge löschen

Die manuelle Auswahl zeigt immer alle eindeutig sicheren inaktiven Servereinträge **unabhängig vom Alter** und fest **älteste zuerst**. Es gibt keine manuelle Altersgrenze und keinen Scope-Selektor. Die automatische Altersgrenze bleibt unverändert.

Geschützt bleiben:

- `playing`
- `paused`
- unklare Wiedergabe- oder Identitätszustände
- Einträge ohne verlässlichen Aktivitätszeitpunkt

Nach Auswahl folgen Vorschau und eindeutige Bestätigung. Erst nach erfolgreicher Serverlöschung darf eine exakt zugeordnete Home-Assistant-Entity entfernt werden. Config Entry, Domain, Plattform, Entity-ID, Unique-ID, verbleibende Serverhistorie und Wiedergabestatus werden frisch geprüft. Eine pauschale Registry-Bereinigung findet nicht statt.

## Installation über HACS

1. HACS öffnen.
2. `Seger85/home-assistant-embi` als benutzerdefiniertes Integrations-Repository hinzufügen.
3. **Emby Integration - EMBi** installieren oder aktualisieren.
4. Home Assistant neu starten.
5. EMBi unter **Einstellungen → Geräte & Dienste** konfigurieren.

EMBi wird ausschließlich über reguläre GitHub-Releases bereitgestellt. Das HACS-Paket heißt `embi.zip`; die Prüfsumme liegt in `embi.zip.sha256`.

## Upgrade auf 0.9.7

Die Migration erhält:

- Config Entry und Verbindung
- bestehende Entity-IDs und Unique-IDs
- individuelle Namen, Aliase, Areas und Labels
- deaktivierten Registry-Zustand
- bestehende Sichtbarkeitsregeln
- automatische Bereinigung einschließlich exakter Alterswerte
- Scheduler- und Laufstatus

Die bisherige manuelle Altersoption bleibt migrationssicher in gespeicherten Optionen erhalten, wird aber nicht mehr als UI-Steuerung verwendet. Vor dem Update bleibt ein vollständiges Home-Assistant-Backup empfohlen. Direkte Änderungen an `.storage` sind nicht erforderlich und nicht unterstützt.

## Dokumentation

- [Konfiguration](docs/configuration.md)
- [Serverbereinigung](docs/server-cleanup.md)
- [Architektur](docs/architecture.md)
- [Sicherheit](docs/security.md)
- [Fehlerbehebung](docs/troubleshooting.md)
- [UI-Qualitätssicherung](docs/ui-qa.md)

## Credits

- **Projekt:** Seger
- **Basis:** Home Assistant Emby und pyemby

Lizenz: Apache-2.0
