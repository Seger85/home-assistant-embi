# EMBi – Emby integration for Home Assistant

**English** · [Deutsch](README.de.md)

**Bring your Emby players and library into Home Assistant.** See what is playing, control supported clients and choose which players and sensors appear. Communication stays between Home Assistant and your Emby server.

## Features

- **Player controls:** play, pause, stop and seek where the Emby client supports remote control; display titles, artwork and progress.
- **Flexible player visibility:** keep known players or show them only while playing or paused. Choose whether to add new clients automatically.
- **Seven optional sensors, configured through the integration UI. No YAML required.** Library counts, active players and users watching are available as separate entities.
- **Review before saving:** ordinary settings are collected in a draft and shown together before you apply them.
- **Optional device-history cleanup:** remove old Emby client records manually or on a schedule. Automatic cleanup is off for new installations.
- **English and German setup, options and sensor translations.** Home Assistant handles the language selection. Custom entity names are preserved.

## Install with HACS

Requires **Home Assistant 2026.7.2 or newer**, an accessible Emby server and an Emby API key.

1. In HACS, add `https://github.com/Seger85/home-assistant-embi` as a custom repository, category **Integration**.
2. Install **Emby Integration - EMBi** and restart Home Assistant.
3. Open **Settings → Devices & services → Add integration**, then search for **EMBi**.
4. Enter your server address, port and API key. Create the key in your Emby server dashboard. Enable SSL only for a working HTTPS connection.
5. Open the integration options to choose players, sensors and cleanup settings.

EMBi uses the `emby` domain and replaces Home Assistant's built-in Emby integration. The warning that a custom integration overrides a core component is therefore expected. Existing entity IDs and automations do not need renaming for this update.

## Sensors: players are not people

| Default entity ID | Meaning |
|---|---|
| `sensor.emby_active_players` | Distinct Emby players currently playing or paused, including players hidden from the HA player list |
| `sensor.emby_users_watching` | Distinct users with playback in progress; paused sessions do not count |
| `sensor.emby_movie_count` | Movies |
| `sensor.emby_tv_series_count` | TV series |
| `sensor.emby_tv_episode_count` | TV episodes |
| `sensor.emby_album_count` | Music albums |
| `sensor.emby_song_count` | Music tracks |

One user can use several players. A player is identified by its Emby device ID and client app; repeated sessions for that combination count once. Different apps may be separate players.

All seven sensors are selected on a new installation. **Upgrades preserve your selection:** enable **Active players** in **EMBi → Options → Emby sensors** if you want the new sensor. The integration creates the sensors without YAML. Dashboard examples below use optional card YAML only.

A confirmed empty result is `0`. Missing or ambiguous data produces an unavailable sensor instead of a misleading zero. Library counts and users watching normally refresh every 60 seconds, with separate availability. Active players follows session updates directly, without additional HTTP polling.

Custom names are preserved. Actual entity IDs may differ after renaming, a naming collision or adding multiple servers. EMBi does not take over unrelated template or YAML sensors.

## Player visibility and safe cleanup

**Keep players** retains known players between sessions. A disconnected client may be unavailable; that alone is not a reason to delete it. **Show only playing or paused players** makes player entities follow activity. A requested removal waits until inactivity is confirmed.

**Emby device-history cleanup is at your own risk.** It removes selected old device/client records, never libraries, media files or user accounts. A removed client may need to sign in again. Optionally, EMBi also removes the corresponding EMBi player entries from Home Assistant. Automatic cleanup is disabled on a new installation.

Playing and paused clients are protected. Failed requests, ambiguous responses and missing timestamps are not treated as proof of inactivity. Emby exposes checking and deletion as separate requests, so a small race window between the final check and deletion cannot be eliminated completely. See the [cleanup guide](docs/server-cleanup.md) (German).

## Dashboard examples

Enable the required sensors first and adjust their IDs if necessary. The player list follows the same server as `sensor.emby_active_players`; replace that ID in **both** relevant cards if yours differs. Hidden HA players are absent from the card list but still count in the server-wide sensor.

For the first and third examples, install these community frontend cards through HACS: [Mushroom](https://github.com/piitaya/lovelace-mushroom), [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) and [mini-media-player](https://github.com/kalkih/mini-media-player). The library card uses Home Assistant's built-in entities card. EMBi itself does not require these frontend extensions. [Dashboard instructions](docs/dashboard.en.md).

These individually cropped, unmodified screenshots show a German dashboard with a custom theme. Your colours, rounded corners and player count may differ. The examples below use English labels and the new numeric player sensor.

### Active players

![Active players](docs/images/active-players.jpg)

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

![Library counts](docs/images/library-counts.jpg)

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

![Playing and paused players](docs/images/media-players.jpg)

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
    {% for player in expand(config_entry_entities(entry) if entry else []) | selectattr('domain', 'eq', 'media_player') | list %}
      {% if player.state in ['playing', 'paused'] %}
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

## Updates and recovery

Back up Home Assistant before a major update. Existing EMBi players and sensors keep their identities. Newly created players include their integration identity to avoid collisions across servers. Downgrading through HACS alone may not restore an older registry layout; restore your pre-update backup for a full rollback. Deleted Emby history requires a suitable Emby backup to recover.

## Help and project information

- [German documentation](README.de.md): configuration, cleanup and troubleshooting.
- [Dashboard examples](docs/dashboard.en.md), [architecture](docs/architecture.md), [contributing](CONTRIBUTING.md), [releases](RELEASING.md), [changelog](CHANGELOG.md), [workflow maintenance](docs/workflows.md).
- Report problems or suggestions in [GitHub Issues](https://github.com/Seger85/home-assistant-embi/issues). Include EMBi, HA and Emby versions and your client app. Check diagnostics and screenshots for personal information before sharing.

GitHub and HACS use this English README as the main description. Use the language link at the top for German; this README does not automatically switch with Home Assistant's language.

Community project by Seger, based on the Home Assistant Emby integration and pyemby. Not an official Emby or Home Assistant product. [Apache-2.0 license](LICENSE); [attribution](NOTICE.md).
