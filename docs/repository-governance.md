# Repository- und Release-Governance

## Branchrollen

### `main`

- öffentlich veröffentlichte Linie
- Änderungen nur über kontrollierten Promotion-PR aus `develop`
- kein direkter Feature-, Fix- oder Dependabot-Merge
- kein Force-Push und keine History-Umschreibung
- Stable-Tag nur auf einem Commit, der in `main` enthalten ist

### `develop`

- integrierte Entwicklungs- und Pre-Live-Linie
- Ziel normaler Feature-, Fix-, Dokumentations- und Dependabot-PRs
- Quelle des unveröffentlichten Testartefakts
- Prerelease-Tag nur auf einem Commit, der in `develop` enthalten ist

### Arbeitsbranches

- von `develop` erstellen
- bestehende Implementierungsbranches weiterverwenden
- keine konkurrierende Stable-Implementierung
- kein Rebase oder Force-Push zur kosmetischen Historienbereinigung

## Pull-Request-Fluss 0.3.0

```text
feature/stable-0.3.0
→ Draft-PR #18 nach develop
→ vollständige CI auf exaktem Head
→ Ready for review
→ Squash-Merge nach develop
→ vollständige CI auf Develop-Merge-Commit
→ unveröffentlichtes Test package auf exakt diesem Commit
→ Draft-Promotion-PR develop nach main
→ Home-Assistant-Liveabnahme
→ ausdrückliche Gerry-Freigabe
→ Promotion-Merge nach main
→ Tag und Stable Release
```

Der Draft-Promotion-PR ist eine technische Sperre. Grüne CI allein erlaubt keinen Merge nach `main` und keine Veröffentlichung.

## Pflichtchecks

- `Quality (Python 3.13)`
- `Quality (Python 3.14)`
- `HACS validation`
- `Hassfest`
- `Test package`

Quality umfasst JSON, YAML, Compileall, Ruff, Ruff-Format, vollständigen Pytest-Lauf, Stable-Vertrag, Übersetzungssynchronität, Secret-/Privacy-Scan, releasegleichen Paketbau, SHA-256 und `BUILD_COMMIT`.

## Testpaket

Der Workflow `Test package` erzeugt ausschließlich ein unveröffentlichtes Actions-Artefakt:

- `embi.zip`
- `embi.zip.sha256`
- `BUILD_COMMIT`

Das Artefakt erzeugt keinen Tag, kein Release und kein `latest`. Installationsdateien liegen direkt im ZIP-Root. Tests, Dokumentation, `.github` und Repositorymetadaten sind ausgeschlossen.

## Releasevertrag

Der Release-Workflow verwendet denselben Paketbuilder wie Quality und Test package.

Zulässige Versionen:

```text
vMAJOR.MINOR.PATCH
vMAJOR.MINOR.PATCH-PRERELEASE
```

Prüfungen:

- Tag und Manifestversion exakt gleich
- interne Version exakt gleich
- Stable-Commit in `main`
- Prerelease-Commit in `develop`
- vollständige Tests, HACS und Hassfest
- SHA-256 und `BUILD_COMMIT`
- Assets nach Veröffentlichung erneut herunterladen und prüfen
- RC ist `prerelease: true` und niemals `latest`
- Stable ist `prerelease: false` und `latest`

Ein `release/v...`-Branch darf nur nach ausdrücklicher Releasefreigabe erzeugt werden. Für 0.3.0 ist er in der Pre-Live-Runde ausdrücklich gesperrt.

## HACS

`hacs.json` verlangt:

```json
{
  "zip_release": true,
  "filename": "embi.zip"
}
```

Ein Commit oder Testartefakt ist keine HACS-Version. HACS Stable wird erst durch den veröffentlichten Stable Release verfügbar.

## Tags und Releases

- vorhandene Tags und Releases sind unveränderlich
- kein Verschieben, Ersetzen oder Neuerstellen bestehender rc-Tags
- kein öffentliches rc4 im Stable-Abschluss
- Stable `v0.3.0` erst nach Live-Abnahme

## Rulesets

Für `main` und `develop`:

- Pull Requests erzwingen
- Force-Push blockieren
- Branch-Löschung blockieren
- offene Review-Konversationen auflösen
- Pflichtchecks erzwingen
- kein Auto-Merge
- Administrator-Bypass soweit möglich deaktivieren

## Historische Integrität

Bereits öffentliche sichere Historie wird nicht umgeschrieben. Bei einem versehentlichen, aber nicht geheimnisbehafteten Merge werden Zustand und Folgen dokumentiert und anschließend regulär über Pull Requests korrigiert. Secrets oder private Diagnosedaten erfordern dagegen sofortige Sicherheitsmaßnahmen und gegebenenfalls Credential-Rotation.
