# EMBi auf dem Dashboard

[English](dashboard.en.md)

1. Schalte **Aktive Player**, **Filme**, **Serien** und **Episoden** in den EMBi-Optionen ein.
2. Installiere für die erweiterten Karten [Mushroom](https://github.com/piitaya/lovelace-mushroom), [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) und [mini-media-player](https://github.com/kalkih/mini-media-player) über HACS. Lade anschließend das Frontend neu.
3. Bearbeite dein Dashboard, füge eine **Manuelle Karte** hinzu und kopiere ein vollständiges Beispiel. Alternativ gibt es [alle Karten als gemeinsamen Stapel](../examples/dashboard-embi.yaml).
4. Ersetze bei Bedarf die Sensor-IDs. Die Playerliste gehört zum selben Integrationseintrag wie der Sensor für aktive Player; umbenannte Player werden ebenfalls gefunden.

EMBi und die Mediathekskarte benötigen keine zusätzlichen Frontend-Erweiterungen. Alternativ kannst du [normale HA-Karten](../examples/dashboard-native.yaml) verwenden. Die Original-Screenshots zeigen ein deutsches Dashboard mit eigenem Theme. Farben und Rundungen hängen von deinem Theme und den Kartenversionen ab. Ausgeblendete Player fehlen in der Karte, zählen im serverweiten Sensor aber mit. Wiedergabe und Pause zählen als aktive Player; schauende Benutzer zählt nur unterschiedliche Benutzer mit laufender Wiedergabe. Nicht verfügbar bedeutet nicht null.

### Aktive Player

![Aktive Player](../docs/images/active-players.jpg)

<details>
<summary>Vollständigen Karten-Code anzeigen</summary>

```yaml
double_tap_action:
  action: none
entity: sensor.emby_active_players
hold_action:
  action: none
icon: mdi:cast-connected
multiline_secondary: true
primary: '{% set count = states(''sensor.emby_active_players'') %}

  {% if count in [''unknown'', ''unavailable''] %}Aktive Emby-Player derzeit nicht verfügbar

  {% elif count | int == 1 %}1 Emby-Player ist aktiv

  {% else %}{{ count | int }} Emby-Player sind aktiv{% endif %}'
secondary: Was läuft gerade? Wiedergabe und Pause im Überblick.
tap_action:
  action: more-info
type: custom:mushroom-template-card
```

</details>

### Mediathek

![Mediathek](../docs/images/library-counts.jpg)

<details>
<summary>Vollständigen Karten-Code anzeigen</summary>

```yaml
entities:
- entity: sensor.emby_movie_count
  icon: mdi:movie
  name: Filme
- entity: sensor.emby_tv_series_count
  icon: mdi:television-classic
  name: Serien
- entity: sensor.emby_tv_episode_count
  icon: mdi:television-play
  name: Episoden
title: Meine Emby-Mediathek
type: entities
```

</details>

### Player mit Wiedergabe oder Pause

![Player mit Wiedergabe oder Pause](../docs/images/media-players.jpg)

<details>
<summary>Vollständigen Karten-Code anzeigen</summary>

```yaml
card:
  show_header_toggle: false
  state_color: true
  type: entities
filter:
  template: "{% set entry = config_entry_id('sensor.emby_active_players') %}\n{% set ns = namespace(rows=[]) %}\n{% for player in expand(config_entry_entities(entry) if entry else []) | selectattr('domain', 'eq', 'media_player') | list %}\n  {% if player.state in ['playing', 'paused'] %}\n    {% set ns.rows = ns.rows + [{\n      'entity': player.entity_id,\n      'type': 'custom:mini-media-player',\n      'artwork': 'material',\n      'hide': {'volume': true, 'next': true, 'prev': true},\n      'tap_action': {'action': 'more-info'}\n    }] %}\n  {% endif %}\n{% endfor %}\n{{ ns.rows }}"
show_empty: false
sort:
  method: friendly_name
type: custom:auto-entities
```

</details>
