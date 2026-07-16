# 06 – Final UI Copy English

The wording is authoritative. Dynamic placeholders use `{braces}`.

## Root

**Title:** Manage EMBi

**Introduction:** Manage Emby players in Home Assistant and safely clean up old device records when needed.

**Statistics:**
- `{count}` devices in Emby server device history
- `{count}` players in Home Assistant
- `{count}` protected by active playback
- `{count}` currently removable from Home Assistant
- Automatic cleanup: `{status}`

**Menus:**
- Devices & players
- Cleanup
- Review `{count}` changes

## Devices & players

**Title:** Devices & players

**Introduction:** Choose which Emby players appear in Home Assistant.

**Switch:** Only show during playback  
**Off description:** Selected players remain available in Home Assistant when nothing is playing.  
**On description:** Players appear only while playing or paused.

**Switch:** Automatically show new players  
**On description:** New playback devices are automatically shown in Home Assistant.  
**Off description:** New playback devices remain hidden until you enable them here.

**Search:** Search user, device, app or entity ID

**Groups:**
- Users
- Shared devices
- Without user assignment
- Technical access
- Unknown clients
- Review older rules

**User switch:** Show all players for `{user}`

**Technical access explanation:** These applications accessed the server through the Emby API. They are not normal playback devices.

**Technical access switch:** Show technical access as Home Assistant players

**Status:**
- Playing
- Paused
- Ready
- Disabled in Home Assistant
- Hidden in EMBi
- No longer reported by the Emby server
- No user assigned
- Used by `{users}`
- Last used by `{user}`
- Last used on `{date}`

**Actions:**
- Enable in Home Assistant
- Hide in EMBi
- Show in Home Assistant again
- Back to Devices & players

**Protection text:** Stop playback before hiding or removing this player.

## Cleanup

**Title:** Cleanup

**Introduction:** Clean old Emby server records or remove unwanted players from Home Assistant.

**Statistics:**
- `{count}` devices in Emby server device history
- `{count}` players in Home Assistant
- `{count}` additional historical devices in Emby server device history
- `{count}` server records currently safe to delete
- `{count}` Home Assistant players currently removable
- `{count}` players protected by playback

**Explanation:** Emby stores every device and app connection that has used the server, including active, inactive and technical access. A physical device can appear more than once because of different apps or sign-ins. You can also change a record's display name in the Emby server under Devices.

**Difference note:** Additional historical records are not automatically safe to delete. EMBi checks age, activity and remaining player relationships.

### Automatic cleanup

**Switch:** Automatically clean old Emby records

**On description:** EMBi regularly checks old records and removes only records that satisfy all safety rules.

**Off description:** Automatic cleanup is off. Manual checks remain available.

**Field:** Remove records older than

**Options:**
- 1 week – 7 days
- 1 month – 30 days
- 3 months – 90 days
- 6 months – 180 days
- 1 year – 365 days
- Custom

**Field:** Custom age in days

**Switch:** Also remove matching Home Assistant players

**Description:** Also removes a related Home Assistant player when no remaining Emby record requires it and it is neither playing nor paused.

### Manual server check

**Heading:** Check Emby server device history

**Action:** Check now

**Empty state:** No matching records were found. Nothing was changed.

**Result lines:**
- `{count}` are older than `{days}` days and safe to delete
- `{count}` are protected by active playback
- `{count}` do not satisfy all deletion rules
- `{count}` have no valid activity date

**Action:** Delete `{count}` selected records

**Confirmation title:** Delete `{count}` Emby server records?

**Confirmation text:** The selected device-history records will be removed from the Emby server. User accounts, media, libraries and playback history are not deleted.

**Buttons:**
- Back
- Delete permanently

### Home Assistant

**Heading:** Home Assistant players

**Summary:**
- `{count}` players in Home Assistant
- `{count}` currently removable
- `{count}` protected by playback

**Action:** Manage Home Assistant players

**Player action:** Remove from Home Assistant

**Confirmation title:** Remove `{count}` players from Home Assistant?

**Confirmation text:** The selected players will be hidden in EMBi and removed from Home Assistant. They remain in the Emby server device history and can be restored later under Devices & players.

**Button:** Remove `{count}` players

**Failure:** `{name}` could not be removed. The player was detected again after reload.

**Success:** `{name}` was removed from Home Assistant and remained hidden after reload.

### Last run

**Heading:** Last cleanup run

**Status:**
- Successful
- Partially successful
- Failed
- Not run yet

**Mode:**
- Automatic
- Manual

**Lines:**
- Started: `{datetime}`
- Completed: `{datetime}`
- Age threshold: `{days}` days
- Deleted: `{count}`
- Protected: `{count}`
- Errors: `{count}`
- Next run: `{datetime}`
- Next run: automatic cleanup disabled

## Review changes

**Title:** Review changes

**Buttons:**
- Discard changes
- Apply changes

**Empty state:** No unsaved changes.

## General

**Navigation:**
- Back to Manage EMBi
- Back to Devices & players
- Back to Cleanup

**General failure:** The action could not be completed safely. Success was not reported. Technical details are available in EMBi diagnostics.
