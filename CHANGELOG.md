# Changelog

## [0.9.7] - 2026-07-18

### Player UX and draft navigation

- Remove the player search field and transient sort selector; player groups are always sorted oldest-known access first with unknown timestamps at the end.
- Reduce the Home Assistant player page to global switches and group navigation while retaining direct per-player switches inside each group.
- Use compact two-line player labels with `Device · App` and localized last access.
- Replace Back-only action dropdowns on non-destructive pages with the native OK submit, which updates only the in-memory draft and returns one level.
- Keep permanent storage exclusively behind Review changes → Apply changes; closing the flow still saves nothing.

### Server cleanup and lifecycle

- Replace the server-cleanup intermediate menu with direct root entries for automatic cleanup and individual server-record deletion.
- Show last run, result, protected counts and next run directly on the automatic-cleanup page.
- Make manual cleanup always age-independent, oldest-first and limited to unequivocally safe inactive records; remove the manual age and scope controls without changing the automatic age threshold.
- Remove an exact matching Home Assistant entity only after successful manual server deletion and fresh remaining-history, ownership, platform, Unique-ID and playback revalidation.
- Continue protecting playing, paused and unclear players and preserve strict `stale_restored` ownership checks without blanket registry cleanup.

### Quality

- Update German and English translations, documentation, diagnostics, manifest and runtime identity to 0.9.7.
- Add regression contracts for direct navigation, draft-only submits, fixed sorting, manual cleanup and lifecycle safety.

## [0.9.6] - 2026-07-18

- Close the Options Flow immediately after final apply and run reload, exact registry reconciliation and immediate automatic cleanup as a tracked post-apply task.
- Replace redundant Save actions on non-destructive subpages with Back-only draft navigation.
- Show compact two-line player labels with local last-access timestamps.
- Add transient oldest/newest sorting and group search.

## [0.9.5] - 2026-07-18

- Reconcile exact stale-restored Registry remnants while protecting live, playing, paused and unclear players.
- Add retry-safe startup reconciliation and privacy-safe diagnostics.
- Publish Stable releases directly after a merged internal release PR.

## [0.9.4] - 2026-07-18

- Make group switches authoritative while retaining exact entity identities and Emby history for restoration.
- Run changed automatic cleanup immediately after Apply changes.
- Introduce dynamic package-version resolution in CI.

## [0.9.3] - 2026-07-18

- Add direct native player switches, corrected technical-client classification and explicit safe manual cleanup.
- Improve scheduler catch-up and cleanup reporting.

## [0.9.2] - 2026-07-17

- Repair frontend-serializable selectors, mobile labels, navigation and technical-client safety tests.

## [0.9.1] - 2026-07-17

- Introduce the product-oriented Options Flow, semantic review and stable migration contracts.

## [0.9.0]

- Add grouped player management, exact visibility rules, controlled Home Assistant Registry cleanup, server-history cleanup, diagnostics and HACS release packaging.

Older prototype history remains available through the repository tags and release notes.
