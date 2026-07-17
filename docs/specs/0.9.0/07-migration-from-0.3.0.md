# 07 – Migration from 0.3.0

## 1. Objective

Upgrade an existing 0.3.0 installation without changing the user's effective behavior unless the user later applies a new setting.

## 2. Must preserve

- config entry data,
- entity unique IDs,
- existing entity IDs,
- Home Assistant custom entity names,
- disabled and hidden entity states,
- aliases, areas and labels,
- ignored exact player/app rules,
- ignored whole-device rules,
- unresolved legacy rules,
- cleanup enabled/disabled state,
- automatic cleanup state,
- automatic and manual thresholds,
- remove-matching-HA-player setting,
- last cleanup report where compatible.

## 3. Must not happen automatically

- enable or disable automatic cleanup,
- delete Emby server records,
- delete Home Assistant entities,
- enable disabled entities,
- disable enabled entities,
- expose technical clients,
- hide current playback clients,
- rename entity IDs,
- overwrite custom names,
- collapse two existing unique IDs into one,
- create duplicate entities.

## 4. Disabled entity correction

0.3.0 may treat a disabled entity with no runtime state as a registry-only cleanup candidate.

0.9.0 migration must read the entity registry, retain disabled status, match the unique identity to current Emby records, classify it as valid when a current match exists, exclude it from orphan cleanup and show it as Disabled in Home Assistant.

## 5. Technical access migration

Existing technical-client entities remain unchanged and visible after upgrade if they were visible before. The new technical-access switch reflects the effective preserved state. No technical entity is deleted because the new-install default is off.

## 6. Player-selection migration

Map current all-device, selected-device and active-playback-only modes, exact ignored player keys, ignored reported-device IDs and unresolved IDs.

Required behavior:

> The same players that appear immediately before the upgrade must appear immediately after the upgrade, except for a player currently impossible to load for reasons unrelated to migration.

## 7. Age values

Preserve exact numeric values including unusual values such as 364. Display a preset only when exact; otherwise use Custom. Do not change 364 to 365.

## 8. Storage version

Introduce an explicit schema version. Migration must be idempotent, logged once, safe after interrupted startup, non-destructive and visible in diagnostics. Partial migration causes a clear setup failure or repair notice rather than silent defaults.

## 9. Rollback compatibility

Test downgrade behavior from 0.9.0 to 0.3.0 in a disposable environment. If safe downgrade is impossible, document backup restore as required.

## 10. Required fixtures

- default options,
- all-device mode,
- selected-device mode,
- active-only mode,
- exact app ignore,
- whole-device ignore,
- unresolved legacy rule,
- cleanup 364 and 365,
- automation on and off,
- disabled valid entity,
- custom entity name,
- technical clients,
- duplicate-friendly-name entities.
