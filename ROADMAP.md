# EMBi Roadmap

## 0.2.0 – produktive Baseline

Status: abgeschlossen und versioniert.

- Config Entry und Options Flow
- Übernahme der vorhandenen 28 Media-Player
- Erhalt der Entity-IDs
- kontrollierte Migration weg vom Legacy-YAML-Pfad

## 0.3.0-rc1 – Identität, Sicherheit und Repository

Status: Code und Dokumentation vorbereitet; vor Produktivfreigabe fehlen GitHub-CI und Laufzeittest.

- korrekte Trennung von Emby-`Id` und `ReportedDeviceId`
- automatische Optionsmigration
- Legacy-YAML-Code vollständig entfernt
- verständlichere deutsche und englische UI
- sichere Sammelauswahl
- abgesicherte Registry-Bereinigung
- optionale Serverbereinigung mit zweiter Bestätigung
- Teilerfolg bei mehreren Löschungen
- redigierte Diagnostics
- HACS-Struktur, Tests und GitHub Actions

## 0.3.0 – stabile Freigabe

Freigabekriterien:

- GitHub Actions vollständig erfolgreich
- Installation über privates HACS-Repository erfolgreich
- Upgrade 0.2.0 → 0.3.0 auf Testinstanz erfolgreich
- bestehende Entity-IDs unverändert
- Optionsmigration geprüft
- alle Optionsmenüs funktional geprüft
- Screenshot-QA auf iPhone, iPad und Desktop
- keine neuen EMBi-Warnungen oder Fehler

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
