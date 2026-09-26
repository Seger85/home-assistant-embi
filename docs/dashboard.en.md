# EMBi dashboard examples

[Deutsch](dashboard.md)

1. Enable **Active players**, **Movies**, **TV series** and **Episodes** in the EMBi options.
2. Install [Mushroom](https://github.com/piitaya/lovelace-mushroom), [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) and [mini-media-player](https://github.com/kalkih/mini-media-player) through HACS for the enhanced cards. Reload your browser.
3. Edit your dashboard, add a **Manual card**, and paste one complete example below. Alternatively, paste [the combined stack](../examples/dashboard-embi.en.yaml).
4. Replace sensor IDs with the actual IDs of your integration. The player list uses the integration entry associated with the active-player sensor, including renamed media players.

No frontend extensions are needed for EMBi itself or the library card. You can also use the standard [native-card example](../examples/dashboard-native.yaml). The screenshots show an original German dashboard; theme and card versions affect the appearance. Hidden player entities are not shown in the card, even when they count in the server-wide sensor. Playing and paused players count as active; users watching counts distinct users with ongoing playback only. Unavailable is not zero.

### Active players

![Active players](../docs/images/active-players.jpg)

<details>
<summary>Copy the complete card YAML</summary>

```yaml
double_tap_action:
  action: none
entity: sensor.emby_active_players
hold_action:
  action: none
icon: mdi:cast-connected
multiline_secondary: true
primary: |-
  {% set count = states('sensor.emby_active_players') %}
  {% if count in ['unknown', 'unavailable'] %}Active Emby players currently unavailable
  {% elif count | int == 1 %}1 Emby player is active
  {% else %}{{ count | int }} Emby players are active{% endif %}
secondary: What is playing? Playing and paused devices at a glance.
tap_action:
  action: more-info
type: custom:mushroom-template-card
```

</details>

### Library counts

![Library counts](../docs/images/library-counts.jpg)

<details>
<summary>Copy the complete card YAML</summary>

```yaml
entities:
- entity: sensor.emby_movie_count
  icon: mdi:movie
  name: Movies
- entity: sensor.emby_tv_series_count
  icon: mdi:television-classic
  name: TV series
- entity: sensor.emby_tv_episode_count
  icon: mdi:television-play
  name: Episodes
title: My Emby library
type: entities
```

</details>

### Playing and paused players

![Playing and paused players](../docs/images/media-players.jpg)

<details>
<summary>Copy the complete card YAML</summary>

```yaml
card:
  show_header_toggle: false
  state_color: true
  type: entities
filter:
  template: |
    {% set entry = config_entry_id('sensor.emby_active_players') %}
    {% set ns = namespace(rows=[]) %}
    {% for player in expand(integration_entities('emby')) | selectattr('domain', 'eq', 'media_player') | list %}
      {% if entry and config_entry_id(player.entity_id) == entry and player.state in ['playing', 'paused'] %}
        {% set duration = player.attributes.get('media_duration') %}
        {% set position = player.attributes.get('media_position') %}
        {% set updated = as_timestamp(player.attributes.get('media_position_updated_at'), none) %}
        {% set elapsed = ([as_timestamp(now()) - updated, 0] | max) if player.state == 'playing' and updated is not none else 0 %}
        {% set invalid_runtime = duration is not number or position is not number or position < 0 or position + elapsed > duration %}
        {% set ns.rows = ns.rows + [{
          'entity': player.entity_id,
          'type': 'custom:mini-media-player',
          'artwork': 'material',
          'hide': {'controls': false, 'volume': true, 'next': true, 'prev': true, 'runtime': invalid_runtime, 'info': false},
          'tap_action': {'action': 'more-info'}
        }] %}
      {% endif %}
    {% endfor %}
    {{ ns.rows }}
show_empty: false
sort:
  method: friendly_name
type: custom:auto-entities
```

</details>
