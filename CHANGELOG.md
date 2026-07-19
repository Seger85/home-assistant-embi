# Changelog

## [0.9.9] - 2026-07-19

- Canonicalize the active-viewer sensor as `sensor.emby_users_watching` and migrate an exact EMBi-owned registry entry in place when the target is free.
- Remove accidental duplicate top-level user visibility options while preserving the effective nested visibility map.
- Use compact mobile-safe player labels with oldest-known activity first and unknown timestamps last.
- Run registry reconciliation version 2 for safely removable hidden `stale_restored` players while preserving active, paused, live, and ambiguous protections.
- Version cleanup reports so legacy runs without `skipped_recent` show that the value was not recorded instead of a false zero.
- Extend translated error contracts and privacy-safe diagnostics for sensor identities, option duplicates, and report versions.

## [0.9.8] - 2026-07-19

- Add six optional Emby library and active-viewer sensors, enabled by default.
- Remove disabled EMBi sensors from the entity registry after successful option apply and reload.
- Preserve stable sensor unique IDs and documented entity IDs when available.
- Persist and display the automatic-cleanup `skipped_recent` count with the configured age threshold.
- Clarify that manual server-record selection is independent of the automatic age threshold.
- Refresh community documentation, translations, diagnostics, contracts, and regression coverage.

## [0.9.7] - 2026-07-18

- Simplify player management and cleanup navigation while preserving the existing lifecycle safety model.
- Keep player groups fixed oldest-known access first with unknown timestamps at the end.
- Keep normal option pages draft-only until final apply.
