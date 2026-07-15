# 04 – Options Flow and Navigation

## 1. Draft model

Normal settings are edited in one in-memory draft:

- player visibility,
- user master switches,
- global player-mode switches,
- technical-access visibility,
- automatic cleanup,
- cleanup thresholds,
- remove-matching-HA-player option.

Nothing is persisted until Apply changes.

## 2. Root page without draft

```text
EMBi settings

69 Emby history devices
30 Home Assistant players
Automatic cleanup: off

Devices & players                                >
Cleanup                                          >
```

## 3. Root page with draft

```text
EMBi settings

69 Emby history devices
30 Home Assistant players
Automatic cleanup: off

Devices & players                                >
Cleanup                                          >

-----------------------------------------------

3 changes to review                              >
```

Do not show counters such as selection: 0, app rules: 1 or device rules: 1.

## 4. Review changes page

Show semantic before/after changes.

```text
Review changes

Automatically clean old Emby records
Off → On

Cleanup age
364 days → 365 days

Apple TV · Suthan
Show in Home Assistant → Hide from Home Assistant

[ Discard changes ]
[ Apply changes ]
```

## 5. Apply

Apply changes:

1. revalidate the draft against current data,
2. persist normal options,
3. perform required reloads,
4. verify player removals/restorations,
5. display a result summary,
6. identify failed items clearly.

If a player became playing or paused after the draft was created, skip that player and report it as protected.

## 6. Discard

Discard resets the complete draft to persisted options, performs no reload and deletes nothing.

## 7. X behavior

The top-left X cancels the complete options session, discards all unsaved normal changes, runs no second confirmation and performs no destructive action.

## 8. Back behavior

Every normal child page has a visible bottom action:

- Back to EMBi settings
- Back to Devices & players
- Back to Cleanup

Back preserves the draft.

## 9. Destructive actions

Destructive actions are not normal draft state.

Examples:

- delete server-history records,
- remove selected Home Assistant players immediately.

Rules:

- hide them while unresolved normal draft changes exist, or require Apply/Discard first,
- use a fresh check,
- use one final confirmation,
- execute immediately,
- return a verified result.

## 10. No double confirmation

Prohibited: confirmation switch, then OK, then global Apply.

Allowed: review targets, press one clearly named destructive button, receive a verified result.

## 11. Native Home Assistant UI constraints

Use native Config/Options Flow components. Do not add custom frontend code merely to color individual buttons. Semantic separation takes priority over custom coloring. No fragile CSS or frontend patching.

## 12. Page count rule

Use a child page only when a searchable list is required, more than five records must be managed, destructive targets must be reviewed or record-level detail is necessary. Otherwise keep the control on the main functional page.
