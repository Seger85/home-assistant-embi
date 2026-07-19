# Troubleshooting

## A sensor is unavailable

EMBi marks sensor updates unavailable when `/Items/Counts` or `/Sessions` fails or returns malformed values. Check Home Assistant logs, the Emby API key, network reachability, and server availability. EMBi deliberately does not replace an API failure with zero.

## The documented sensor entity ID is not created

A YAML, template, or other integration entity may already use the entity ID. Remove the conflicting YAML definition, restart Home Assistant, and then enable the EMBi sensor again. EMBi does not adopt or delete the conflicting entity.

## A disabled sensor still appears

Apply the draft through **Review changes → Apply changes**. Registry deletion occurs only after a successful config-entry reload and only for an exact EMBi-owned sensor identity.

## A player cannot be removed

Playing, paused, unknown, ambiguous, restored-without-proof, and otherwise unsafe lifecycle states remain protected. Stop playback and refresh the options page before trying again.

## Cleanup shows fewer candidates than expected

Automatic cleanup excludes records newer than its age threshold and records without a reliable timestamp. Manual cleanup ignores the age threshold but still protects active, paused, unknown, ambiguous, or temporally unverifiable records.

## HACS does not show the latest release

Refresh HACS repository information and confirm that the GitHub release is stable, marked latest, and contains `embi.zip` plus `embi.zip.sha256`.
