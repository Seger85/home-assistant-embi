# 00 – Master Specification

## 1. Product objective

EMBi adds Emby clients to Home Assistant as media-player entities and provides safe, understandable controls for:

1. deciding which Emby clients appear in Home Assistant,
2. grouping clients by the people who use them,
3. distinguishing playback clients from technical API access,
4. cleaning old records from the Emby server device history,
5. removing unwanted EMBi players from Home Assistant without them returning after reload,
6. preserving existing installations during the upgrade from 0.3.0.

The user interface must be understandable without knowledge of Emby API records, Home Assistant registry internals, ReportedDeviceId values, Config Entry IDs or unique IDs.

## 2. Scope of 0.9.0

Included:

- radically simplified options flow,
- compact status numbers,
- user-oriented player grouping,
- shared-device grouping with named users,
- technical-access grouping,
- clear Home Assistant entity names and entity IDs,
- one combined cleanup area,
- one global draft and review workflow,
- safe removal of non-playing Home Assistant players,
- protection of playing and paused players,
- safe restoration of hidden players,
- correct handling of disabled Home Assistant entities,
- migration from 0.3.0,
- diagnostics and logging improvements,
- complete German and English UI copy,
- community-oriented README and documentation,
- stable 0.9.0 release through HACS/GitHub.

## 3. Explicit non-scope

Not included in 0.9.0:

- library item-count sensors,
- film, series, episode or collection sensors,
- watch-history sensors,
- YAML-sensor replacement,
- dashboards,
- media statistics platform,
- unrelated refactors without a requirement ID.

These are reserved for 1.0.0 or later.

## 4. Main menu

The root options page contains only:

1. **Devices & players**
2. **Cleanup**
3. **Review changes** – shown only when a draft differs from persisted options

There is no separate About EMBi, Status & Help, Server cleanup, Automatic cleanup, Home Assistant cleanup or Last cleanup run root item. The standard Home Assistant `?` help action links to the repository documentation.

## 5. Compact root statistics

The root page shows clearly separated values:

- devices in Emby server device history,
- players in Home Assistant,
- currently playing or paused players,
- players currently removable from Home Assistant,
- automatic-cleanup status.

Example:

```text
69 devices in Emby server device history
30 players in Home Assistant
2 protected by active playback
28 currently removable from Home Assistant
Automatic cleanup: off
```

“Removable from Home Assistant” means EMBi can hide the selected player, remove the Home Assistant entity and verify that it stays removed. It does not mean the Emby server history record is deleted.

## 6. Product vocabulary

Use:

- Emby server device history
- Home Assistant player
- user
- shared device
- technical access
- visible / hidden in EMBi
- enabled / disabled in Home Assistant
- playing / paused / ready
- remove from Home Assistant
- delete from Emby server history

Do not expose as normal UI concepts:

- ReportedDeviceId
- player key
- Config Entry ID
- platform ownership
- unique ID
- entity registry
- unload
- revalidation ambiguity
- queue
- TOCTOU

## 7. UX principles

- Fewer pages and fewer confirmations.
- Explanations directly beside the relevant switch or action.
- No confirmation switch for normal draft changes.
- Exactly one final confirmation for a destructive action.
- A visible back action preserves the draft.
- The top-left X cancels the whole session and discards the draft.
- Full Home Assistant entity IDs are shown where they help the user search.
- UUIDs and internal identifiers are hidden by default.
- Desktop is the primary acceptance format.
- Mobile is checked at the end for basic usability and overflow only.

## 8. Current live reference system

The specification was created against this verified baseline:

- Home Assistant Core 2026.7.2
- Home Assistant OS 18.1
- Supervisor 2026.07.3
- EMBi 0.3.0
- config entry loaded
- 69 Emby server device-history records
- 30 enabled and loaded EMBi media-player entities
- no current Home Assistant registry orphan
- automatic cleanup disabled
- manual and automatic cleanup thresholds: 365 days
- Home Assistant removal after matching server deletion: persisted enabled
- latest cleanup run completed without deletion

The numbers are test data, not hardcoded product assumptions.

## 9. Definition of done

EMBi 0.9.0 is done only when:

- all blocker requirements in `requirements.yaml` pass,
- migration preserves existing IDs and names,
- no disabled-but-valid entity is falsely offered as orphaned,
- non-playing players can be removed through one user action,
- playing and paused players cannot be removed,
- removed players do not return after reload,
- hidden players can be restored,
- server-history cleanup and Home Assistant player removal are clearly separated,
- German and English copy is complete,
- CI passes,
- a stable GitHub release `v0.9.0` is published,
- the release is not a draft or prerelease,
- HACS release structure is valid,
- release assets and checksum are published.
