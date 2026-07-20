# Changelog

## [Unreleased]

No unreleased product changes.

## [1.0.2] - 2026-07-20

- Remove confirmed dead player-action helpers, unused enable entry points, and obsolete reconciliation compatibility aliases.
- Remove unused player catalog and Options Flow rendering helpers together with their isolated test-only contract.
- Preserve exact EMBi entity ownership checks, stable entity and unique IDs, player and sensor creation rules, active-playback protection, cleanup safety, and published legacy migrations.
- Extend stable and repository contracts so removed runtime symbols cannot silently return.

## [1.0.1] - 2026-07-20

- Enforce saved media-player visibility after every config-entry setup, reload, and restart instead of treating reconciliation as a one-time migration.
- Remove disallowed technical clients safely even when a fresh media-player platform has not yet rebuilt its local entity maps.
- Keep playing and paused clients protected while continuing to remove idle, off, standby, unavailable, and safely revalidated inactive clients.
- Refresh reconciliation diagnostics after every setup, including idempotent no-op runs, without changing Emby server history or causing reload loops.
- Restore technical clients with their stable unique IDs when the master or exact player option is enabled again.
- Isolate published legacy option upgrades in `legacy_migration.py` and keep current runtime names, tests, workflows, and documentation version-neutral.

## [1.0.0] - 2026-07-19

- Consolidate the Options Flow, player-group UI, and reconciliation runtime into canonical unversioned modules.
- Replace the failing sensor form with one serializable six-item multi-select that remains draft-only until final apply.
- Hide the review step when no semantic changes exist and return stale direct review calls to the root menu.
- Protect only freshly confirmed playing or paused clients; revalidate unknown playback per player and report named blockers.
- Keep the technical master independent from individual player exceptions and remove disallowed entities from the entity platform, state machine, and exact EMBi registry ownership.
- Advance bounded startup reconciliation to version 3 and safely remove inactive or stale-restored states before exact registry cleanup.
- Complete idempotent active-viewer sensor identity migration, including exact duplicate-remnant cleanup and collision safety.
- Standardize dependency-free version resolution through `scripts/read_version.py` before dependency installation in every package and release workflow.
- Clean release-suffixed runtime modules and behavior tests while preserving migration coverage and legal files.

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
