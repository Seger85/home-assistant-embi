# EMBi Project State

## Veröffentlichte Linie

- aktuelle Produktversion: `0.9.3`
- Stable-Branch: `main`
- Stable-Tag: `v0.9.3`
- Verteilung: regulärer GitHub-Release mit `embi.zip` und `embi.zip.sha256`
- HACS verwendet ausschließlich veröffentlichte Releaseassets; der Default-Branch-Fallback ist ausgeblendet
- zusätzliche EMBi-Wartungsentity: keine
- Legacy YAML: nicht Bestandteil des Laufzeitpfads

Dieses Dokument enthält keine privaten Geräteidentitäten, Zugangsdaten, Netzwerkadressen oder Config-Entry-IDs.

## Produktumfang 0.9.3

### Home-Assistant-Player

- Hauptbereich **Home-Assistant-Player**
- globale Schalter für Active-only, neue Player und technische Zugriffe
- kompakte Benutzer-, Shared-, Unassigned-, Technical- und Unknown-Gruppen
- Master-Schalter für bekannte Benutzer
- einzelne Abweichungen unter **Ausnahmen verwalten**
- Suche und Seitennavigation für lange Listen
- kurze Labels aus Gerät und App
- technische Angaben ausschließlich in Detailansichten
- bestehende Entity-IDs, Unique IDs, Namen, Aliase, Areas, Labels und disabled state bleiben unverändert

### Options-Flow-Draft

- Hauptmenü aus **Home-Assistant-Player** und **Emby-Server bereinigen**
- **Änderungen prüfen** erscheint nur bei offenem Entwurf
- jede Unterseite besitzt **‹ Zurück**
- Zurück behält den vollständigen Entwurf
- X und Verwerfen schreiben nichts und laden nicht neu
- unverändertes Apply bleibt als Inline-Hinweis im Flow
- geändertes Apply schreibt genau einmal und lädt höchstens einmal neu
- normale Fehler bleiben auf der aktiven Seite

### Emby-Server bereinigen

- getrennte Seiten für automatische Bereinigung, manuelle Prüfung und letzten Lauf
- getrennte manuelle und automatische Alterswerte
- Presets 7, 30, 90, 180 und 365 Tage plus benutzerdefinierter Wert
- exakte Bestandswerte wie `364` und `365` bleiben unverändert
- benutzerdefiniertes Zahlenfeld nur bei Auswahl von **Benutzerdefiniert**
- Kandidatenauswahl als Vorschau und anschließend genau eine Ausführung
- Serverhistorie und Home-Assistant-Player bleiben getrennte Vorgänge

### Player entfernen und wiederherstellen

- `playing`, `paused` und unklare Wiedergabezustände sind geschützt
- exakte Hidden-Regel wird vor einer Registry-Entfernung gespeichert
- aktuelle Server-, Registry-, Config-Entry-, Plattform- und Unique-ID-Daten werden erneut validiert
- Erfolg wird erst nach Reload und Wiederkehrprüfung gemeldet
- Restore entfernt die passende Regel, lädt neu und verifiziert die resultierende Entity
- deaktivierte gültige Entities gelten nicht als Orphans
- Registry-Einträge ohne aktuellen Emby-Datensatz werden als **Nicht mehr vom Emby-Server gemeldet** geführt
- echte Home-Assistant-Orphans bleiben eine separate Registry-Semantik

## Migration

Die Migration von 0.9.0 auf 0.9.3 ist idempotent und verändert keine wirksame Sichtbarkeit. Erhalten bleiben:

- Config Entry
- Entity-IDs und Unique IDs
- individuelle Namen, Aliase, Areas und Labels
- aktivierter oder deaktivierter Registry-Zustand
- automatische Bereinigung ein oder aus
- manuelle und automatische Alterswerte
- persistenter Scheduler und Laufbericht
- vorhandene exakte Player-, Geräte- und Benutzerregeln

Nicht eindeutig auflösbare ältere Regeln werden sichtbar erhalten und nicht still neu klassifiziert.

Historische Einordnung: 0.9.0 führte den Bereich **Geräte & Player** ein. 0.9.3 ersetzt dessen Navigation durch **Home-Assistant-Player**. Frühere private Abnahmeartefakte sind keine Installationsquelle; produktiv wird ausschließlich der reguläre Stable-Release verwendet.

## Persistenz und Datenschutz

- offizielle Home-Assistant-Storage-API
- versionierter Wartungsstatus pro Config Entry
- persistenter Scheduler mit absolutem `next_run_at`
- persistenter Laufbericht mit getrennten Server- und Registry-Zählern
- Diagnostics enthalten nur redigierte oder aggregierte Angaben
- keine API-Schlüssel, vollständigen Record-IDs, ReportedDeviceIds, Player-Keys oder Benutzernamen in Reports
- keine direkte `.storage`-Bearbeitung

## Qualität und Releasevertrag

Jeder Stable-Commit benötigt:

- Quality auf Python 3.13 und 3.14
- JSON, YAML, Compileall, Mypy, Ruff und Ruff-Format
- vollständigen Pytest-Lauf
- Specification Contract und Stable Contract
- Secret-/Privacy-Scan
- HACS Validation und Hassfest
- releasegleichen Paketbau mit SHA-256 und `BUILD_COMMIT`

Ein Stable-Release muss auf einem Commit in `main` liegen, darf weder Draft noch Prerelease sein, muss `latest` sein und ausschließlich `embi.zip` sowie `embi.zip.sha256` veröffentlichen.
