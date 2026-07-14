# Konfiguration und Gerätefilter

## Verbindung

Pflichtfelder:

- Anzeigename
- Host/IP ohne Protokollpräfix
- Port
- HTTPS-Schalter
- API-Schlüssel

Der API-Schlüssel wird im Config Entry gespeichert und in Diagnostics redigiert. Bei der Rekonfiguration wird ein gespeicherter Schlüssel nie in das Passwortfeld zurückgegeben. Ein leeres Feld behält den vorhandenen Schlüssel bei.

## Gerätemodus

### Alle Geräte anzeigen

Alle von pyemby gelieferten Geräte dürfen Entitäten erzeugen, sofern sie nicht ignoriert sind.

### Nur aktive Wiedergaben

Zulässig sind `playing` und `paused`. Leerlaufende oder ausgeschaltete Clients werden nicht als verfügbar geführt.

### Nur ausgewählte Geräte

Die Liste **Anzuzeigende Geräte** speichert `ReportedDeviceId.AppName`. Zwei Apps auf demselben Client können getrennt behandelt werden.

## Ignorierliste

Die Ignorierliste hat immer Vorrang. Sie speichert standardmäßig die rohe `ReportedDeviceId` und schließt damit alle App-Varianten desselben Clients aus.

## Sammelaktionen

- alle aktuellen Geräte auswählen
- Auswahl anzuzeigender Geräte leeren
- alle aktuellen Geräte ignorieren
- Ignorierliste leeren

Historische Datensätze werden auf eindeutige Client-/App- beziehungsweise rohe Client-Identitäten dedupliziert.

## Übergeordnete Serverbereinigung

Die gesamte Serverbereinigung ist standardmäßig ausgeschaltet. Dieser Master-Schalter kontrolliert:

- manuelle altersbasierte Serverbereinigung
- automatische Serverbereinigung
- optionalen separaten Cleanup-API-Schlüssel

Wird der Master-Schalter ausgeschaltet, wird die Automatik ebenfalls deaktiviert. Ein gespeicherter separater Schlüssel wird dabei entfernt. Ein leeres Passwortfeld bei aktivierter Bereinigung behält einen vorhandenen separaten Schlüssel bei.

## Manuelle altersbasierte Bereinigung

Der manuelle Ablauf ist zweigeteilt:

1. Mindestalter in Tagen wählen
2. aus den danach gefilterten Datensätzen konkrete Einträge auswählen

Standardwert: **365 Tage**.

Ausgeschlossen werden:

- `playing`- oder `paused`-Player
- Datensätze ohne gültigen letzten Aktivitätszeitpunkt
- Datensätze, die den Altersfilter nicht erfüllen

Optionen pro manueller Löschung:

- erfolgreich gelöschte rohe Clients zusätzlich ignorieren
- den zugehörigen HA-Media-Player nach erfolgreicher und revalidierter Serverlöschung entfernen

## Automatische Serverbereinigung

Die Automatik besitzt einen separaten Schalter und ist standardmäßig aus.

Erstaktivierung:

- Warnschalter aktivieren
- exakten Aktivierungstext eingeben
- Altersfilter festlegen; Standard 365 Tage
- entscheiden, ob zugehörige HA-Media-Player sicher entfernt werden sollen

Zeitverhalten:

- erster Lauf einmalig 120 Sekunden nach der bewussten Aktivierung
- anschließend alle 24 Stunden; Reloads oder Neustarts lösen den Erstlauf nicht erneut aus

Löschverhalten:

- keine maximale Zahl pro Lauf
- alle zulässigen Datensätze werden unabhängig verarbeitet
- Fehler eines Datensatzes stoppen die übrigen nicht
- aktive Player und unbekannte Zeitstempel werden übersprungen
- die Automatik trägt Clients nicht automatisch in die rohe Ignorierliste ein

## Verhalten bei fehlenden Geräten

Bereits konfigurierte IDs bleiben im Selektor sichtbar, auch wenn sie vom Server momentan nicht gemeldet werden. Sie erhalten einen entsprechenden Hinweis.
