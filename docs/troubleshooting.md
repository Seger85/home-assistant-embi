# Troubleshooting

## Emby sensors page

The 1.0 sensor page is a native multi-select. If it does not open, verify that `strings.json`, `translations/en.json`, and `translations/de.json` have identical key structures and inspect the Options Flow error log.

If a documented sensor remains unavailable, verify the Emby API response and reload the integration. Remove conflicting YAML sensors before enabling the EMBi-owned entity and restart Home Assistant.

## A player is not removed

Playing or paused clients remain protected. For an unknown state EMBi refreshes Emby sessions; a failed refresh protects only that client. Diagnostics report aggregate requested, removed, protected, and failed counts plus reason codes.

## Technical players remain visible

Confirm the technical master is off, apply the draft, and allow the planned reload to finish. A currently playing client is retained until playback ends; the media-player callback then rechecks visibility.

## Sensor identity collision

EMBi never changes a foreign target entity. Remove or rename the unrelated entity manually, then reload EMBi. Do not edit `.storage`.

## HACS still shows an older version

Reload the custom repository information in HACS and confirm that the latest stable GitHub release contains both `embi.zip` and `embi.zip.sha256`.
