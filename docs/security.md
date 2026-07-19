# Security

Credentials stay in Home Assistant and are redacted from diagnostics. Logs and diagnostics contain aggregate counts and reason codes, not player keys, server record IDs, device names, or usernames.

Registry operations require exact EMBi ownership. A foreign entity occupying a desired sensor or player entity ID is left untouched. Unknown playback is never assumed inactive when the Emby session refresh fails. Server-history deletion remains explicit, separately confirmed, and irreversible without an Emby backup.
