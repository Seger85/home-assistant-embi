# Security

Credentials stay in Home Assistant and are redacted from diagnostics. Logs and diagnostics contain aggregate counts and reason codes, not player keys, server record IDs, device names, or usernames.

Registry operations require exact EMBi ownership by domain, platform, config entry, and unique ID. EMBi leaves unrelated entities and a foreign entity occupying a desired sensor or player entity ID untouched. Direct `.storage` changes are unsupported.

Unknown playback is never assumed inactive when the Emby session refresh fails. Server-history deletion remains explicit, separately confirmed, and irreversible without an Emby backup.
