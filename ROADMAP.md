# EMBi Roadmap

## 0.2.0 – produktive Baseline

Status: abgeschlossen und versioniert.

- Config Entry und Options Flow
- Übernahme der vorhandenen 28 Media-Player
- Erhalt der Entity-IDs
- kontrollierte Migration weg vom Legacy-YAML-Pfad

## 0.3.0-rc1 – Identität, Sicherheit und Repository

Status: über das öffentliche HACS-Custom-Repository installiert und in Home Assistant erfolgreich live verifiziert.

Bestätigt:

- korrekte Trennung von Emby-`Id` und `ReportedDeviceId`
- Legacy-YAML-Code vollständig entfernt
- bestehender Config Entry erhalten
- alle 28 Media-Player erhalten
- Entity-IDs, Unique IDs und individuelle Namen erhalten
- Live-Wiedergabestatus und Push-Updates funktional
- sichere Standardstellung der Serverbereinigung
- redigierte Diagnostics
- HACS-, Hassfest-, Ruff- und Unit-Test-CI erfolgreich

Noch offen:

- vollständige Options-Flow- und Screenshot-QA auf iPhone, iPad und Desktop
- kontrollierter Sicherheitstest der destruktiven Serverbereinigung
- finale Entscheidung über die stabile Version 0.3.0

## Repository- und Release-Governance

Status: Korrektur nach einem vorzeitigen Merge in Arbeit.

- öffentliche Historie wird nicht zurückgesetzt
- `develop` wurde regulär mit `main` synchronisiert
- zukünftige Dependabot-PRs zielen auf `develop`
- CI-Checks erhalten eindeutige Namen für GitHub-Rulesets
- neue Tags sollen Releases nach erfolgreicher CI automatisch erzeugen
- RC-Tags werden automatisch als Prerelease und nicht als `latest` veröffentlicht
- Release-Archive und SHA-256-Prüfsummen werden automatisch erzeugt
- einmalige GitHub-Rulesets für `main` und `develop` bleiben einzurichten

## 0.3.0 – stabile Freigabe

Freigabekriterien:

- GitHub Actions vollständig erfolgreich
- Installation über das öffentliche HACS-Custom-Repository erfolgreich
- Upgrade 0.2.0 → 0.3.0-rc1 erfolgreich
- bestehende Entity-IDs und Unique IDs unverändert
- Optionsmigration und alle Optionsmenüs abschließend geprüft
- Screenshot-QA auf iPhone, iPad und Desktop abgeschlossen
- keine neuen EMBi-Warnungen oder Fehler
- kontrollierter Server-Cleanup-Test abgeschlossen oder ausdrücklich auf eine spätere Version verschoben
- GitHub-Rulesets aktiv
- automatisierter Release-Workflow geprüft
- temporäre HACS-Metadatenausnahmen geprüft und soweit möglich entfernt
- ausdrückliche Freigabe durch Gerry

## 0.4.0 – vertiefte Testabdeckung

- vollständige Home-Assistant-Testumgebung für Config Flow und Options Flow
- Tests der Entity Registry mit Mock Registry
- Tests für Reload/Unload und pyemby-Callbacks
- Tests für Reauth-/Auth-Fehler
- strukturierter Audit-Log-Eintrag für Wartungsaktionen ohne sensible IDs

## 1.0.0 – Veröffentlichungsreife

- dokumentierte Kompatibilitätsmatrix
- externe Beta-Tests
- vollständige HACS- und Hassfest-Konformität
- Datenschutz- und Sicherheitsreview
- stabiler Migrationspfad über mindestens zwei Vorversionen
- klare Abgrenzung zum minimalen Home-Assistant-Core-Vorschlag
