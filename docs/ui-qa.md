# UI-QA

## Ziel

Alle Config- und Options-Flows müssen mit dem produktiven Seger-Theme auf iPhone, iPad und Desktop vollständig bedienbar sein. EMBi verwendet ausschließlich native Home-Assistant-Selektoren und injiziert kein fragiles CSS.

## Zu prüfende Seiten

- Config Flow und Reconfigure Flow
- Options-Hauptmenü mit Draft-Zusammenfassung
- Media-Player und Geräte
- Sammelaktionen für Auswahl, App-Regeln und Geräte-Regeln
- Serverbereinigung mit Preset und Custom-Wert
- Automatische Serverbereinigung
- Warnseite mit Pflichtschalter und ohne Texteingabe
- Apply
- Discard
- HA-Registry-Bereinigung
- manuelle Serverbereinigung
- Bestätigungsdialog
- letzter Bereinigungslauf
- About

## Funktionsmatrix

- Entwurf über mehrere Unterseiten erhalten
- Rückkehr zum Hauptmenü
- Dirty-Zusammenfassung korrekt
- Apply schreibt einmal und löst höchstens einen Reload aus
- unveränderter Apply ohne Reload
- Discard ohne Write und ohne Reload
- Schließen über X ohne Write
- kritische Aktionen bei Dirty Draft gesperrt
- Automatik startet nicht vor Apply
- 364 als Custom sichtbar
- 365 bewusst auswählbar
- Warnseite enthält keinen Aktivierungstext
- neue HA-Mitbereinigung standardmäßig aus

## Breakpoints

Mindestens:

- iPhone Hochformat
- iPad Hochformat oder Split View
- Desktop

## Sichtkriterien

- keine abgeschnittenen Beschreibungen
- keine horizontalen Überstände
- lange Gerätenamen und Labels umbrechen
- Dropdowns geschlossen und geöffnet lesbar
- Mehrfachauswahl bedienbar
- Preset und Custom-Feld eindeutig
- Schalterzustände eindeutig
- Pflichtwarnungen vollständig sichtbar
- Bestätigungstext vollständig sichtbar
- Zeitpunkte und Zähler des Laufberichts lesbar
- keine privaten IDs oder Zugangsdaten sichtbar
- Passwortfelder leer

## Screenshot-Ablauf

1. Backup und Ausgangszustand bestätigen.
2. jede Seite über den regulären UI-Weg öffnen.
3. iPhone, iPad und Desktop aufnehmen.
4. Apply/Discard funktional prüfen, nicht nur fotografieren.
5. kritische Wartungsseiten nur mit sicherem Testobjekt öffnen.
6. Automatik nicht ausschließlich für einen Screenshot aktivieren.
7. nach jeder tatsächlichen Aktion Logs, Storebericht, Entitäten und Seiteneffekte prüfen.

## Theme-Grenze

Zu helle native Selektoren werden im globalen Home-Assistant-Theme korrigiert. EMBi selbst verändert kein Shadow DOM und liefert keine gerätespezifischen CSS-Hacks.
