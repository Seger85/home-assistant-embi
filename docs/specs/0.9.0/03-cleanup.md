# 03 – Cleanup

## 1. One cleanup page

The root menu contains one item: **Cleanup**.

The page contains:

1. statistics and explanation,
2. automatic Emby server-history cleanup,
3. manual Emby server-history check,
4. Home Assistant player removal,
5. last cleanup run.

There are no separate root menu items for these functions. Result lists and one final destructive confirmation may open as dialogs.

## 2. Cleanup statistics

```text
69 devices in Emby server device history
30 players in Home Assistant
39 additional historical devices in Emby server device history
0 server-history devices currently safe to delete
28 Home Assistant players currently removable
2 protected by active playback
```

The difference is descriptive, not a deletion count. Home Assistant removal count is independent of server-history deletion count.

## 3. Explanation of Emby server records

> Emby stores every device and app connection that has used the server, including active, inactive and technical access. A physical device can appear more than once because of different apps or sign-ins. Display names can also be adjusted in the Emby server under Devices.

Do not assume a particular naming convention.

## 4. Automatic server-history cleanup

```text
Automatically clean old Emby records              [ off ]

Delete records older than
[ 1 year – 365 days                         v ]

Also remove matching Home Assistant players       [ on/off ]
```

Automatic cleanup on: EMBi regularly checks old records and removes only records satisfying all safety rules.

Off: manual checks remain available.

Age options: 7, 30, 90, 180, 365 days and Custom. Custom displays the exact stored number. Do not show “numeric value is the source of truth”.

Matching HA removal explanation:

> After a server-history record is deleted, EMBi also removes a matching Home Assistant player when no remaining Emby record needs it and it is not playing or paused.

New installations default off; upgrades preserve the stored value.

## 5. Manual server-history check

```text
Manual check

0 records currently safe to delete
1 active player protected
39 other records do not meet the deletion rules

[ Check now ]
```

Use freshly loaded server data.

### Zero candidates

Do not show an empty selector.

```text
No matching records found.

Of 69 Emby server-history records:
- 0 are older than 365 days and safe to delete
- 1 is protected by active playback
- 39 do not meet all cleanup rules
- 0 have no valid activity date

Nothing was changed.
```

### Candidates present

Group by understandable user/device context and show last use. The user selects records and presses one clearly named deletion button.

## 6. Final server-deletion confirmation

Exactly one confirmation:

```text
Delete 3 Emby server-history records?

The selected device-history records will be removed from the Emby server.
User accounts, media, libraries and playback history are not deleted.

[ Back ]
[ Delete permanently ]
```

## 7. Home Assistant player removal

This section intentionally allows removing normal EMBi players from Home Assistant, not only orphans.

```text
Home Assistant players

30 players in Home Assistant
28 currently removable
2 protected by playing or paused playback

[ Manage Home Assistant players ]
```

The manager lists all EMBi players in the same user-oriented grouping as Devices & players.

### Removable player

```text
Emby for iOS · iPhone
User: Gerry
media_player.emby_iphone_12
Ready

[ Remove from Home Assistant ]
```

### Protected player

```text
Android TV · Living-room television
User: Gerry
media_player.emby_bravia_vh1
Playing

Stop playback before removing this player.
```

## 8. Meaning of Remove from Home Assistant

For a non-playing selected player, EMBi performs one safe operation:

1. refresh Emby presence,
2. refresh HA registry metadata,
3. refresh playback state,
4. block if playing or paused,
5. store the exact player as hidden in EMBi,
6. remove/unload the HA entity using supported APIs,
7. reload EMBi,
8. verify that the entity does not return,
9. report success only after verification.

The Emby server device-history record remains.

## 9. Final Home Assistant removal confirmation

Exactly one final confirmation:

```text
Remove 2 players from Home Assistant?

The players will be hidden in EMBi and removed from Home Assistant.
They remain in the Emby server device history and can be restored later
under Devices & players.

[ Back ]
[ Remove 2 players ]
```

No confirmation switch.

## 10. Disabled entities

A disabled but valid EMBi entity is shown as disabled and still reported by Emby, with actions to enable in Home Assistant or hide in EMBi and remove. It is not shown as an orphan.

## 11. Actual orphan case

Only when a fresh check proves no server match:

```text
Old iPhone
media_player.emby_old_iphone
Not reported by the Emby server
Stored only in Home Assistant

[ Remove from Home Assistant ]
```

## 12. Last cleanup run

Shown exactly once on this page.

```text
Last cleanup run

Successful · 15 July 2026, 20:40
0 deleted · 1 protected · no errors
Next run: automatic cleanup disabled
```

## 13. Failure handling

If verification fails, do not report success. Show the friendly name and entity ID, keep technical detail in diagnostics and never silently leave a partially removed player.
