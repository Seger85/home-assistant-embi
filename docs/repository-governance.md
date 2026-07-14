# Repository- und Release-Governance

## Zielbild

EMBi verwendet einen nachvollziehbaren Entwicklungs- und Releasefluss ohne direkte Veröffentlichung ungeprüfter Änderungen.

```text
Feature-/Fix-Branch
→ Pull Request nach develop
→ Quality, HACS und Hassfest
→ Review und Merge nach develop
→ Draft-Release-PR develop nach main
→ Home-Assistant-Livetest und ausdrückliche Freigabe
→ Merge nach main
→ versionsgleicher Git-Tag
→ automatisierter GitHub-Release
```

## Branchrollen

### `main`

- öffentlich veröffentlichter Repository-Stand
- Ziel ausschließlich für kontrollierte Release-PRs aus `develop`
- keine direkten Feature-, Fix- oder Dependabot-Commits
- keine Force-Pushes und keine Branch-Löschung

### `develop`

- gemeinsamer Integrationsbranch
- Ziel für Feature-, Fix-, Dokumentations-, CI- und Dependabot-PRs
- Ausgangspunkt für Release-PRs nach `main`

### Arbeitsbranches

- von `develop` erstellen
- nach Zweck benennen, zum Beispiel `feat/...`, `fix/...`, `docs/...` oder `chore/...`
- nach erfolgreichem Merge entfernen

## Pull-Request-Regeln

- Änderungen nach `develop` benötigen einen Pull Request und erfolgreiche CI.
- Release-PRs von `develop` nach `main` bleiben bis zur ausdrücklichen Freigabe als Draft geöffnet.
- Ein Draft-Status ist eine technische Sperre und keine bloße Kennzeichnung.
- Vor dem Merge eines Release-PRs müssen Manifestversion, Changelog, Roadmap, Projektstatus und Home-Assistant-Livetest konsistent sein.
- Ein stabiler Release darf nicht allein aufgrund grüner CI veröffentlicht werden.

## Dependabot

Dependabot zielt für GitHub-Actions- und Python-Abhängigkeiten auf `develop`. Dependabot-PRs werden nicht automatisch gemergt. Major-Updates benötigen eine inhaltliche Prüfung der Release Notes und eine vollständige CI-Runde.

## Releasevertrag

Ein Release entsteht ausschließlich durch einen Git-Tag im Format:

```text
vMAJOR.MINOR.PATCH
vMAJOR.MINOR.PATCH-PRERELEASE
```

Beispiele:

```text
v0.3.0
v0.3.0-rc2
```

Der Release-Workflow prüft vor der Veröffentlichung:

- Tagformat
- exakte Übereinstimmung von Tag und `manifest.json`-Version
- Prerelease-Tags liegen in der Historie von `develop`
- stabile Tags liegen in der Historie von `main`
- JSON-Validierung
- Python-Kompilierung
- Ruff Lint und Format
- Unit-Tests
- HACS-Validierung
- Hassfest
- Inhalt und Manifestversion des Release-Archivs

Erst danach werden `embi.zip` und `embi.zip.sha256` veröffentlicht.

Tags mit einem Prerelease-Suffix werden automatisch als GitHub-Prerelease veröffentlicht und niemals als `latest` markiert. Tags ohne Prerelease-Suffix werden als stabile Releases veröffentlicht.

## HACS und Vorabversionen

Während ausschließlich ein Prerelease verfügbar ist, muss in HACS die Anzeige von Beta-/Vorabversionen aktiviert bleiben. Ein neuer Commit auf `main` ist keine neue EMBi-Version, solange die Manifestversion unverändert bleibt und kein neuer Release veröffentlicht wurde.

## Empfohlene GitHub-Rulesets

Die folgenden Einstellungen müssen einmalig in GitHub unter den Repository-Regeln gesetzt werden, da sie nicht über den derzeitigen Connector verwaltet werden können.

### `main`

- Änderungen nur über Pull Requests
- Force-Pushes blockieren
- Branch-Löschung blockieren
- offene Review-Konversationen vor Merge auflösen
- folgende Statuschecks verpflichtend machen:
  - `Quality (Python 3.13)`
  - `Quality (Python 3.14)`
  - `HACS validation`
  - `Hassfest`
- kein Auto-Merge
- Bypass für Repository-Administratoren nach Möglichkeit deaktivieren

### `develop`

- Änderungen über Pull Requests bevorzugen
- Force-Pushes blockieren
- Branch-Löschung blockieren
- dieselben vier Statuschecks verpflichtend machen

## Umgang mit versehentlichen Merges

Öffentlich sichtbare Historie wird nicht nachträglich umgeschrieben, solange kein Geheimnis oder sicherheitskritischer Inhalt veröffentlicht wurde.

Bei einem versehentlichen, aber inhaltlich sicheren Merge:

1. Ist-Zustand und Commitfolge dokumentieren.
2. Keine Tags verschieben.
3. Keine öffentlichen Branches per Force-Push zurücksetzen.
4. `develop` regulär mit `main` synchronisieren.
5. Governance und Branch-Regeln korrigieren.
6. Erst danach den normalen PR- und Releasefluss fortsetzen.

## Aktueller historischer Hinweis

PR #1 wurde trotz dokumentierter Draft-Sperre am 14. Juli 2026 gemergt. Anschließend wurden mehrere Dependabot-PRs nach `main` übernommen. Da die Änderungen keine Secrets enthielten und der EMBi-0.3.0-rc1-Livetest erfolgreich war, wurde die öffentliche Historie bewusst nicht zurückgesetzt. `develop` wurde regulär mit `main` synchronisiert und zukünftige Dependabot-PRs wurden auf `develop` umgestellt.
