# Visuelle Qualitätssicherung

Config- und Options-Flows verwenden native Home-Assistant-Komponenten. Jede Version muss im produktiven Theme geprüft werden.

## Prüfumfang

- Config Flow und Reconfigure Flow
- Options-Hauptmenü
- Geräteverwaltung und Sammelaktionen
- HA-Registry-Bereinigung
- Master-Schalter Serverbereinigung aus/an
- manueller Altersfilter
- gefilterte Datensatzauswahl
- Optionen „ignorieren“ und „HA-Player entfernen“
- manueller Bestätigungsdialog und Ergebnis
- automatische Bereinigung aus/an
- Altersfeld der Automatik
- Warnschalter und exakter Aktivierungstext
- Hinweis auf 120 Sekunden, 24 Stunden und keine maximale Löschzahl
- About-Dialog

## Breakpoints

- iPhone
- iPad
- Desktop

## Sichtkriterien

- keine abgeschnittenen Beschreibungen
- Warnhinweis zur unbegrenzten Kandidatenzahl vollständig sichtbar
- Bestätigungstexte vollständig sichtbar
- lange Gerätenamen und Labels umbrechen sinnvoll
- Zahlenfelder auf Mobilgeräten bedienbar
- Schalterzustände eindeutig
- keine horizontalen Überstände
- Passwortfelder leer
- keine privaten IDs oder Schlüssel sichtbar

## Funktionale Screenshot-Grenze

Die Automatik darf nicht nur für einen Screenshot aktiviert werden. Eine visuelle Prüfung des aktivierten Zustands benötigt Backup, geplanten Rollback und bewusste Freigabe. Screenshots ergänzen technische Prüfungen, ersetzen sie aber nicht.

## Verantwortungsgrenze

Theme-Probleme nativer Selektoren werden zentral im Home-Assistant-Theme gelöst. EMBi injiziert kein Shadow-DOM- oder Config-Flow-CSS.
