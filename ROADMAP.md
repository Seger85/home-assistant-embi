# EMBi Roadmap

## 0.2.0 – produktive Baseline

Status: abgeschlossen und versioniert.

- Config Entry und Options Flow
- Übernahme der vorhandenen 28 Media-Player
- Erhalt der Entity-IDs
- kontrollierte Migration weg vom Legacy-YAML-Pfad

## 0.3.0-rc1 – Identität, Sicherheit und Repository

Status: über das öffentliche HACS-Custom-Repository installiert und in Home Assistant 2026.7.2 erfolgreich live verifiziert.

- korrekte Trennung von Emby-`Id` und `ReportedDeviceId`
- automatische Optionsmigration
- Legacy-YAML-Code vollständig entfernt
- bestehender Config Entry und 28 Media-Player erhalten
- Entity-IDs, Unique IDs und individuelle Namen erhalten
- Live-Wiedergabestatus und Push-Updates funktional
- sichere Standardstellung der Serverbereinigung
- redigierte Diagnostics

## 0.3.0-rc2 – Runtime-, Safety- und UI-Härtung

Status: als GitHub-Prerelease `v0.3.0-rc2` veröffentlicht. Der Tag bleibt unverändert auf Commit `f69224ff6dc6609f2923e391dda428dd0b91bf69`.

- deduplizierte Allowlist- und Ignore-Sammelaktionen
- aktive Registry-Einträge vollständig geschützt
- Revalidierung vor jedem Registry-Remove
- eindeutige Serverbereinigungs-Labels
- keine gespeicherten API-Schlüssel in Passwortfeld-Defaults
- automatisierter, geprüfter Prerelease-Workflow

## 0.3.0-rc3 – Finale Gerätebereinigung

Status: Implementierung auf Basis des aktuellen `develop`; Releaseziel `v0.3.0-rc3`. rc2 wird nicht verschoben oder überschrieben.

Enthalten:

- zwei klar getrennte Bereinigungswege: manuell und automatisch
- manueller Altersfilter vor Datensatzauswahl
- Standard-Altersfilter: älter als 365 Tage
- separat aktivierbare Automatik mit ausdrücklicher Warnung und Bestätigungstext
- erster automatischer Lauf 120 Sekunden nach der bewussten Erstaktivierung
- weitere automatische Läufe alle 24 Stunden
- bewusst keine maximale Löschzahl pro Lauf
- aktive Wiedergaben und Datensätze ohne gültigen Aktivitätszeitpunkt werden übersprungen
- Fehler eines Datensatzes stoppen die übrigen Löschungen nicht
- optionales Entfernen des zugehörigen HA-Media-Players nach erfolgreicher Emby-Löschung
- HA-Registry-Entfernung nur nach frischer `/Devices`-Revalidierung, ohne verbleibende gleiche `ReportedDeviceId.AppName`-Identität und ohne Entity-State beim Reload
- aggregierte automatische Laufdiagnose ohne private IDs

Live-Freigabekriterien für rc3:

- Upgrade über HACS erfolgreich
- Config Entry, 28 Media-Player und bestehende Unique IDs unverändert
- Automatik standardmäßig ausgeschaltet
- Erstaktivierung erfordert Schalter und exakten Text
- erster Lauf nach 120 Sekunden nachvollziehbar
- Altersfilter 365 Tage korrekt
- keine Begrenzung der Kandidatenzahl
- aktive Player und unbekannte Zeitstempel sicher übersprungen
- HA-Registry-Eintrag nur nach letzter Serverhistorie und kontrolliertem Reload entfernt
- UI-QA auf iPhone, iPad und Desktop
- keine neuen EMBi-Warnungen, Repairs oder unbeabsichtigten Löschungen

## 0.3.0 – stabile Freigabe

Freigabekriterien:

- GitHub Actions vollständig erfolgreich
- rc3-Liveprüfung einschließlich manueller und automatischer Bereinigung abgeschlossen
- bestehende Entity-IDs und Unique IDs unverändert
- Optionsmigration und alle Optionsmenüs geprüft
- Registry- und Serverbereinigung sicher geprüft
- Screenshot-QA auf iPhone, iPad und Desktop abgeschlossen
- Backup- und Rollback-Weg praktisch bestätigt
- keine neuen EMBi-Warnungen oder Fehler
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
