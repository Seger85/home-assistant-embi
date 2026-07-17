# Repository- und Release-Governance

## Stable-Linie

`main` enthält veröffentlichte Stable-Versionen. Änderungen erfolgen über geprüfte Pull Requests. Force-Push und History Rewrite sind ausgeschlossen.

## EMBi 0.9.2

```text
release/0.9.2
→ PR #30 nach main
→ vollständige CI
→ Squash-Merge
→ Tag v0.9.2
→ Stable Release als latest
```

Der vorherige Funktionsumfang 0.9.0 entstand im Branch `feature/embi-0.9.0` und in PR #29. Diese abgeschlossene Linie bleibt unverändert.

## Pflichtchecks

- Quality Python 3.13 und 3.14
- HACS validation
- Hassfest
- EMBi specification contract
- Test package

Quality umfasst JSON, YAML, Compileall, Mypy, Ruff, Ruff-Format, Pytest, Vertragsprüfungen, Datenschutzprüfung, Paketbau, SHA-256 und `BUILD_COMMIT`.

## Releasevertrag

- Manifest und Runtime: `0.9.2`
- Tag: `v0.9.2`
- Titel: `EMBi 0.9.2`
- nicht Draft oder Prerelease
- als Latest markiert
- Assets: `embi.zip` und `embi.zip.sha256`
- veröffentlichte Assets erneut prüfen

Bestehende Tags und Releases bleiben unverändert.

## HACS

HACS verwendet `zip_release: true`, `filename: embi.zip` und `hide_default_branch: true`.

## Schutz

Das Ruleset **Protect main and develop** erzwingt Pull Requests und Pflichtchecks und blockiert Force-Push. Unabhängige Änderungen werden nicht in den Release-PR gemischt. Zugangsdaten und private Systeminformationen dürfen nicht veröffentlicht werden.
