# EMBi – Emby in Home Assistant, ohne Gerätefriedhof

**EMBi ist die Emby-Integration für alle, die irgendwann mehr Geräte in der Liste haben als im Haus.**

Sie verbindet deinen lokalen Emby-Server mit Home Assistant, übernimmt bestehende Media-Player und gibt dir Kontrolle über sichtbare Player, historische Servereinträge und technische Zugriffe.

Kurz gesagt: **weniger Gerätechaos, mehr Kontrolle – mit Sicherheitsprüfungen vor jeder dauerhaften Aktion.**

## Was EMBi trennt

EMBi behandelt drei Dinge bewusst getrennt:

- **Emby-Serverhistorie:** historische Gerätedatensätze auf dem Emby-Server
- **Home-Assistant-Player:** registrierte `media_player`-Entities
- **Sichtbarkeitsregeln:** welche Player EMBi bereitstellt oder verborgen hält

Dadurch ist klar, ob du nur eine App-Variante ausblendest, einen Home-Assistant-Player entfernst oder einen alten Serverdatensatz löschst.

## Home-Assistant-Player

Der Bereich **Home-Assistant-Player** beginnt mit den globalen Einstellungen:

- Player nur während Wiedergabe oder Pause anzeigen
- neue Player automatisch hinzufügen
- technische Zugriffe als Player anzeigen

Danach navigierst du über kurze Gruppen mit Anzahl:

- bekannte Emby-Benutzer
- **Gemeinsam genutzt** für Geräte mit mehreren bekannten Benutzern
- **Ohne Benutzerzuordnung**
- **Technische Zugriffe**
- **Unklare Clients**

Normale Playerzeilen bleiben kompakt, beispielsweise:

> Wohnzimmer · Emby TV

Interne Schlüssel, Unique IDs und Rohstatus erscheinen nicht in Auswahlfeldern. Home-Assistant-Anzeigename, Entity-ID und weitere technische Angaben stehen nur in der Detailansicht.

### Benutzergruppen und direkte Player-Schalter

Innerhalb einer Benutzer- oder Clientgruppe besitzt jeder Player direkt einen Ein-/Aus-Schalter. Damit lassen sich einzelne Player ohne zusätzliche Ausnahmenseite ein- oder ausblenden.

Der Gruppenstatus wird aus den gewählten Playern abgeleitet. Laufende und pausierte Wiedergaben bleiben geschützt. Optional kann weiterhin eine technische Detailansicht für einen einzelnen Player geöffnet werden.

## Änderungen prüfen

Normale Einstellungen werden zunächst nur im geöffneten Dialog gesammelt.

- **‹ Zurück** wechselt die Seite und behält den Entwurf.
- **Änderungen prüfen** zeigt eine verständliche Zusammenfassung.
- **Änderungen übernehmen** schreibt genau einmal, lädt EMBi höchstens einmal neu und führt anschließend sichtbar zur Hauptseite zurück.
- Eine Bestätigung auf der Hauptseite zeigt, dass die Einstellungen gespeichert und EMBi neu geladen wurden.
- **Änderungen verwerfen** setzt den Entwurf ohne Speicherung zurück.
- Schließen über **X** speichert nichts.

Normale Fehler bleiben als Hinweis auf der aktuellen Seite. Sie beenden den Options Flow nicht.

## Emby-Server bereinigen

Der Bereich **Emby-Server bereinigen** enthält:

1. **Automatische Bereinigung**
2. **Jetzt auf alte Einträge prüfen**
3. **Letzter Bereinigungslauf**
4. **‹ Zurück**

Manuelle und automatische Altersgrenzen bleiben getrennt. Die Presets 7, 30, 90, 180 und 365 Tage sowie benutzerdefinierte Werte werden unterstützt. Bestehende exakte Werte wie `364` bleiben unverändert.

### Automatische Bereinigung

Die automatische Bereinigung hält immer an der gespeicherten Altersgrenze fest. Nach dem Aktivieren registriert EMBi den persistenten Scheduler und führt einen fälligen ersten Lauf nach einer kurzen Grace Period aus. Weitere Läufe werden jeweils 24 Stunden nach Abschluss des vorherigen Laufversuchs geplant.

### Manuelle Bereinigung

Bei der manuellen Prüfung stehen zwei Geltungsbereiche zur Verfügung:

- **Nur Einträge außerhalb der Altersgrenze**
- **Alle sicheren Einträge – unabhängig vom Alter**

Damit können bewusst auch jüngere historische Datensätze ausgewählt werden, ohne die automatische Altersregel zu verändern.

Vor jeder Serverlöschung prüft EMBi erneut:

- der Datensatz gehört weiterhin eindeutig zum ausgewählten Servereintrag
- ein gültiger Aktivitätszeitpunkt ist vorhanden
- der zugehörige Player spielt nicht und ist nicht pausiert
- Server, Config Entry, Plattform und Identität sind weiterhin eindeutig
- bei automatischen Läufen und manueller Altersprüfung ist die konfigurierte Altersgrenze erfüllt

Die Kandidatenauswahl ist die Vorschau. Danach folgt genau eine eindeutig bezeichnete Ausführung, beispielsweise **3 Emby-Einträge löschen**.

Eine Serverlöschung ändert Sichtbarkeitsregeln nicht automatisch.

## Home-Assistant-Player entfernen

Nicht spielende EMBi-Player können im Playerbereich aus Home Assistant entfernt werden, ohne die Emby-Serverhistorie zu löschen.

EMBi speichert zuerst die exakte Hidden-Regel, validiert die Registry-Zuordnung erneut, lädt die Integration neu und bestätigt den Erfolg erst, wenn der Player nicht zurückgekehrt ist. `playing`, `paused` und unklare Wiedergabezustände bleiben geschützt.

Registry-Einträge ohne aktuellen Emby-Datensatz heißen **Nicht mehr vom Emby-Server gemeldet**. Dieser Zustand ist nicht automatisch ein Home-Assistant-Orphan. Deaktivierte, aber gültige Entities bleiben ebenfalls gültige Entities.

### Player wiederherstellen

Beim Wiederherstellen entfernt EMBi die passende Regel, lädt neu und prüft die entstandene Entity. Eine neu angelegte Entity kann anschließend erneute Zuordnungen in Dashboards, Automationen, HomeKit oder Siri erfordern.

## Installation über HACS

1. HACS öffnen.
2. `Seger85/home-assistant-embi` als benutzerdefiniertes Integrations-Repository hinzufügen.
3. **Emby Integration - EMBi** installieren oder aktualisieren.
4. Home Assistant neu starten.
5. Unter **Einstellungen → Geräte & Dienste** EMBi hinzufügen oder die bestehenden Optionen öffnen.

EMBi wird ausschließlich über reguläre GitHub-Releases bereitgestellt. Das HACS-Paket heißt `embi.zip`; die zugehörige Prüfsumme liegt im Releaseasset `embi.zip.sha256`.

## Upgrade auf 0.9.3

Die Migration ist idempotent und erhält insbesondere:

- Config Entry und bestehende Entity-IDs
- Unique IDs und individuelle Namen
- Aliase, Areas, Labels und deaktivierten Registry-Zustand
- wirksame Sichtbarkeitsentscheidungen
- Status der automatischen Bereinigung
- manuelle und automatische Alterswerte
- Scheduler- und Laufstatus

Nicht eindeutig auflösbare ältere Regeln werden sichtbar erhalten und nicht still verworfen. Ein vollständiges Home-Assistant-Backup vor dem Update bleibt empfohlen. Direkte Änderungen an `.storage` sind weder erforderlich noch unterstützt.

## Datenschutz und Sicherheit

- lokale Kommunikation mit dem Emby-Server
- redigierte Diagnostics ohne API-Schlüssel oder vollständige private Clientidentitäten
- unterstützte Home-Assistant-APIs statt direkter `.storage`-Bearbeitung
- exakte Registry-Prüfung nach Domain, Plattform, Config Entry und Unique ID
- frische Revalidierung unmittelbar vor dauerhaften Aktionen
- gemeinsamer Lock gegen parallele Wartungsläufe
- persistenter Scheduler und persistenter Laufbericht

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
