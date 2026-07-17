# Konfiguration

## Verbindung

EMBi benötigt pro Emby-Server genau einen Config Entry mit:

- Name
- Host oder IP-Adresse
- Port
- HTTPS an/aus
- Emby-API-Schlüssel

Es gibt keinen zweiten Cleanup-Schlüssel. Der gespeicherte Schlüssel wird im Reconfigure-Flow nicht als Frontend-Default zurückgegeben und in Diagnostics redigiert.

## Root-Navigation

Der Options Flow besitzt genau diese fachlichen Bereiche:

- **Geräte & Player**
- **Bereinigung**
- **Änderungen prüfen**, sobald der Entwurf vom gespeicherten Zustand abweicht

Normale Unterseiten schreiben nicht direkt. Apply schreibt Optionen einmal und lädt höchstens einmal neu. Discard und Schließen über X schreiben nichts.

## Geräte & Player

### Globale Darstellung

**Nur während der Wiedergabe anzeigen**

- aus: ausgewählte Player bleiben dauerhaft verfügbar
- ein: Player erscheinen nur bei `playing` oder `paused`

**Neue Player automatisch anzeigen**

- ein: neue Wiedergabeclients werden automatisch berücksichtigt
- aus: neue Player bleiben verborgen, bis sie im Options Flow aktiviert werden

**Technische Zugriffe anzeigen**

Technische Zugriffe werden nur bei belastbarer Metadaten- oder Verhaltensgrundlage erkannt. Ein Produktname allein reicht nicht. Unsichere Clients verbleiben unter **Unklare Clients**.

### Gruppen

Reihenfolge:

1. bekannte Emby-Benutzer
2. **Gemeinsam genutzt** mit allen bekannten Benutzern
3. **Ohne Benutzerzuordnung**
4. **Technische Zugriffe**
5. **Unklare Clients**
6. gegebenenfalls **Ältere Regeln**

Jede Player-Zeile zeigt App/Gerät, Home-Assistant-Anzeigename, vollständige Entity-ID, Benutzerkontext und Status. ReportedDeviceId, Config Entry ID und Unique ID werden in der normalen UI nicht benötigt.

### Sichtbarkeitsregeln

Kanonische Regeln:

- exakter logischer Player/App-Variante
- exaktes vollständiges Gerät über alle App-Varianten
- Master-Sichtbarkeit für Player, die ausschließlich einem Benutzer zugeordnet sind
- nicht eindeutig migrierbare ältere Regeln

Regeln arbeiten ausschließlich exakt. Präfix-, Wildcard- oder Teilstring-Matching ist ausgeschlossen.

### Deaktivierte Entities

Eine deaktivierte, weiterhin gültige EMBi-Entity ist kein Orphan. Sie kann gezielt wieder aktiviert werden, ohne Entity-ID, Unique ID, Namen, Alias, Area oder Labels neu zu schreiben.

## Änderungen prüfen

Die Review-Seite zeigt semantische Vorher-/Nachher-Angaben, zum Beispiel:

- Immer verfügbar → Nur während der Wiedergabe
- Neue Player automatisch anzeigen: Ein → Aus
- Altersgrenze: 364 Tage → 365 Tage
- Wohnzimmer Fernseher: In Home Assistant anzeigen → Ausgeblendet

Für normales Apply und Discard gibt es keinen zusätzlichen Bestätigungsschalter.

## Bereinigung

Der gemeinsame Bereich zeigt getrennte Zähler für:

- Emby-Server-Gerätehistorie
- Home-Assistant-Player
- zusätzliche historische Datensätze
- aktuell entfernbare Player
- durch Wiedergabe geschützte Player
- letzten Lauf und nächsten automatischen Termin

### Manuelle Serverprüfung

Alterswerte:

- 7 Tage
- 30 Tage
- 90 Tage
- 180 Tage
- 365 Tage
- benutzerdefiniert

Der numerische Wert ist die Quelle der Wahrheit. `364` bleibt `364`; `365` bleibt `365`.

Wenn keine sicheren Kandidaten existieren, wird kein leerer Mehrfachselektor angezeigt. Es erfolgt keine Änderung.

### Automatische Serverbereinigung

- bei Neuinstallation aus
- bestehende Stellung bleibt bei Migration erhalten
- 120-Sekunden-Catch-up für Erstaktivierung, überfälligen Termin oder Migration ohne persistenten Termin
- danach 24 Stunden nach Abschluss des vorherigen Versuchs
- persistentes absolutes `next_run_at`
- kein Batchlimit

### Home-Assistant-Player entfernen

Dies ist eine eigene destruktive Aktion und löscht keine Emby-Serverhistorie.

Auswählbar sind nur EMBi-Player, die:

- eindeutig zur Integration gehören
- aktuell nicht spielen
- nicht pausiert sind
- einen ausreichend bekannten Wiedergabestatus besitzen

Vor der Entfernung wird eine exakte Hidden-Regel gespeichert. Danach folgen Reload, Registry-Entfernung und Verifikation. Diese Aktion besitzt genau eine abschließende Bestätigung.

### Wiederherstellen

Ein verborgener oder entfernter Player wird unter **Geräte & Player** wieder sichtbar geschaltet. Nach Apply lädt EMBi neu und prüft die resultierende Entity. Bei einer neu angelegten Entity können manuelle Zuordnungen in Dashboards, Automationen, HomeKit oder Siri erneut nötig sein.

## Migration von 0.3.0

Erhalten:

- Config Entry und Verbindung
- Entity-IDs und Unique IDs
- individuelle Namen
- Aliase, Areas und Labels
- disabled state
- bestehende Sichtbarkeitsentscheidungen
- automatische Bereinigung ein/aus
- exakte Alterswerte
- HA-Mitbereinigung
- Scheduler- und Laufstatus

Überführt:

- alter Modus → permanenter oder Active-only-Modus
- Allowlist → exakte sichtbare Player bei ausgeschalteter Auto-Anzeige
- App-Ignore → exakte Hidden-Player-Regel
- Geräte-Ignore → exakte Hidden-Geräte-Regel
- unklare Altwerte → sichtbare **Ältere Regeln**

Entfernt:

- separater Cleanup-API-Schlüssel
- Aktivierungsphrase
- automatische Ignore-Regel nach Serverlöschung
- obsolete rc3-Hilfswerte

Vor dem Upgrade ein vollständiges Home-Assistant-Backup erstellen. Keine `.storage`-Dateien direkt bearbeiten.
