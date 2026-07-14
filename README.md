# Emby Integration - EMBi

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.7%2B-41BDF5)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5)](https://hacs.xyz/)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue)](LICENSE)

**EMBi** ist eine UI-basierte Weiterentwicklung der Home-Assistant-Integration `emby` für langjährig betriebene Emby-Server mit vielen historischen Clients.

Die Integration erhält bekannte Media-Player-Entity-IDs, ergänzt eine kontrollierte Geräteauswahl und stellt bewusst abgesicherte Wartungsfunktionen für Home Assistant und den lokalen Emby-Server bereit.

> Projektstatus: **0.3.0-rc3 Release Candidate**. `v0.3.0-rc2` bleibt unverändert veröffentlicht; rc3 ergänzt die finale manuelle und automatische Gerätebereinigung. Vor produktiven Updates immer ein Home-Assistant- und Emby-Backup erstellen.

## Warum EMBi?

Emby-Server behalten häufig historische Geräte- und App-Einträge: ersetzte Fernseher, alte Mobilgeräte, Browser-Sitzungen, mehrfach registrierte Apps oder administrative API-Clients. Die normale Emby-Integration kann daraus dauerhaft viele Media-Player erzeugen.

EMBi setzt an der Quelle der Entity-Erzeugung und an der Gerätehistorie an:

- vollständige Einrichtung über Config Flow und Options Flow
- stabile Übernahme vorhandener Media-Player-Entity-IDs
- Anzeige aller, nur aktiver oder gezielt ausgewählter Clients
- Ignorierliste mit Vorrang vor allen anderen Regeln
- sichere, deduplizierte Sammelaktionen
- kontrollierte Registry-Bereinigung
- manuelle altersbasierte Bereinigung historischer Emby-Geräte
- separat und ausdrücklich aktivierte automatische Gerätebereinigung
- Standard-Altersfilter: älter als 365 Tage
- erster automatischer Lauf 120 Sekunden nach der bewussten Erstaktivierung, danach alle 24 Stunden
- bewusst keine maximale Löschzahl pro automatischem Lauf
- aktive Player und Datensätze ohne gültigen Aktivitätszeitpunkt werden übersprungen
- optionales Entfernen des zugehörigen HA-Media-Players nach erfolgreicher Serverlöschung und erneuter Sicherheitsprüfung
- Deutsch und Englisch
- datenschutzbewusste Diagnosedaten
- HACS-kompatible Repository-Struktur

## Zentrale Sicherheitsentscheidung

Emby liefert für einen historischen Geräte-Eintrag unterschiedliche Identitäten:

- `Id`: serverseitiger Historieneintrag; ausschließlich für `DELETE /Devices`
- `ReportedDeviceId`: stabile Client-Identität; Grundlage einer geräteweiten Ignorierregel
- `ReportedDeviceId.AppName`: konkrete Client-/App-Kombination; pyemby- und Home-Assistant-Unique-ID

EMBi verändert vorhandene Unique IDs nicht. Ein HA-Registry-Eintrag wird nach einer Serverlöschung nur vorgemerkt, wenn kein verbleibender `/Devices`-Datensatz dieselbe `ReportedDeviceId.AppName`-Identität verwendet. Die tatsächliche Entfernung erfolgt während eines kontrollierten Config-Entry-Reloads und nur ohne vorhandenen Entity-State.

## Installation

### HACS Custom Repository

1. In HACS **Benutzerdefinierte Repositories** öffnen.
2. `Seger85/home-assistant-embi` als Kategorie **Integration** hinzufügen.
3. **Emby Integration - EMBi** installieren.
4. Home Assistant neu starten.
5. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach EMBi suchen.

Für Release Candidates muss die Anzeige von Beta-/Vorabversionen in HACS aktiviert sein.

### Manuell

Den Ordner `custom_components/emby` nach `/config/custom_components/emby` kopieren und Home Assistant neu starten.

Da EMBi die eingebaute Domain `emby` ersetzt, darf nicht gleichzeitig eine andere Custom Component mit derselben Domain installiert sein.

## Migration von der Core-/YAML-Integration

Die sichere Reihenfolge ist:

1. vollständiges Home-Assistant-Backup erstellen
2. EMBi installieren und neu starten
3. UI-Config-Entry mit demselben Emby-Server anlegen
4. vorhandene Entity-IDs und Wiedergabestatus prüfen
5. ausschließlich den alten YAML-Block `media_player: - platform: emby` entfernen
6. Konfiguration validieren und neu starten
7. prüfen, dass keine Duplicate-Unique-ID- oder Legacy-YAML-Meldungen mehr erscheinen

Separat konfigurierte REST-Sensoren und Templates werden dadurch nicht entfernt. Details stehen in [docs/migration-from-core.md](docs/migration-from-core.md).

## Gerätefilter

### Alle Geräte anzeigen

Kompatibles Standardverhalten. Jeder von pyemby gemeldete Client kann als Media-Player angelegt werden.

### Nur aktive Wiedergaben

Ein Client wird nur während `playing` oder `paused` angeboten. Im Leerlauf wird seine Entität nicht als verfügbar geführt.

### Nur ausgewählte Geräte

Nur die unter **Anzuzeigende Geräte** ausgewählten stabilen Client-/App-Kombinationen werden angelegt.

### Ignorierte Geräte

Die Ignorierliste hat immer Vorrang. Eine rohe `ReportedDeviceId` ignoriert alle App-Varianten desselben Clients.

## Wartungsfunktionen

### Home-Assistant-Einträge bereinigen

EMBi bietet nur inaktive, unmittelbar vor dem Entfernen erneut geprüfte Kandidaten an:

- alte YAML-Einträge ohne aktiven State
- reine Registry-Einträge ohne aktiven State
- bereits durch EMBi ignorierte Entitäten ohne aktiven State

Aktive alte YAML-, ignorierte und normale Media-Player werden bewusst nicht angeboten.

### Manuelle Emby-Serverbereinigung

1. Serverbereinigung ausdrücklich aktivieren.
2. Altersfilter wählen; Standard: älter als 365 Tage.
3. Aus den gefilterten Historieneinträgen konkrete Datensätze auswählen.
4. Optional Client geräteweit ignorieren und/oder zugehörigen HA-Player entfernen lassen.
5. Löschung in einem zweiten Schritt mit Schalter und exaktem Bestätigungstext bestätigen.

Aktive Player und Datensätze ohne gültigen Aktivitätszeitpunkt werden nicht angeboten. Jeder ausgewählte Datensatz wird unabhängig verarbeitet.

### Automatische Emby-Serverbereinigung

Die Automatik besitzt einen separaten Schalter und ist standardmäßig deaktiviert. Die erstmalige Aktivierung benötigt einen Warnschalter und den exakten Aktivierungstext.

Nach Aktivierung gilt:

- erster Lauf nach 120 Sekunden
- weitere Läufe alle 24 Stunden
- Standard-Altersfilter 365 Tage
- alle zulässigen Datensätze werden verarbeitet; keine maximale Löschzahl
- aktive Player werden übersprungen
- Datensätze ohne verwertbaren Aktivitätszeitpunkt werden übersprungen
- Fehler eines Datensatzes stoppen die übrigen Löschungen nicht
- HA-Registry-Einträge werden nur nach erfolgreicher Serverlöschung, frischer `/Devices`-Abfrage und kontrolliertem Reload entfernt

Eine spätere Nutzung eines gelöschten Clients kann ihn erneut auf dem Emby-Server registrieren.

## Dokumentation

- [Architektur](docs/architecture.md)
- [Konfiguration und Gerätefilter](docs/configuration.md)
- [Migration](docs/migration-from-core.md)
- [Serverbereinigung](docs/server-cleanup.md)
- [Sicherheit](docs/security.md)
- [Fehleranalyse](docs/troubleshooting.md)
- [Entwicklung](docs/development.md)
- [Visuelle Qualitätssicherung](docs/ui-qa.md)
- [Release-Checkliste](docs/release-checklist.md)
- [Roadmap](ROADMAP.md)

## Bekannte Einschränkungen

- Die Darstellung nativer Home-Assistant-Selektoren wird durch das aktive Frontend-Theme bestimmt. EMBi injiziert bewusst kein fragiles Config-Flow-CSS.
- Die serverseitige Löschberechtigung hängt vom verwendeten Emby-API-Schlüssel ab.
- Eine serverseitige Löschung ist nur über ein Emby-Backup vollständig rückgängig zu machen.
- Ein gelöschter Client kann sich bei späterer Nutzung erneut registrieren und wieder als Media-Player erscheinen.

## Herkunft und Lizenz

EMBi basiert auf der Home-Assistant-Core-Integration `emby` und `pyemby`. Das Projekt steht unter der Apache License 2.0. Siehe [LICENSE](LICENSE) und [NOTICE.md](NOTICE.md).

---

## English summary

EMBi is a Config-Flow-based enhancement of Home Assistant's Emby integration. It preserves existing media-player identities and adds stable client filtering, guarded registry cleanup, manual age-filtered server maintenance, and an explicitly enabled automatic cleanup. Automatic cleanup starts after 120 seconds, then runs every 24 hours, has no per-run deletion cap, skips active/undated records, and removes a matching HA registry entry only after post-delete server revalidation and a safe reload.
