# Changelog

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
