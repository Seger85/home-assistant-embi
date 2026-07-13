# Visuelle Qualitätssicherung

Config- und Options-Flows verwenden native Home-Assistant-Komponenten. Trotzdem muss jede Version im produktiven Theme geprüft werden.

## Prüfumfang

- Config Flow: neu verbinden
- Reconfigure Flow
- Hauptmenü des Options Flow
- Geräteverwaltung
- geöffnete und geschlossene Mehrfachauswahl
- Sammelaktionen
- Registry-Bereinigung
- Serverbereinigung ausgeschaltet
- Serverbereinigung eingeschaltet
- Auswahl, Bestätigung, Fehler und Abschlussmeldung
- About-Dialog

## Breakpoints

- iPhone
- iPad
- Desktop

## Sichtkriterien

- Feldhintergrund und Text ausreichend kontrastreich
- ausgeschaltete Schalter klar erkennbar
- Fokusrahmen sichtbar
- keine abgeschnittenen Beschreibungen
- lange Gerätenamen umbrechen sinnvoll
- Bestätigungstext und Anzahl vollständig sichtbar
- keine horizontalen Überstände

## Verantwortungsgrenze

Weiße oder zu helle native Selektoren sind ein Theme-Problem. EMBi darf dafür kein eigenes Shadow-DOM- oder Config-Flow-CSS injizieren. Die Theme-Korrektur muss zentral erfolgen und anschließend mit EMBi erneut geprüft werden.
