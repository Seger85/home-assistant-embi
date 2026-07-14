# EMBi Roadmap

## 0.2.0 – produktive Baseline

Status: abgeschlossen und versioniert.

- Config Entry und Options Flow
- Übernahme der vorhandenen 28 Media-Player
- Erhalt der Entity-IDs
- kontrollierte Migration weg vom Legacy-YAML-Pfad

## 0.3.0-rc1 – Identität, Sicherheit und Repository

Status: über HACS installiert und in Home Assistant 2026.7.2 erfolgreich live geprüft.

- korrekte Trennung von Emby-`Id` und `ReportedDeviceId`
- automatische Optionsmigration
- Legacy-YAML-Code vollständig entfernt
- verständlichere deutsche und englische UI
- abgesicherte Registry- und optionale Serverbereinigung
- redigierte Diagnostics
- HACS-Struktur, Tests und GitHub Actions
- 28 bestehende Media-Player, Entity-IDs, Unique IDs und individuelle Namen erhalten
- Push-Updates, aktive Wiedergabe und ergänzende Sensoren bestätigt

## 0.3.0-rc2 – Runtime-, Safety- und UI-Härtung

Status: Umsetzung in separatem Draft-PR; noch nicht installiert, getaggt oder veröffentlicht.

- deduplizierte Allowlist- und Ignore-Sammelaktionen
- korrekte Anzahl eindeutiger Client-Identitäten in Sammeldialogen
- aktive Legacy-YAML-, ignorierte und normale Entitäten von Registry-Bereinigung ausgeschlossen
- unmittelbare Revalidierung vor jedem Registry-Remove
- eindeutige Serverbereinigungs-Labels mit App, Version, Aktivität und kurzer Datensatz-ID
- keine gespeicherten API-Schlüssel als Passwortfeld-Standardwerte
- erweiterte Unit- und Repository-Vertragstests
- aktualisierte deutsche und englische UI-Hinweise

Live-Freigabekriterien für rc2:

- Upgrade von v0.3.0-rc1 auf v0.3.0-rc2 über HACS erfolgreich
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
- temporäre HACS-Metadatenausnahmen geprüft und soweit möglich entfernt

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
