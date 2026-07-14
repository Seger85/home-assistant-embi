# Manuelle und automatische Emby-Serverbereinigung

## Zweck

Die Funktion entfernt historische Einträge aus der Geräteübersicht des lokalen Emby-Servers. Sie löscht keine Filme, Serien, Benutzer oder Bibliotheken.

## Standardzustand

- übergeordnete Serverbereinigung: aus
- automatische Serverbereinigung: aus
- destruktive Menüs: ausgeblendet
- Standard-Altersfilter: 365 Tage

## Backup und Rollback

Eine serverseitige Löschung ist aus Home Assistant nicht rückgängig zu machen. Ein Emby-Server-Backup ist der einzige vollständige Rollback-Weg. Ein Home-Assistant-Backup schützt Registry und Config Entry, stellt aber gelöschte Emby-Historieneinträge nicht wieder her.

## API-Schlüssel

EMBi verwendet entweder den normalen Verbindungsschlüssel oder einen optionalen separaten Bereinigungsschlüssel. Der separate Schlüssel wird gegen `/System/Info` validiert. Gespeicherte Schlüssel werden nicht als Passwortfeld-Standardwert angezeigt.

Ob ein Schlüssel `DELETE /Devices` darf, lässt sich ohne destruktiven Test nicht beweisen. Fehlende Berechtigung wird daher pro Datensatz als Fehler ausgewiesen.

## Altersfilter

Ein Datensatz ist nur zulässig, wenn:

- `DateLastActivity` beziehungsweise `LastActivityDate` vorhanden und parsebar ist
- der Zeitstempel strikt älter als der konfigurierte Grenzwert ist
- der zugehörige `ReportedDeviceId.AppName`-Player nicht `playing` oder `paused` ist

Zeitstempel ohne Zeitzone werden konservativ als UTC behandelt. Emby-Zeitstempel mit siebenstelligen Sekundenbruchteilen werden auf Mikrosekunden normalisiert. Ungültige Werte werden nicht gelöscht.

## Manueller Ablauf

1. Master-Schalter aktivieren.
2. Altersfilter wählen.
3. konkrete historische `Id`-Datensätze auswählen.
4. optional festlegen:
   - rohe `ReportedDeviceId` ignorieren
   - zugehörigen HA-Media-Player entfernen
5. zweiten Bestätigungsdialog öffnen.
6. Schalter aktivieren und `LÖSCHEN <Anzahl>` beziehungsweise `DELETE <count>` exakt eingeben.
7. EMBi liest `/Devices` erneut und verwirft eine inzwischen ungültige oder aktive Auswahl.
8. alle gültigen Einträge werden einzeln gelöscht.
9. Ergebnis zeigt Erfolg, Fehler und vorgemerkte HA-Registry-Entfernungen.

## Automatischer Ablauf

Die Automatik muss separat aktiviert werden. Beim Wechsel von aus auf an sind Warnschalter und exakter Aktivierungstext erforderlich.

- erster Lauf einmalig 120 Sekunden nach der bewussten Aktivierung
- weitere Läufe alle 24 Stunden; Reloads und Neustarts lösen nicht erneut den 120-Sekunden-Erstlauf aus
- Standard-Alter 365 Tage
- keine maximale Löschzahl pro Lauf
- alle Kandidaten werden sequenziell und unabhängig verarbeitet
- parallele Läufe werden durch einen Lock verhindert
- aktive Player und unbekannte Zeitstempel werden übersprungen
- Ergebnisse werden nur aggregiert protokolliert und diagnostiziert

## HA-Media-Player nach erfolgreicher Serverlöschung

Die Option entfernt nicht blind eine Entity. Der Sicherheitsvertrag lautet:

1. Emby-`DELETE /Devices` war für den konkreten historischen `Id`-Datensatz erfolgreich.
2. EMBi liest `/Devices` erneut.
3. Kein verbleibender Datensatz verwendet dieselbe `ReportedDeviceId.AppName`-Identität.
4. Der Player ist nicht aktiv.
5. Exakt dieser Player-Key wird für den nächsten Config-Entry-Reload vorgemerkt.
6. Nach dem Unload ist kein Entity-State vorhanden.
7. Die Registry-Entität gehört zur Plattform `emby` und zum gleichen Config Entry.
8. Erst dann wird sie entfernt.

Bleibt ein weiterer Historieneintrag derselben Client-/App-Kombination bestehen, bleibt auch der HA-Media-Player erhalten. Andere App-Varianten derselben rohen `ReportedDeviceId` werden nicht entfernt.

## Teilerfolg

Ein Fehler stoppt die übrigen Datensätze nicht. Es existiert bewusst keine maximale Löschzahl. Der Lauf meldet aggregiert:

- Kandidaten
- erfolgreiche Löschungen
- fehlgeschlagene Löschungen
- übersprungene aktive Player
- übersprungene unbekannte Zeitstempel
- vorgemerkte Registry-Entfernungen

## Wiederkehrende Clients

Ein später verwendeter Client kann sich erneut auf Emby registrieren. Die automatische Bereinigung trägt ihn nicht geräteweit in die Ignorierliste ein. Der Media-Player kann deshalb bei erneuter Nutzung wieder entstehen.
