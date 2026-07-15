# 05 – Finale UI-Texte Deutsch

Die Formulierungen sind verbindlich. Dynamische Platzhalter stehen in `{geschweiften_klammern}`.

## Hauptseite

**Titel:** EMBi verwalten

**Einleitung:** Verwalte Emby-Player in Home Assistant und bereinige bei Bedarf alte Geräte-Einträge sicher.

**Statistik:**
- `{count}` Geräte in der Emby-Server-Gerätehistorie
- `{count}` Player in Home Assistant
- `{count}` durch laufende Wiedergabe geschützt
- `{count}` derzeit aus Home Assistant entfernbar
- Automatische Bereinigung: `{status}`

**Menüs:**
- Geräte & Player
- Bereinigung
- `{count}` Änderungen prüfen

## Geräte & Player

**Titel:** Geräte & Player

**Einleitung:** Lege fest, welche Emby-Player in Home Assistant erscheinen.

**Schalter:** Nur während der Wiedergabe anzeigen  
**Beschreibung aus:** Ausgewählte Player bleiben auch ohne laufende Wiedergabe in Home Assistant verfügbar.  
**Beschreibung ein:** Player erscheinen nur, während darauf abgespielt oder pausiert wird.

**Schalter:** Neue Player automatisch anzeigen  
**Beschreibung ein:** Neue Wiedergabegeräte werden automatisch in Home Assistant angezeigt.  
**Beschreibung aus:** Neue Wiedergabegeräte bleiben ausgeblendet, bis du sie hier aktivierst.

**Suche:** Benutzer, Gerät, App oder Entity-ID suchen

**Gruppen:**
- Benutzer
- Gemeinsam genutzt
- Ohne Benutzerzuordnung
- Technische Zugriffe
- Unklare Clients
- Ältere Regeln prüfen

**Benutzer-Schalter:** Alle Player von `{user}` anzeigen

**Technische Zugriffe – Erklärung:** Diese Anwendungen haben über die Emby-API auf den Server zugegriffen. Sie sind keine normalen Wiedergabegeräte.

**Technische Zugriffe – Schalter:** Technische Zugriffe als Player in Home Assistant anzeigen

**Status:**
- Spielt
- Pausiert
- Bereit
- In Home Assistant deaktiviert
- In EMBi ausgeblendet
- Wird vom Emby-Server nicht mehr gemeldet
- Kein Benutzer zugeordnet
- Genutzt von `{users}`
- Zuletzt verwendet von `{user}`
- Zuletzt verwendet am `{date}`

**Aktionen:**
- In Home Assistant aktivieren
- In EMBi ausblenden
- Wieder in Home Assistant anzeigen
- Zurück zu Geräte & Player

**Schutztext:** Beende zuerst die Wiedergabe, bevor du diesen Player ausblendest oder entfernst.

## Bereinigung

**Titel:** Bereinigung

**Einleitung:** Bereinige alte Einträge auf dem Emby-Server oder entferne nicht gewünschte Player aus Home Assistant.

**Statistik:**
- `{count}` Geräte in der Emby-Server-Gerätehistorie
- `{count}` Player in Home Assistant
- `{count}` zusätzliche historische Geräte in der Emby-Server-Gerätehistorie
- `{count}` Server-Einträge können derzeit sicher gelöscht werden
- `{count}` Home-Assistant-Player können derzeit entfernt werden
- `{count}` Player sind durch Wiedergabe geschützt

**Erklärung:** Emby speichert alle Geräte- und App-Verbindungen, die den Server verwendet haben – aktive, inaktive und technische Zugriffe. Ein physisches Gerät kann durch verschiedene Apps oder Anmeldungen mehrfach erscheinen. Den Anzeigenamen eines Eintrags kannst du auch direkt im Emby-Server unter „Geräte“ anpassen.

**Hinweis zur Differenz:** Zusätzliche historische Einträge sind nicht automatisch löschbar. EMBi prüft Alter, Aktivität und bestehende Player-Zuordnungen.

### Automatik

**Schalter:** Alte Emby-Einträge automatisch bereinigen

**Beschreibung ein:** EMBi prüft regelmäßig alte Einträge und entfernt nur Datensätze, die alle Sicherheitsregeln erfüllen.

**Beschreibung aus:** Die automatische Bereinigung ist ausgeschaltet. Manuelle Prüfungen bleiben möglich.

**Feld:** Einträge entfernen, die älter sind als

**Optionen:**
- 1 Woche – 7 Tage
- 1 Monat – 30 Tage
- 3 Monate – 90 Tage
- 6 Monate – 180 Tage
- 1 Jahr – 365 Tage
- Eigener Wert

**Feld:** Eigener Zeitraum in Tagen

**Schalter:** Passende Home-Assistant-Player ebenfalls entfernen

**Beschreibung:** Entfernt zusätzlich einen zugehörigen Player aus Home Assistant, wenn kein verbleibender Emby-Eintrag ihn benötigt und er weder spielt noch pausiert.

### Manuelle Serverprüfung

**Überschrift:** Emby-Server-Gerätehistorie prüfen

**Aktion:** Jetzt prüfen

**Nullzustand:** Keine passenden Einträge gefunden. Es wurde nichts verändert.

**Ergebniszeilen:**
- `{count}` sind älter als `{days}` Tage und können sicher gelöscht werden
- `{count}` sind durch aktive Wiedergabe geschützt
- `{count}` erfüllen nicht alle Löschregeln
- `{count}` besitzen kein gültiges Aktivitätsdatum

**Aktion:** `{count}` ausgewählte Einträge löschen

**Bestätigungstitel:** `{count}` Emby-Server-Einträge löschen?

**Bestätigungstext:** Die ausgewählten Geräte-Einträge werden aus der Emby-Server-Gerätehistorie entfernt. Benutzerkonten, Medien, Bibliotheken und Wiedergabeverläufe werden nicht gelöscht.

**Buttons:**
- Zurück
- Endgültig löschen

### Home Assistant

**Überschrift:** Home-Assistant-Player

**Zusammenfassung:**
- `{count}` Player in Home Assistant
- `{count}` derzeit entfernbar
- `{count}` durch Wiedergabe geschützt

**Aktion:** Home-Assistant-Player verwalten

**Player-Aktion:** Aus Home Assistant entfernen

**Bestätigungstitel:** `{count}` Player aus Home Assistant entfernen?

**Bestätigungstext:** Die ausgewählten Player werden in EMBi ausgeblendet und aus Home Assistant entfernt. Sie bleiben in der Emby-Server-Gerätehistorie und können später unter „Geräte & Player“ wiederhergestellt werden.

**Button:** `{count}` Player entfernen

**Fehler:** `{name}` konnte nicht entfernt werden. Der Player wurde nach dem Neuladen erneut erkannt.

**Erfolg:** `{name}` wurde aus Home Assistant entfernt und blieb nach dem Neuladen ausgeblendet.

### Letzter Lauf

**Überschrift:** Letzter Bereinigungslauf

**Status:**
- Erfolgreich
- Teilweise erfolgreich
- Fehlgeschlagen
- Noch nicht ausgeführt

**Modus:**
- Automatisch
- Manuell

**Zeilen:**
- Gestartet: `{datetime}`
- Beendet: `{datetime}`
- Altersgrenze: `{days}` Tage
- Gelöscht: `{count}`
- Geschützt: `{count}`
- Fehler: `{count}`
- Nächster Lauf: `{datetime}`
- Nächster Lauf: Automatik deaktiviert

## Änderungsprüfung

**Titel:** Änderungen prüfen

**Buttons:**
- Änderungen verwerfen
- Änderungen übernehmen

**Leerer Zustand:** Keine ungespeicherten Änderungen.

## Allgemein

**Navigation:**
- Zurück zu EMBi verwalten
- Zurück zu Geräte & Player
- Zurück zur Bereinigung

**Fehler allgemein:** Die Aktion konnte nicht sicher abgeschlossen werden. Es wurde kein Erfolg gemeldet. Weitere technische Details stehen in den EMBi-Diagnosedaten.
