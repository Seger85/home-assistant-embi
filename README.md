# Emby Integration - EMBi

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.7%2B-41BDF5)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5)](https://hacs.xyz/)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue)](LICENSE)

**EMBi** ist eine UI-basierte Weiterentwicklung der Home-Assistant-Integration `emby` für langjährig betriebene Emby-Server mit vielen historischen Clients.

Die Integration erhält die bekannten Media-Player-Entity-IDs, ergänzt eine kontrollierte Geräteauswahl und stellt bewusst abgesicherte Wartungsfunktionen für Home Assistant und – optional – den lokalen Emby-Server bereit.

> Projektstatus: **0.3.0-rc2 Release Candidate**. Der produktive Ausgangsstand 0.2.0 ist separat als Baseline versioniert. Vor produktiven Updates immer ein Home-Assistant-Backup erstellen.

## Warum EMBi?

Emby-Server behalten häufig historische Geräte- und App-Einträge: ersetzte Fernseher, alte Mobilgeräte, Browser-Sitzungen, mehrfach registrierte Apps oder administrative API-Clients. Die normale Emby-Integration kann daraus dauerhaft viele Media-Player erzeugen.

EMBi setzt an der Quelle der Entity-Erzeugung an:

- vollständige Einrichtung über Config Flow und Options Flow
- stabile Übernahme vorhandener Media-Player-Entity-IDs
- Anzeige aller, nur aktiver oder gezielt ausgewählter Clients
- Ignorierliste mit Vorrang vor allen anderen Regeln
- sichere, deduplizierte Sammelaktionen für Geräteauswahl und Ignorierliste
- kontrollierte Bereinigung ausschließlich inaktiver, unmittelbar erneut geprüfter Entity-Registry-Altlasten
- optionale, standardmäßig ausgeschaltete Bereinigung historischer Emby-Geräte mit eindeutig beschrifteten Datensätzen
- separater zweiter Bestätigungsschritt vor serverseitigen Löschungen
- Teilerfolgsauswertung bei mehreren Löschungen
- Deutsch und Englisch
- datenschutzbewusste Diagnosedaten
- HACS-kompatible Repository-Struktur

## Zentrale Sicherheitsentscheidung

Emby liefert für einen historischen Geräte-Eintrag zwei unterschiedliche IDs:

- `Id`: serverseitiger Historieneintrag; ausschließlich für `DELETE /Devices`
- `ReportedDeviceId`: tatsächliche Client-Identität; Grundlage der pyemby- und Home-Assistant-Unique-ID

EMBi 0.3 trennt diese IDs konsequent. Dadurch funktioniert die Geräteauswahl stabil, ohne bestehende Entity-IDs zu verändern.

## Installation

### HACS Custom Repository

1. In HACS **Benutzerdefinierte Repositories** öffnen.
2. `Seger85/home-assistant-embi` als Kategorie **Integration** hinzufügen.
3. **Emby Integration - EMBi** installieren.
4. Home Assistant neu starten.
5. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach EMBi suchen.

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

### Geräte auf dem Emby-Server löschen

Diese Funktion ist standardmäßig deaktiviert und muss zuerst ausdrücklich eingeschaltet werden. Optional kann ein separater API-Schlüssel hinterlegt werden; ohne separaten Schlüssel wird der normale Verbindungsschlüssel verwendet. Gespeicherte Schlüssel werden in Passwortfeldern nie als Standardwert zurückgegeben.

Historische Datensätze werden mit Gerätename, App, App-Version, letzter Aktivität und kurzer Datensatz-ID eindeutig beschriftet.

Vor jeder Löschung sind erforderlich:

- konkrete Mehrfachauswahl
- separater Bestätigungsschritt
- aktivierter Bestätigungsschalter
- exakter Text `LÖSCHEN <Anzahl>` bzw. `DELETE <count>`

Eine erneute Nutzung des Clients kann ihn später wieder auf dem Emby-Server registrieren.

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
- „Alle auswählen“ wird über kontrollierte Sammelaktionen umgesetzt, da der native Mehrfachselektor keine verlässliche universelle Alles-auswählen-Schaltfläche bereitstellt.
- Die serverseitige Löschberechtigung ist von den Rechten des verwendeten Emby-API-Schlüssels abhängig.
- Ein gelöschter Client kann sich bei späterer Nutzung erneut registrieren.

## Herkunft und Lizenz

EMBi basiert auf der Home-Assistant-Core-Integration `emby` und `pyemby`. Das Projekt steht unter der Apache License 2.0. Siehe [LICENSE](LICENSE) und [NOTICE.md](NOTICE.md).

---

## English summary

EMBi is a Config-Flow-based enhancement of Home Assistant's Emby integration. It preserves existing media-player identities, adds stable client filtering, guarded entity-registry cleanup, and an optional two-step cleanup of historical records on the local Emby server. Full English UI translations are included.
