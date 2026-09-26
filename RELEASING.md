# Wartung und stabile Releases

Die bestehende Pipeline bleibt der einzige reguläre Veröffentlichungsweg. Es werden keine Einmal-Publisher und keine direkten Versionscommits auf dem geschützten `main` benötigt.

## Abhängigkeitsupdates

Dependabot prüft GitHub Actions am sechsten Tag jedes Monats um 03:00 Uhr und Python-Abhängigkeiten um 03:15 Uhr, jeweils Europe/Berlin. Sicherheitsupdates können zusätzlich erscheinen. Updates einschließlich neuer Hauptversionen werden gruppiert und erst nach erfolgreichen Prüfungen automatisch integriert. Ein inkompatibles Update bleibt offen.

Die Automatik verarbeitet neue Anfragen unmittelbar und holt unterbrochene Arbeit einmal täglich nach. Fehlgeschlagene Prüfungen werden einmal wiederholt. Anschließend sind nur deterministische Ruff-Formatierung und sichere Lint-Korrekturen erlaubt. Danach laufen sämtliche Prüfworkflows erneut. Ein dauerhaft fehlerhafter Commit wird im PR-Text markiert; es entstehen keine laufenden Reparaturkommentare.

## Vertrauen und Berechtigungen

Der stabile Publisher benötigt `EMBI_AUTOMATION_PAT` als Repository-Secret. Vor jeder Änderung prüft er, dass es zum Repository-Eigentümer gehört. Es wird nur für geplante oder bewusst gestartete Veröffentlichungen auf vertrauenswürdigem `main` verwendet. PR-Prüfungen und automatisches Zusammenführen verwenden den kurzlebigen `GITHUB_TOKEN` mit ausdrücklich begrenzten Rechten.

Die Standardrechte bleiben lesend. Workflows dürfen keine eigenen genehmigenden Reviews abgeben. Bei `first_time_contributors` müssen fremde erstmalige Beiträge entsprechend den GitHub-Einstellungen vor dem Ausführen ihrer Workflows freigegeben werden. Geheimniswerte und genaue externe Token-Einstellungen gehören nicht ins Repository.

Actions sind auf vollständige Commit-IDs festgelegt; Dependabot hält diese Referenzen aktuell. Historische deaktivierte Workflows bleiben dokumentiert, werden aber nicht reaktiviert: [Inventar](docs/workflows.md).

## Verbindliche Prüfungen

Für Implementierungs-, Abhängigkeits- und Release-PRs gelten dieselben Anforderungen:

- `Quality (Python 3.13)` und `Quality (Python 3.14)`
- `Static analysis and contracts`: Ruff, MyPy, Kompilierung, JSON/YAML, Übersetzungen, Migrationen, Repository-Verträge und Geheimnisprüfung
- `Home Assistant (minimum)` und `Home Assistant (current)`: echte HA-Lebenszyklen, Registry, Store und Netzwerkprotokoll
- `Build unpublished test package`
- `HACS validation` und `Hassfest`

Der Automerge-Controller wartet auf die vollständigen Workflows `Quality`, `Test package`, `HACS validation` und `Hassfest` für genau denselben Commit. Keine fehlgeschlagene oder unvollständige Prüfung darf übersprungen werden.

In Build- und Releasejobs wird zuerst ausgecheckt, Python eingerichtet und die Version mit `python -I scripts/read_version.py` gelesen. Erst danach werden Abhängigkeiten installiert und Integrationsmodule importiert.

## Ablauf der Veröffentlichung

Der Publisher läuft täglich zur Wiederaufnahme unterbrochener Arbeit und lässt sich über `workflow_dispatch` starten.

1. Er prüft den aktuellen `main`-Commit und die gemeinsame Version in Manifest und Konstanten.
2. Ist die Version bereits veröffentlicht und gibt es neue Änderungen, bereitet `scripts/prepare_automatic_release.py` die nächste Patchversion auf `release/automatic-vX.Y.Z` vor. Größere Funktionsreleases können die gewünschte Version bereits im geprüften Implementierungs-PR mitbringen.
3. Der Publisher erstellt beziehungsweise verwendet einen Release-PR des verifizierten Eigentümers. Ein bestehender fremder Automations-PR wird nicht als vertrauenswürdig übernommen.
4. Alle Prüfungen laufen für den konkreten Branchstand. Die geschützte Zusammenführung erfolgt per Squash.
5. Der Publisher prüft den resultierenden `main` erneut, führt Tests aus und baut `embi.zip` sowie `embi.zip.sha256` reproduzierbar aus diesem Commit.
6. Ein annotierter Tag `vX.Y.Z` wird auf genau diesen Commit gesetzt. Ein vorhandener Tag darf nicht auf einen anderen Commit verschoben werden.
7. Die Veröffentlichung ist regulär, weder Entwurf noch Vorabversion, und wird als **Latest** markiert. Sie enthält genau die beiden Paketdateien.
8. Die Assets werden erneut heruntergeladen; Prüfsumme, Dateiinhalt, Tagziel und Latest-Zuordnung werden geprüft.

`scripts/extract_release_notes.py` übernimmt die zur Version gehörenden, geprüften deutschsprachigen Hinweise aus `CHANGELOG.md`. Automatisch vorbereitete reine Wartungsreleases erhalten einen kurzen deutschen Wartungstext.

## Wiederanlauf nach Teilfehlern

Ein vorhandener Tag am unveränderten aktuellen Commit bedeutet nicht automatisch, dass der Release vollständig ist. `scripts/verify_published_release.py` kontrolliert Metadaten, Assets, Prüfsumme und Paketinhalt. Ein vollständiger Release beendet den Lauf ohne Änderung. Ein nachweislich unvollständiger Release wird mit demselben Tag fertiggestellt. Abweichende bereits veröffentlichte Paketdaten, falsche Prüfsummen und unerwartete Zusatzassets stoppen die automatische Reparatur. Ist GitHub nicht zuverlässig abfragbar, stoppt der Publisher, statt einen Defekt zu unterstellen. Vorhandene Tags werden nicht umgehängt.

Die automatische Ruff-Reparatur liefert auf Standardausgabe ausschließlich die neue 40-stellige Commit-ID. Andere Ausgaben gehen an das Laufprotokoll; ein fehlgeschlagener Reparaturschritt wird nicht gepusht.

## HACS und Rückweg

`hacs.json` verwendet `zip_release: true` und `filename: embi.zip`. HACS bezieht das Paket aus dem neuesten regulären GitHub-Release. Ein lokaler Versionswechsel wird nach Installation und HA-Neustart wirksam.

Alte stabile Releases bleiben erhalten. HACS kann frühere Versionen installieren, aber ein Paket-Downgrade allein kehrt neue Registry-Identitäten nicht vollständig um. Für eine verlässliche Rückkehr nach einem größeren Update ist ein vorheriges Home-Assistant-Backup nötig. Serverlöschungen benötigen zusätzlich ein passendes Emby-Backup. Beides vor dem Produktiveinsatz berücksichtigen.
