# EMBi Project State

## Veröffentlichte Basis

- aktuelle stabile Version auf `main`: `v0.3.0`
- veröffentlichter Main-Commit: `0ebf273f0bd41f6c8f878042ac0fc4160d07e978`
- aktuelle verifizierte Home-Assistant-Live-Baseline: 69 Emby-Server-Historieneinträge und 30 aktiv geladene EMBi-`media_player`-Entities
- zusätzliche EMBi-Wartungsentity: keine
- Legacy YAML: nicht Bestandteil des Laufzeitpfads
- automatische Bereinigung: deaktiviert
- manuelle und automatische Bereinigungsschwelle: jeweils 365 Tage

Keine privaten Geräteidentitäten, Zugangsdaten oder internen Config-Entry-IDs werden in diesem Dokument gespeichert.

## 0.9.0-Implementierung

- eingefrorener Vertrag: `docs/specs/0.9.0/`
- Spezifikationsbasis auf `develop`: `75b68f6a1181f66e7603ab4f920aebfeda5f323e`
- Implementierungsbranch: `feature/embi-0.9.0`
- Implementierungs-PR: #29 nach `develop`
- Zielversion: `0.9.0`
- Releaseart: reguläre Stable-Version
- öffentlicher Tag/Release: vor der privaten Live-Abnahme nicht zulässig
- `main` bleibt bis zur späteren Promotion unverändert auf `v0.3.0`

## 0.9.0-Produktvertrag

### Geräte & Player

- bekannte Emby-Benutzer als erste Gruppen
- gemeinsam genutzte Geräte mit allen bekannten Benutzern
- Geräte ohne Benutzerzuordnung
- technische Zugriffe nur bei belastbarer Metadaten- oder Verhaltensgrundlage
- unklare Clients bleiben unklar
- verständliche App-, Geräte-, HA-Namens-, Entity-ID- und Statusangaben
- keine normale UI-Abhängigkeit von ReportedDeviceId, Config Entry ID oder Unique ID
- dauerhafte und Active-only-Sichtbarkeit
- exakte Player-, Geräte- und Benutzerregeln
- nicht eindeutig migrierbare ältere Regeln bleiben sichtbar erhalten

### Bereinigung

- ein gemeinsamer UI-Bereich
- Serverhistorie und Home-Assistant-Player bleiben getrennte Aktionen
- `playing` und `paused` sind geschützt
- unklarer Status arbeitet fail-safe
- nicht spielende EMBi-Player können in EMBi verborgen und separat aus Home Assistant entfernt werden
- exakte Hidden-Rule wird vor Registry-Entfernung gespeichert
- Reload und Verifikation verhindern unbeabsichtigtes Wiedererscheinen
- Wiederherstellung prüft die resultierende Entity
- deaktivierte gültige Entities gelten nicht als verwaist
- jede destruktive Aktion besitzt genau eine abschließende Bestätigung

### Entwurf und Migration

- normale Änderungen bleiben bis Apply ausschließlich im Entwurf
- semantische Vorher-/Nachher-Ausgabe
- Discard und Schließen über X schreiben nichts
- normales Apply schreibt Optionen genau einmal und lädt höchstens einmal neu
- Config Entry Schema 4 / Optionsschema 2
- Entity-IDs, Unique IDs, individuelle Namen, Aliase, Areas, Labels und deaktivierter Zustand bleiben erhalten
- bestehende Sichtbarkeit bleibt wirksam
- automatische Bereinigung bleibt ein oder aus wie zuvor
- exakte Alterswerte wie `364` und `365` bleiben unverändert
- Scheduler- und Laufstatus bleiben erhalten

## Persistenz und Datenschutz

- offizielle Home-Assistant-Storage-API
- Store-Envelope bleibt kompatibel; internes Wartungsschema wird versioniert erweitert
- persistente, redigierte Migration-, Cleanup-, Removal- und Restore-Zusammenfassungen
- Diagnostics enthalten aggregierte Zähler, Klassen, Gruppen, Sichtbarkeit und Status
- keine API-Schlüssel, vollständigen Server-Record-IDs, ReportedDeviceIds, Player-Keys oder Benutzernamen in Diagnostics oder Laufberichten
- keine direkte `.storage`-Bearbeitung

## Pre-Live-Gates

Vor dem Merge von PR #29 nach `develop` ist genau ein externer Prüfpunkt vorgesehen:

- vollständige CI auf dem exakten Feature-Commit
- privates releasegleiches `0.9.0`-Artefakt mit SHA-256 und `BUILD_COMMIT`
- frisches Home-Assistant-Backup
- Upgrade von `v0.3.0` auf das private Artefakt
- Config Entry bleibt geladen
- 69 Server-Historieneinträge und 30-Player-Baseline sowie Entity-IDs, Unique IDs, Namen, Aliase, Areas, Labels und disabled state bleiben erhalten, sofern unmittelbar vor dem Test keine reale Clientänderung dokumentiert wird
- Benutzer-, Shared-, Unassigned-, Technical- und Unknown-Gruppen prüfen
- normale Draft-Navigation, Review, Apply, Discard und X prüfen
- iPhone-, iPad- und Desktop-QA
- `playing` und `paused` als geschützt verifizieren
- einen normalen nicht spielenden Player kontrolliert entfernen
- prüfen, dass der Player nach Reload nicht zurückkehrt
- denselben Player wiederherstellen und resultierende Entity dokumentieren
- Serverhistorien-Bereinigung separat prüfen
- exakte Werte `364`/`365`, Automatikstellung, Scheduler, Reload und Neustart prüfen
- Rollback auf `v0.3.0` oder Backup demonstrieren

## Veröffentlichungssperre

Vor dokumentierter privater Live-Abnahme:

- PR #29 nicht nach `develop` mergen
- `develop` nicht nach `main` promoten
- keinen Tag `v0.9.0` erstellen
- keinen GitHub Release veröffentlichen
- kein RC, Beta- oder Dev-Release veröffentlichen
- keine bestehenden Tags oder Releases verändern
