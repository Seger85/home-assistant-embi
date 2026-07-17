# 02 – Devices and Players

## 1. Page goal

The page answers:

1. Which people use which Emby players?
2. Which player appears in Home Assistant?
3. Which Home Assistant entity belongs to it?
4. How can it be hidden or restored?

## 2. Page structure

```text
Devices & players

30 players in Home Assistant
1 currently playing
8 known Emby users

Only show during playback                         [ off ]
Automatically show new players                    [ on ]

[ Search user, device, app or entity ID … ]

Users
Michael                                           >
Gerry                                             >
Nuno                                              >

Shared devices                                    >
Without user assignment                           >
Technical access                                  >
```

## 3. Global switches

### Only show during playback

Off: Selected players remain available in Home Assistant even when nothing is playing.

On: Players are loaded only while playing or paused.

Migration must preserve the current 0.3.0 mode.

### Automatically show new players

On: New playback clients are shown automatically.

Off: New playback clients remain hidden until enabled here.

Technical accesses are not automatically shown on new installations.

## 4. User row

Example:

```text
Michael
2 players · last used 14 July 2026
```

## 5. User page

```text
Michael

Show all players for Michael                      [ on ]

Android TV · Living-room television               [ on ]
Home Assistant: Emby Television Michael
media_player.emby_fernseher_michael
Last used 14 July 2026

Emby for Android · Living-room television         [ on ]
Home Assistant: Emby Television Michael
media_player.emby_fernseher_michael_2
Last used 12 July 2026

[ Back to Devices & players ]
```

## 6. User master switch

On: the user's players are eligible to appear and individual player switches remain effective.

Off: all players assigned only to this user are hidden; individual child choices are preserved internally and restored when re-enabled.

Shared devices are managed in Shared devices, not by a single-user master switch.

## 7. Player row information

Required order:

1. app/client name,
2. understandable device name,
3. Home Assistant display name,
4. full entity ID,
5. last-use information,
6. current playback/status,
7. visibility switch.

Do not use a UUID as the primary label.

## 8. Naming rules

Priority:

1. Home Assistant custom entity name,
2. Emby server display name,
3. Emby device name,
4. app/client name,
5. user name as clarifying suffix,
6. short disambiguator only when still ambiguous.

Never overwrite a user-defined Home Assistant name.

## 9. Shared devices

A device moves to Shared devices when more than one known Emby user has used it.

```text
Living-room television
Used by Gerry and Andji
Last used by Gerry
Android TV
Home Assistant: Emby TV Living Room
media_player.emby_bravia_vh1
```

List all known users by name. For long lists, show a compact line plus a complete detail list.

## 10. Without user assignment

Contains players without a reliable user relation. Do not guess a user from the entity ID.

## 11. Technical access

Shown only when records exist.

```text
Technical access

5 applications accessed the Emby server through its API.
They are not normal playback devices.

Home Assistant
EMBi
Homarr
Windmill FSK/Mini-Series
WhatsApp Newsletter
```

Switch:

```text
Show technical access as Home Assistant players   [ off ]
```

Rules:

- new installations: off,
- upgrades: preserve existing technical entities,
- do not delete existing entities during migration,
- uncertain clients appear under Unknown clients.

## 12. Search

Match user name, Emby display name, device name, app/client name, Home Assistant custom name and full entity ID. UUID search is not required for normal use.

## 13. Sorting

Top-level:

1. users with currently playing/paused clients,
2. other named users alphabetically,
3. shared devices,
4. without user assignment,
5. technical access,
6. unknown clients.

Within a user: playing, paused, recently used, other visible, hidden.

## 14. Toggle behavior

Turning a non-playing player off creates a draft change and does not delete immediately. Review changes shows “Show → Hide”. After Apply, EMBi stores the hidden rule, removes the HA entity safely, reloads and verifies.

Turning a hidden player on removes the hidden rule after Apply, reloads and verifies the entity.

## 15. Playing and paused player switch

The switch is disabled with:

> Stop playback before hiding this player.

EMBi does not stop playback automatically.

## 16. Legacy unresolved rules

Show only when unresolved migrated rules exist:

```text
Older rules need review                            >
```

No bulk confirmation switch is used.
