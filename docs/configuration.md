# Configuration

EMBi is configured through Home Assistant's Config Flow and Options Flow.

## Draft model

Every non-destructive form changes only an in-memory draft. **Review changes** is shown only when a semantic difference exists. A stale direct review request returns to the root menu without saving or reloading. Final apply writes options once and schedules one planned reload.

## Player visibility

The technical master controls whether the technical group and technical entities are exposed. Exact technical player exceptions remain stored independently:

- master off: group hidden; inactive technical entities are removed
- master on: group reachable, including when every individual player is off
- individual off: only that exact player is hidden
- individual on: the same unique ID is restored

Playing and paused clients remain protected. Unknown playback is freshly revalidated per client.

## Sensors

The sensor page uses one six-item multi-select. OK updates only the draft. Final apply removes disabled exact EMBi sensor registry entries; re-enabling restores their stable unique IDs.

Direct `.storage` edits are unsupported.
