# EMBi – Emby in Home Assistant, ohne Gerätefriedhof

**EMBi ist die Emby-Integration für alle, die irgendwann mehr Geräte in der Liste haben als im Haus.**

Sie verbindet deinen lokalen Emby-Server mit Home Assistant, übernimmt vorhandene Media-Player und gibt dir eine verständliche Oberfläche für Benutzer, gemeinsam genutzte Geräte, alte Clients und technische Zugriffe.

Kurz gesagt:

**weniger Gerätechaos, mehr Kontrolle – mit Sicherheitsprüfungen vor jeder Löschung.**

## Was EMBi anders macht

Die normale Emby-Gerätehistorie wächst mit der Zeit. Alte Fernseher, Browser-Sitzungen, Mobilgeräte, doppelte App-Varianten und API-Anwendungen bleiben häufig lange sichtbar. EMBi trennt diese Informationen sauber:

- **Emby-Server-Gerätehistorie** – historische Datensätze auf dem Emby-Server
- **Home-Assistant-Player** – tatsächlich verwaltete `media_player`-Entities
- **Sichtbarkeitsregeln** – welche Player EMBi aktuell in Home Assistant bereitstellt

Dadurch ist jederzeit klar, ob du nur einen Player ausblendest, eine Home-Assistant-Entity entfernst oder einen historischen Servereintrag löschst.

## Geräte & Player

Der Bereich **Geräte & Player** zeigt verständliche Informationen statt interner Emby-IDs:

- App und Gerät
- zugeordnete Emby-Benutzer
- Home-Assistant-Anzeigename
- vollständige Entity-ID
- aktueller Status

### Nach Benutzern gruppiert

Bekannte Emby-Benutzer stehen zuerst. Beispiel:

- **Alex**
  - Emby TV · Wohnzimmer
  - Emby Mobile · Smartphone
- **Sam**
  - Emby Web · Notebook

### Gemeinsam genutzte Geräte

Ein Gerät mit mehreren bekannten Benutzern erscheint unter **Gemeinsam genutzt**. EMBi nennt dabei alle bekannten Benutzer, zum Beispiel:

> Emby TV · Wohnzimmer · Alex, Sam

### Ohne Benutzerzuordnung

Wiedergabegeräte ohne verlässliche Benutzerinformation bleiben sichtbar unter **Ohne Benutzerzuordnung**. EMBi erfindet keine Zuordnung.

### Technische Zugriffe und unklare Clients

EMBi erkennt technische Zugriffe nur anhand eindeutiger Metadaten oder nachvollziehbaren Verhaltens – nicht allein anhand eines Produktnamens.

- bestätigte API- oder Integrationszugriffe: **Technische Zugriffe**
- nicht sicher einzuordnende Clients: **Unklare Clients**

Unklare Clients werden nicht automatisch als technische Zugriffe behandelt.

## Sichtbarkeit steuern

Du kannst festlegen:

- ob Player dauerhaft oder nur während Wiedergabe/Pause angezeigt werden
- ob neue Player automatisch erscheinen
- ob technische Zugriffe als Home-Assistant-Player sichtbar sind
- welche einzelnen App-Varianten verborgen bleiben
- welche Geräte mit allen App-Varianten verborgen bleiben
- ob alle ausschließlich einem Benutzer zugeordneten Player sichtbar sind

Normale Änderungen werden zunächst nur als Entwurf gesammelt. Unter **Änderungen prüfen** siehst du verständliche Vorher-/Nachher-Angaben. Erst **Änderungen übernehmen** speichert den Entwurf und lädt die Integration höchstens einmal neu.

## Bereinigung

Der gemeinsame Bereich **Bereinigung** enthält zwei bewusst getrennte Aufgaben.

### Alte Emby-Server-Einträge

Die manuelle oder automatische Serverbereinigung arbeitet mit einer exakten Altersgrenze. Werte wie `364` oder `365` Tage bleiben unverändert erhalten.

Vor einer Löschung prüft EMBi unter anderem:

- der Eintrag ist strikt älter als die gewählte Grenze
- es liegt ein gültiger Aktivitätszeitpunkt vor
- der zugehörige Player spielt nicht und ist nicht pausiert
- die Auswahl wurde unmittelbar vor der Aktion erneut validiert

Eine Serverlöschung verändert nicht automatisch deine Sichtbarkeitsregeln.

### Home-Assistant-Player entfernen

Nicht spielende EMBi-Player können unabhängig von der Serverhistorie aus Home Assistant entfernt werden.

EMBi führt dafür eine kontrollierte Transaktion aus:

1. aktuelle Emby- und Home-Assistant-Daten neu laden
2. `playing` und `paused` blockieren
3. exakte Sichtbarkeitsregel speichern
4. Integration neu laden
5. nur die eindeutig zugehörige Registry-Entity entfernen
6. erneut laden und prüfen, dass sie nicht zurückkehrt

Ein deaktivierter, aber weiterhin gültiger Home-Assistant-Player ist **kein verwaister Eintrag** und wird entsprechend behandelt.

## Player wiederherstellen

Ein zuvor verborgener oder entfernter Player kann unter **Geräte & Player** wieder eingeblendet werden.

Beispiel:

1. Emby TV · Schlafzimmer wurde aus Home Assistant entfernt.
2. Der historische Emby-Datensatz blieb erhalten.
3. Du aktivierst den Player wieder im Entwurf.
4. EMBi lädt die Integration neu und prüft die resultierende Entity.

Bei einer neu angelegten Entity können Home Assistant, Dashboards, Automationen, HomeKit oder Siri eine erneute Zuordnung benötigen. EMBi zeigt deshalb bei destruktiven Aktionen genau eine abschließende Warnung.

## Installation über HACS

1. HACS öffnen.
2. EMBi als benutzerdefiniertes Integrations-Repository hinzufügen.
3. Die aktuelle stabile Version installieren.
4. Home Assistant neu starten.
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Emby Integration - EMBi** öffnen.
6. Host, Port, HTTPS-Einstellung und Emby-API-Schlüssel eintragen.

Das Releasepaket heißt `embi.zip`. Der veröffentlichte SHA-256-Wert steht im Asset `embi.zip.sha256`.

## Upgrade von 0.3.0

Die Migration auf 0.9.0 ist idempotent und erhält insbesondere:

- Config-Entry-ID
- Entity-IDs und Unique IDs
- individuelle Namen
- Aliase, Areas und Labels
- deaktivierten Zustand gültiger Entities
- bestehende Sichtbarkeitsentscheidungen
- automatische Bereinigung ein oder aus
- exakte Alterswerte wie `364` und `365`
- bestehenden Scheduler- und Laufstatus

Nicht eindeutig auflösbare ältere Regeln werden nicht still gelöscht. Sie erscheinen in einem eigenen Abschnitt **Ältere Regeln**.

Vor dem Upgrade empfiehlt sich ein vollständiges Home-Assistant-Backup. Direkte Änderungen an `.storage`-Dateien sind weder erforderlich noch unterstützt.

## Datenschutz und Diagnosen

EMBi arbeitet lokal mit deinem Emby-Server. Diagnosedaten enthalten aggregierte Zähler und kategorisierte Statusinformationen, aber keine API-Schlüssel, vollständigen Geräte-IDs, Player-Keys oder Benutzernamen.

## Sicherheit

- ausschließlich unterstützte Home-Assistant-APIs
- keine direkte `.storage`-Bearbeitung
- exakte Registry-Zuordnung nach Domain, Plattform, Config Entry und Unique ID
- erneute Prüfung unmittelbar vor destruktiven Aktionen
- ein gemeinsamer Lock gegen parallele manuelle und automatische Läufe
- keine automatische Wiederholung unsicherer DELETE-Aufrufe
- genau eine abschließende Bestätigung pro destruktiver Aktion

## Dokumentation

- [Konfiguration](docs/configuration.md)
- [Bereinigung](docs/server-cleanup.md)
- [Architektur](docs/architecture.md)
- [Sicherheit](docs/security.md)
- [Fehlerbehebung](docs/troubleshooting.md)
- [UI-Qualitätssicherung](docs/ui-qa.md)
- [Roadmap](ROADMAP.md)

## Credits

- **Projekt:** Seger
- **Basis:** Home Assistant Emby und pyemby

Lizenz: Apache-2.0
