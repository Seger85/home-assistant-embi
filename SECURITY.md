# Security Policy

## Supported version

Security fixes are provided for the latest regular stable EMBi release.

## Reporting a vulnerability

Do not post API keys, complete diagnostics, server addresses, device identifiers, user names, or other private data in a public issue. Use GitHub private vulnerability reporting when available, or contact the repository owner `Seger85` privately with a minimal reproduction.

## Sensitive data

API keys, server addresses, server-history IDs, reported client IDs, device or client names, and user names are confidential. Diagnostics redact configuration and identity-bearing options and expose only aggregate evidence. Review every diagnostics file manually before sharing it.

## Destructive operations

Server-history deletion is disabled by default and requires explicit selection, confirmation, and fresh validation. Home Assistant registry operations verify domain, platform, config entry, unique ID, and playback state. Unrelated entities are never adopted or removed. An Emby server backup is the only complete rollback for server-side deletion.
