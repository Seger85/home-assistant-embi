# EMBi auf dem Dashboard

Die Beispiele zeigen zwei Bereiche: eine Übersicht über die Mediathek und die gerade aktiven Player. Du kannst sie an dein eigenes Dashboard und Theme anpassen. Die Integration selbst benötigt keine zusätzlichen Frontend-Karten.

## Mit normalen Home-Assistant-Karten

Öffne [dashboard-native.yaml](../examples/dashboard-native.yaml), kopiere den Inhalt und füge im Dashboard eine **Manuelle Karte** hinzu. Ersetze `media_player.dein_emby_player` durch die tatsächliche Entitäts-ID eines EMBi-Players. Die Sensor-IDs findest du ebenfalls unter den Entitäten der Integration. Für weitere Player kannst du zusätzliche Mediensteuerungskarten anlegen.

## Automatische Playeranzeige

Das Beispiel [dashboard-embi.yaml](../examples/dashboard-embi.yaml) benötigt diese separat installierbaren Frontend-Erweiterungen:

- [Mushroom](https://github.com/piitaya/lovelace-mushroom) für die Übersicht.
- [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) für die dynamische Playerliste.
- [mini-media-player](https://github.com/kalkih/mini-media-player) für die Wiedergabekarten.

Installiere sie über HACS und lade das Frontend neu. Füge anschließend den YAML-Inhalt als manuelle Karte ein. Prüfe die drei Sensor-IDs; bei eigenen Umbenennungen oder mehreren Servern können sie abweichen.

Die Kopfzeile unterscheidet null, einen und mehrere aktive Player. Wiedergabe und Pause zählen als aktiv. Sind alle vorhandenen Player nicht erreichbar oder noch unbekannt, zeigt sie einen entsprechenden Hinweis. Pausierte und laufende Player erhalten dieselbe Darstellung. Ohne aktive Player wird die Wiedergabeliste ausgeblendet.

Die Auswahl verwendet die tatsächliche Integrationszuordnung über `integration_entities('emby')`. Umbenannte Player funktionieren damit weiterhin; ein bestimmter `media_player.emby_`-Namensanfang ist nicht nötig. Bei mehreren EMBi-Servern enthält die Playerliste alle zugehörigen Player. Möchtest du einen einzelnen Server anzeigen, wähle dessen Entitäten gezielt aus.

Die Kopfzeile zählt **Player**, nicht unterschiedliche Benutzer. Für letztere kannst du zusätzlich `sensor.emby_users_watching` anzeigen. Dieser Sensor berücksichtigt nur laufende Wiedergabe und zählt jeden Benutzer einmal.

Die Beispiele enthalten keine privaten Serveradressen, Gerätekennungen oder API-Schlüssel. Farben und Rundungen stammen aus deinem HA-Theme; die tatsächliche Darstellung hängt außerdem von den installierten Kartenversionen ab.
