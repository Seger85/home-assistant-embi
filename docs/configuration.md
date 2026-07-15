# Konfiguration

## Verbindung

EMBi benötigt genau einen Config Entry mit:

- Name
- Host oder IP-Adresse
- Port
- HTTPS an/aus
- normalem Emby-Verbindungsschlüssel

Es gibt keine zusätzlichen Cleanup-Anmeldedaten. Derselbe gespeicherte Verbindungsschlüssel wird für Wiedergabe, Geräteabfrage und ausdrücklich bestätigte Wartungsaktionen verwendet. Der gespeicherte Wert wird im Reconfigure-Flow nie als Standardwert an das Frontend zurückgegeben.

## Media-Player-Modus

- **Alle Geräte anzeigen**: kompatibles Standardverhalten
- **Nur aktive Wiedergaben**: nur `playing` oder `paused`
- **Nur ausgewählte Geräte**: exakte `ReportedDeviceId.AppName`-Allowlist

## Ignorierregeln

- **Ignorierte App-Varianten**: exakte App-/Client-Identität
- **Ignorierte Geräte**: exakte `ReportedDeviceId`, wirkt auf alle App-Varianten
- **Nicht auflösbare Altregeln**: bleiben sichtbar erhalten, bis sie bewusst entfernt werden

Ignorieren hat Vorrang vor Allowlist und Modus. Es gibt keine Präfix- oder Teilstring-Auswertung.

## Options-Entwurf

Eine Options-Sitzung kann mehrere Unterseiten umfassen. Änderungen bleiben im Entwurf, bis **Änderungen übernehmen** bestätigt wird.

- Unterseiten schreiben nicht.
- Sammelaktionen ändern nur den Entwurf.
- Apply speichert genau einmal.
- Bei unverändertem Entwurf erfolgt kein Write und kein Reload.
- Discard verwirft den Entwurf vollständig.
- Schließen über X schreibt nichts.
- Kritische Wartungsaktionen sind bei Dirty Draft gesperrt.

## Serverbereinigung

Der Master-Schalter ist bei neuen Installationen aus. Wird er im Entwurf ausgeschaltet, wird auch die Automatik im Entwurf ausgeschaltet.

Manuelle und automatische Alterswerte sind getrennt. Verfügbar sind:

- 7 Tage
- 30 Tage
- 90 Tage
- 180 Tage
- 365 Tage
- Benutzerdefiniert

Der numerische Tageswert ist die Quelle der Wahrheit. Ein vorhandener Wert 364 bleibt 364 und erscheint als Custom. Es findet keine globale Umwandlung auf 365 statt.

## Automatische Bereinigung

- bei neuen Aktivierungen aus
- Warnseite mit Pflichtschalter
- keine Texteingabe und keine Aktivierungsphrase
- Start erst nach finalem Apply
- erster beziehungsweise Catch-up-Lauf nach 120 Sekunden
- anschließend 24 Stunden nach Abschluss
- kein Batchlimit

## HA-Mitbereinigung

Die Option für passende HA-Media-Player ist bei neuen Aktivierungen standardmäßig `false`. Vorhandene Werte werden bei der Migration nicht verändert. Gerrys bestehender Wert `true` bleibt deshalb erhalten.

Eine tatsächliche Registry-Entfernung kann individuelle Namen, Entity-IDs, Dashboards, Automationen, HomeKit und Siri betreffen. Sie wird ausschließlich nach dem vollständigen Sicherheitsvertrag ausgeführt.

## Migration von rc3

Erhalten werden:

- Config Entry
- Entity-IDs und Unique IDs
- individuelle Namen
- Master-Schalter und Automatik
- abgeschlossener rc3-Erstlauf
- manuelle und automatische Alterswerte
- HA-Mitbereinigung
- gültige Auswahl- und Ignore-Werte

Entfernt werden:

- zusätzliches Cleanup-Zugangsfeld
- bisheriger Aktivierungstext
- automatische Ignore-Option nach Serverbereinigung
- obsoleter rc3-Erstlauf-Hilfswert nach Übertragung in den Store
- gemischte Legacy-Ignore-Liste nach sicherer Klassifizierung
