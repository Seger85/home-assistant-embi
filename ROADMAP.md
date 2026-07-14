# EMBi Roadmap

## 0.2.0 – produktive Baseline

Status: abgeschlossen und versioniert.

- Config Entry und Options Flow
- Übernahme der vorhandenen 28 Media-Player
- Erhalt der Entity-IDs
- kontrollierte Migration weg vom Legacy-YAML-Pfad

## 0.3.0-rc1 – Identität, Sicherheit und Repository

Status: über das öffentliche HACS-Custom-Repository installiert und in Home Assistant 2026.7.2 erfolgreich live verifiziert.

Bestätigt:

- korrekte Trennung von Emby-`Id` und `ReportedDeviceId`
- automatische Optionsmigration
- Legacy-YAML-Code vollständig entfernt
- bestehender Config Entry erhalten
- alle 28 Media-Player erhalten
- Entity-IDs, Unique IDs und individuelle Namen erhalten
- Live-Wiedergabestatus, Push-Updates und ergänzende Sensoren funktional
- sichere Standardstellung der Serverbereinigung
- redigierte Diagnostics
- HACS-, Hassfest-, Ruff- und Unit-Test-CI erfolgreich

## Repository- und Release-Governance

Status: auf `develop` umgesetzt; öffentliche Historie wurde nicht zurückgesetzt.

- `develop` wurde regulär mit `main` synchronisiert
- zukünftige Dependabot-PRs zielen auf `develop`
- Ruleset `Protect main and develop` ist aktiv
- Force-Push und Löschung sind für `main` und `develop` blockiert
- Pull Requests und definierte Statuschecks sind verpflichtend
- CI-Checks besitzen stabile Namen
- ausdrücklich freigegebene `release/v...`-Branches erzeugen nach erfolgreicher CI automatisch den versionsgleichen Tag und GitHub-Release
- RC-Versionen werden als Prerelease und nicht als `latest` veröffentlicht
- stabile Versionen werden als normale Releases und `latest` veröffentlicht
- `embi.zip` und `embi.zip.sha256` werden automatisch erzeugt
- Tagziel, Assets, Prerelease- und Latest-Status werden nach der Veröffentlichung geprüft
- temporäre Release-Anforderungsbranches werden automatisch entfernt

## 0.3.0-rc2 – Runtime-, Safety- und UI-Härtung

Status: als GitHub-Prerelease `v0.3.0-rc2` veröffentlicht; Tag und Release-Automation vollständig geprüft. HACS-Liveupgrade und UI-/Safety-Verifikation stehen noch aus.

Veröffentlicht:

- Tag `v0.3.0-rc2` auf Commit `f69224ff6dc6609f2923e391dda428dd0b91bf69`
- Prerelease-Status bestätigt
- nicht als `latest` markiert
- `embi.zip` und `embi.zip.sha256` vorhanden
- temporärer Release-Anforderungsbranch entfernt

Enthalten:

- deduplizierte Allowlist- und Ignore-Sammelaktionen
- korrekte Anzahl eindeutiger Client-Identitäten in Sammeldialogen
- aktive Legacy-YAML-, ignorierte und normale Entitäten von Registry-Bereinigung ausgeschlossen
- unmittelbare Revalidierung vor jedem Registry-Remove
- eindeutige Serverbereinigungs-Labels mit App, Version, Aktivität und kurzer Datensatz-ID
- keine gespeicherten API-Schlüssel als Passwortfeld-Standardwerte
- erweiterte Unit- und Repository-Vertragstests
- aktualisierte deutsche und englische UI-Hinweise

Live-Freigabekriterien für rc2:

- Upgrade von `v0.3.0-rc1` auf `v0.3.0-rc2` über HACS erfolgreich
- weiterhin 28 Media-Player ohne Entity-/Unique-ID-Änderung
- Allow-all speichert keine doppelten Player-Keys
- aktive Registry-Einträge werden nicht angeboten
- Auswahlbeschriftungen sind auf Desktop, iPad und iPhone verständlich
- gespeicherte Schlüssel bleiben erhalten, werden aber nicht angezeigt
- keine neue EMBi-Warnung, kein Repair und keine unbeabsichtigte Löschung

## 0.3.0 – stabile Freigabe

Freigabekriterien:

- GitHub Actions vollständig erfolgreich
- 0.3.0-rc2-Liveprüfung abgeschlossen
- bestehende Entity-IDs und Unique IDs unverändert
- Optionsmigration und alle Optionsmenüs geprüft
- Registry- und Serverbereinigung sicher geprüft
- Screenshot-QA auf iPhone, iPad und Desktop abgeschlossen
- keine neuen EMBi-Warnungen oder Fehler
- GitHub-Rulesets aktiv
- automatisierter Release-Workflow einschließlich Release-Branch-Auslöser geprüft
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
