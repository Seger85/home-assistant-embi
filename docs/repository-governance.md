# Repository- und Release-Governance

## Branchrollen

### `main`

- veröffentlichte Linie
- bleibt bis zur finalen 0.9.0-Promotion auf Stable `v0.3.0`
- Änderungen nur über einen kontrollierten Promotion-PR aus `develop`
- kein Force-Push und keine History-Umschreibung
- Stable-Tag nur auf einem Commit, der in `main` enthalten ist

### `develop`

- integrierte Entwicklungs- und Pre-Live-Linie
- Ziel normaler Feature-, Fix-, Dokumentations- und Dependabot-PRs
- Ziel von PR #29 nach erfolgreicher privater Live-Abnahme

### `feature/embi-0.9.0`

- einziger Implementierungsbranch für den Frozen Contract 0.9.0
- enthält Implementierung, Tests, Dokumentation und Abnahmefixes
- kein konkurrierender 0.9-Implementierungsbranch
- kein Rebase oder Force-Push zur kosmetischen Historienbereinigung

## Pull-Request-Fluss 0.9.0

```text
feature/embi-0.9.0
→ Draft-PR #29 nach develop
→ vollständige CI auf einem exakten finalen Feature-Commit
→ privates embi-test-<vollständiger SHA>-Artefakt
→ private Home-Assistant- und visuelle Abnahme
→ Abnahmefixes weiterhin auf demselben Branch und in PR #29
→ vollständige CI erneut grün
→ PR #29 nach develop mergen
→ Promotion-PR develop nach main
→ Promotion-Merge nach main
→ Tag v0.9.0
→ regulärer Stable Release als latest
```

PR #29 bleibt bis zur dokumentierten privaten Abnahme Draft, offen und ungemergt. Grüne CI und ein privates Testartefakt allein erlauben keinen Merge.

## Pflichtchecks

- `Quality (Python 3.13)`
- `Quality (Python 3.14)`
- `HACS validation`
- `Hassfest`
- `EMBi specification contract`
- `Test package`

Quality umfasst JSON, YAML, Compileall, Ruff, Ruff Format, vollständigen Pytest-Lauf, Specification Contract, Stable Contract, Secret-/Privacy-Scan, releasegleichen Paketbau, SHA-256 und `BUILD_COMMIT`. Kein Pflichtcheck darf umgangen oder abgeschwächt werden.

## Privates Testpaket

Der Workflow `Test package` erzeugt ausschließlich:

- `embi.zip`
- `embi.zip.sha256`
- `BUILD_COMMIT`

Der Name lautet `embi-test-<vollständiger Feature-Commit-SHA>`. Das Artefakt erzeugt keinen Tag, kein Release und kein `latest`. Das Installations-ZIP enthält nur Dateien aus `custom_components/emby` direkt im ZIP-Root.

## Releasevertrag

Für 0.9.0 gelten:

- Tag, Manifest und interne Version exakt `0.9.0`
- Stable-Commit muss in `main` enthalten sein
- regulärer Release: nicht Draft, nicht Prerelease und `latest`
- Assets ausschließlich `embi.zip` und `embi.zip.sha256`
- veröffentlichte Assets erneut herunterladen und prüfen

Vor der erfolgreichen privaten Abnahme sind Tag, Draft Release, Prerelease, öffentlicher RC und Stable Release gesperrt.

## HACS

`hacs.json` verlangt `zip_release: true`, `filename: embi.zip` und `hide_default_branch: true`. Ein Feature-Commit oder privates Testartefakt ist keine HACS-Version.

## Dependabot

Die PRs #23, #24 und #25 werden nicht in PR #29 gemischt, sofern keine Abhängigkeit technisch zwingend erforderlich ist. Eine Ausnahme benötigt dokumentierte Kompatibilitätsprüfung und Begründung.

## Rulesets

Für `main` und `develop` gilt das aktive Ruleset **Protect main and develop**:

- Pull Requests erzwingen
- Force-Push blockieren
- Branch-Löschung blockieren
- Pflichtchecks erzwingen
- kein Auto-Merge

## Historische Integrität

Veröffentlichte Historie wird nicht umgeschrieben. Bestehende Tags und Releases bleiben unverändert. Implementierungsfehler werden durch nachvollziehbare Folgecommits auf dem bestehenden Branch korrigiert.
