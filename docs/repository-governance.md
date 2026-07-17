# Repository- und Release-Governance

## Branchrollen

### `main`

- veröffentlichte Stable-Linie
- Änderungen nur über geprüfte Pull Requests
- kein Force-Push und keine History-Umschreibung
- Stable-Tags nur auf Commits, die in `main` enthalten sind

### `develop`

- optionale integrierte Entwicklungslinie für größere künftige Vorhaben
- kein notwendiger Umweg für freigegebene Stable-Hotfixes

### Release-Branches

Ein freigegebener Stable-Hotfix darf als einzelner `release/<version>`-Branch direkt gegen `main` geführt werden. Der Branch bleibt bis zu vollständig grüner CI erhalten und wird nicht per Rebase oder Force-Push bereinigt.

## Pull-Request-Fluss 0.9.1

```text
release/0.9.1
→ PR #30 direkt nach main
→ vollständige CI auf einem exakten finalen Head
→ Squash-Merge nach main
→ Tag v0.9.1 auf dem exakten Merge-Commit
→ regulärer GitHub-Release als latest
→ Veröffentlichung von embi.zip und embi.zip.sha256
→ erneuter Download und Verifikation der Assets
```

## Pflichtchecks

- `Quality (Python 3.13)`
- `Quality (Python 3.14)`
- `HACS validation`
- `Hassfest`
- `EMBi specification contract`
- `Test package`

Quality umfasst:

- JSON und YAML
- Compileall
- Mypy
- Ruff und Ruff-Format
- vollständigen Pytest-Lauf
- Specification Contract
- Stable Contract
- Secret-/Privacy-Scan
- releasegleichen Paketbau
- SHA-256 und `BUILD_COMMIT`

Kein Pflichtcheck darf übersprungen, abgeschwächt oder durch einen manuellen Direkt-Push ersetzt werden.

## Paketvertrag

Der gemeinsame Paketbuilder erzeugt:

- `embi.zip`
- `embi.zip.sha256`
- intern für die Build-Verifikation `BUILD_COMMIT`

Im veröffentlichten GitHub-Release erscheinen ausschließlich `embi.zip` und `embi.zip.sha256`. Die Installationsdateien liegen direkt im ZIP-Root. Tests, Dokumentation, `.github`, Caches und Repositorymetadaten sind ausgeschlossen.

## Stable-Releasevertrag

Für `v0.9.1` gelten:

- Manifest und interne Runtime-Version exakt `0.9.1`
- Tag exakt `v0.9.1`
- Tagziel ist der finale Main-Merge-Commit
- Release-Titel `EMBi 0.9.1`
- nicht Draft
- nicht Prerelease
- als `latest` markiert
- Releaseassets nach Veröffentlichung erneut herunterladen
- veröffentlichte Prüfsumme gegen das veröffentlichte ZIP prüfen
- ZIP-Struktur und Manifestversion erneut validieren

Bestehende Tags und Releases werden niemals verschoben oder ersetzt.

## HACS

`hacs.json` verlangt:

- `zip_release: true`
- `filename: embi.zip`
- `hide_default_branch: true`

HACS installiert damit reguläre Releaseassets und verwendet keinen Default-Branch-Commit als scheinbare Stable-Version.

## Dependabot und unabhängige Änderungen

Abhängigkeitsupdates und unabhängige Wartungsarbeiten werden nicht beiläufig in einen Produkt- oder Release-PR gemischt. Eine technisch notwendige Ausnahme muss im PR begründet und vollständig geprüft werden.

## Rulesets

Für geschützte Branches gilt das Ruleset **Protect main and develop**:

- Pull Requests erzwingen
- Force-Push blockieren
- Branch-Löschung blockieren
- Pflichtchecks erzwingen
- kein ungeprüfter Auto-Merge

## Historische Integrität

Veröffentlichte Historie wird nicht umgeschrieben. Fehler werden durch nachvollziehbare Folgecommits oder einen neuen regulären Patch-Release korrigiert. Geheimnisse oder private Diagnosedaten dürfen zu keinem Zeitpunkt in Commits, Tests, Logs, Artefakten oder Releases aufgenommen werden.
