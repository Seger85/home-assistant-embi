# Konfiguration

## Verbindung

EMBi verwendet pro Emby-Server einen Home-Assistant-Config-Entry mit Name, Host, Port, HTTPS-Einstellung und API-Schlüssel. Zugangsdaten werden in Diagnostics redigiert.

## Hauptnavigation ab 0.9.7

Der Options Flow bietet direkt:

1. **Home-Assistant-Player**
2. **Automatische Serverbereinigung**
3. **Einzelne Emby-Servereinträge löschen**
4. **Änderungen prüfen**, sobald der Entwurf abweicht

Normale Unterseiten schreiben nicht direkt. Der normale OK-Submit übernimmt Werte nur in den In-Memory-Entwurf und führt eine Ebene zurück. Dauerhaft gespeichert wird ausschließlich über **Änderungen prüfen → Änderungen übernehmen**. Schließen über X und ein nicht angewendeter Entwurf verändern den Config Entry nicht.

## Home-Assistant-Player

### Globale Regeln

- **Nur während der Wiedergabe anzeigen**
- **Neue Player automatisch anzeigen**
- **Technische Zugriffe anzeigen**
- **Gruppe öffnen**

Suchfeld und Sortierauswahl sind vollständig entfernt. Die Gruppenauswahl führt zu den direkten Schaltern der enthaltenen Player.

### Player-Zeilen

- Zeile 1: `Gerät · App`
- Zeile 2: lokalisierter letzter Zugriff
- bekannte Zeitpunkte: immer älteste zuerst
- unbekannte Zeitpunkte: immer am Ende

Entity-ID, Config-Entry-ID und Unique-ID werden nicht in normalen Auswahlzeilen gezeigt.

### Schutzlogik

Ein Schalter darf einen Player nur dann ausblenden und nach finalem Apply aus Home Assistant entfernen, wenn der Player eindeutig zur Integration gehört und sicher inaktiv ist. `playing`, `paused` und `unknown` arbeiten fail-safe und bleiben sichtbar beziehungsweise unangetastet.

Die Emby-Serverhistorie wird durch Player-Sichtbarkeit nicht verändert. Solange der Servereintrag besteht, bleibt der Player in EMBi wiederherstellbar.

## Automatische Serverbereinigung

Die Seite enthält Einstellungen und Status gemeinsam:

- aktiviert/deaktiviert
- Altersgrenze einschließlich vorhandener exakter Werte
- passende Home-Assistant-Entities nach sicherer Serverlöschung bereinigen
- letzter Lauf, Ergebnis, Schutzfälle und nächster Lauf

OK aktualisiert nur den Entwurf. Erst Apply schreibt Optionen und löst bei einer geänderten aktivierten Automatik den vorhandenen sicheren Nachlauf aus.

## Manuelle Serverbereinigung

Die manuelle Seite besitzt keine Altersgrenze und keinen Scope-Selektor. Sie listet alle eindeutig sicheren inaktiven Einträge unabhängig vom Alter, fest älteste zuerst. Die automatische Altersgrenze wird nicht verändert.

Auswahl, Vorschau und eindeutige Löschbestätigung bleiben getrennt. Nach erfolgreicher Serverlöschung wird ein exakt passender Registry-Eintrag nur dann entfernt, wenn keine verbleibende Serverhistorie, keine aktive/unklare Wiedergabe und keine Zuordnungsabweichung vorliegt.

## Migration

0.9.7 verändert weder Entity-IDs noch Unique-IDs. Bestehende Optionen bleiben schema- und migrationssicher erhalten, auch wenn ältere manuelle Alters-/Scope-Werte nicht mehr in der Oberfläche erscheinen. Vor dem Upgrade ein vollständiges Home-Assistant-Backup erstellen; `.storage` nicht direkt bearbeiten.
