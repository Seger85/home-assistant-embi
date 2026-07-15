# 01 – Domain and State Model

## 1. Core records

EMBi must distinguish four record types.

### 1.1 Emby server history record

One row returned by the Emby server device-history/API surface. It can represent a physical playback device, app variant, browser session, past login, technical API client or duplicate/historical record.

### 1.2 Logical player identity

A stable EMBi identity representing the exact combination required to create one Home Assistant media-player entity. The storage format may be normalized in 0.9.0, but migration must preserve entity identity.

### 1.3 Home Assistant entity registration

The entity-registry record belonging to the EMBi config entry, including entity ID, custom name, enabled/disabled state, hidden state and unique identity.

### 1.4 Runtime player state

A currently loaded Home Assistant state such as playing, paused, idle, off, unavailable or unknown. Absence from the state machine does not prove that an entity is orphaned.

## 2. Independent state dimensions

| Dimension | Values |
|---|---|
| Emby presence | present / absent / unknown |
| EMBi visibility | visible / hidden |
| HA registry | present / absent |
| HA registry enablement | enabled / disabled / not applicable |
| HA runtime | loaded / not loaded |
| Playback | playing / paused / non-playing / unknown |
| Client class | playback / technical / unknown |
| User relation | one user / multiple users / no user |
| Cleanup safety | removable / protected / requires refresh |
| Migration state | native 0.9 / migrated / unresolved legacy |

## 3. Removal eligibility from Home Assistant

A player is currently removable when all are true:

1. it belongs to the active EMBi config entry,
2. it is not playing,
3. it is not paused,
4. its exact identity can be stored as hidden in EMBi,
5. the removal can be verified after reload.

The player may still be present on the Emby server. In that case the action hides it in EMBi, removes the Home Assistant entity and verifies no recreation. It does not delete the Emby server history record.

## 4. Playback protection

Removal is blocked for `playing` and `paused`.

Potentially removable after fresh verification: `idle`, `off`, `standby`, `unavailable`, or no runtime state when the registry and server relationship are understood.

Unknown playback requires a refresh. If still unknown, fail closed.

## 5. Disabled Home Assistant entities

A disabled entity is still valid, may still match a current Emby client and may have no runtime state. It must not be classified as orphaned because of that absence.

When a disabled entity still has an Emby match, offer:

- Enable in Home Assistant
- Hide in EMBi

Do not offer orphan cleanup.

## 6. Hidden player lifecycle

### Hide and remove

1. refresh current Emby records,
2. refresh entity-registry metadata,
3. refresh playback state,
4. block if playing/paused,
5. store exact EMBi hidden rule,
6. unload/reload through supported integration APIs,
7. remove the entity registration if still present and owned by EMBi,
8. reload again when needed,
9. verify that the entity does not return,
10. report success only after verification.

### Restore

1. remove the exact hidden rule,
2. reload the integration,
3. confirm the entity is recreated or re-enabled,
4. preserve the existing entity ID when the registry record still exists,
5. report the final entity ID.

## 7. User grouping

- exactly one known user → group under that user,
- more than one known user → group under **Shared devices**,
- no user → group under **Without user assignment**,
- list all known users on a shared device,
- show the latest known user separately where available.

User grouping is presentation metadata and must not change technical identity.

## 8. Technical access classification

Technical access means a client connected to the Emby API but is not a normal playback client.

Classification order:

1. explicit playback capability or observed playback → playback client,
2. explicit API-only metadata → technical access,
3. repeated non-playback API behavior with no playback capability → technical access,
4. insufficient evidence → unknown client.

Unknown clients must not be silently classified as technical.

## 9. Decision table

| Emby present | HA enabled | Runtime | Playback | User action |
|---|---:|---|---|---|
| yes | yes | loaded | playing/paused | removal blocked |
| yes | yes | loaded | non-playing | hide in EMBi + remove from HA allowed |
| yes | no | not loaded | none | enable or hide in EMBi |
| no | yes | loaded | non-playing | remove from HA allowed |
| no | no | not loaded | none | remove registry entry allowed |
| unknown | any | any | any | refresh; fail closed if unresolved |
| yes/no | any | any | playing/paused | removal blocked |
