# Changelog

## [Unreleased]

No unreleased product changes.

## [1.2.2] - 2026-10-06

- Wartungsupdate auf Basis aller geprüften Änderungen seit v1.2.1.
- Die einzelnen Änderungen stehen in den verknüpften Pull Requests auf GitHub.
- Bestehende Player, Sensoren und Einstellungen werden beim Update beibehalten.

## [1.2.1] - 2026-09-26

### English

- Corrected the copy/paste player cards so each list shows the server selected by its active-player sensor. German and English card templates are now rendered in real Home Assistant tests.
- Includes the new **Active players** sensor, clearer English/German options and illustrated dashboard guides introduced in 1.2.0. Sensors are configured through the integration UI, without YAML.
- Existing player identities and settings are preserved. After upgrading from 1.1.0, enable **Active players** in the sensor options if desired.

### Deutsch

- Die kopierbaren Player-Karten sind korrigiert: Jede Liste zeigt den Server ihres Sensors für aktive Player. Beide Sprachfassungen werden jetzt mit Home Assistants echtem Vorlagensystem getestet.
- Enthält den neuen Sensor **Aktive Player**, verständlichere deutsche/englische Optionen und bebilderte Anleitungen aus 1.2.0. Die Sensoren werden über die Oberfläche eingerichtet, ohne YAML.
- Bestehende Player und Einstellungen bleiben erhalten. Beim Update von 1.1.0 kannst du **Aktive Player** in den Sensor-Optionen einschalten.

## [1.2.0] - 2026-09-26

### English

- New **Active players** sensor counts distinct playing or paused Emby clients, separately from users watching. It shares the existing session stream and adds no HTTP polling. Unknown activity or an offline server produces unavailable, not zero.
- Existing sensor choices are preserved. Enable the new sensor in the integration options; all seven sensors are selected for new installations. No configuration YAML is needed.
- Clearer German and English options, grouped overview and explicit device-history cleanup guidance. Entity IDs and custom names remain unchanged.
- English main README with a German version, individual original card screenshots and complete copy/paste examples. Player-card lists are scoped to the selected server.
- Automated maintenance removes completed runs of retired, disabled workflows whose source files no longer exist. Active CI, releases, tags and HA registry entries are untouched.

### Deutsch

- Neuer Sensor **Aktive Player**: zählt unterschiedliche Emby-Player mit Wiedergabe oder Pause, getrennt von schauenden Benutzern. Er verwendet vorhandene Sitzungsdaten ohne zusätzliche Serverabfragen. Bei unklarer Aktivität oder ausgefallenem Server ist er nicht verfügbar, statt irreführend null anzuzeigen.
- Deine Sensorauswahl bleibt beim Update erhalten. Aktiviere den neuen Sensor bei Bedarf in den Optionen. Bei einer neuen Einrichtung sind alle sieben Sensoren ausgewählt; YAML ist dafür nicht nötig.
- Einfachere deutsche und englische Beschreibungen, übersichtlichere Optionen und klare Hinweise zur Gerätebereinigung. Entitäts-IDs und eigene Namen bleiben erhalten.
- Englische Hauptbeschreibung und deutsche Alternative mit einzeln zugeschnittenen Originalbildern sowie vollständigem Karten-Code. Die Playerliste gehört zum ausgewählten Server.
- Automatische Repository-Pflege entfernt abgeschlossene Läufe ausgedienter, deaktivierter Workflows, deren Dateien nicht mehr vorhanden sind. Aktuelle CI, Releases, Tags und HA-Registry bleiben erhalten.

## [1.1.0] - 2026-09-26

### Zuverlässiger im Alltag

- Player reagieren auch dann auf einen Wiedergabestart, wenn der Client bereits vorher bekannt war. Mehrere Sitzungen desselben Clients werden zusammengefasst; eine aktive Sitzung hat Vorrang.
- Die Verbindung verwendet Home Assistants gemeinsame HTTP-Verbindung mit Zeitlimits, geprüften HTTPS-Zertifikaten und einem geregelten WebSocket-/REST-Wiederanlauf. Reload und Unload räumen eigene Aufgaben und Listener auf.
- Cover werden ohne API-Schlüssel in der Bild-URL über Home Assistant geladen. Fehlgeschlagene Steuerbefehle zeigen eine verständliche Meldung. Ein ungültiger Schlüssel lässt sich über die erneute Anmeldung ersetzen.
- Bibliothekszahlen und schauende Benutzer werden unabhängig aktualisiert. Fehlende oder ungültige Daten werden nicht als null ausgegeben.

### Vorsichtiger beim Aufräumen

- Vor jeder einzelnen Serverlöschung werden Geräteidentität und Sitzungsaktivität erneut geprüft. Aktive, pausierte oder nicht eindeutig beurteilbare Clients bleiben geschützt.
- Ein ungewisses Löschergebnis, ein Schreibfehler oder das Entladen der Integration stoppt die laufende Serie. Unterbrochene Löschlisten werden nach einem Neustart nicht ungeprüft fortgesetzt.
- Fehlender oder beschädigter Wartungsspeicher hält die Bereinigung an. Eine eigene Wiederherstellungsseite ermöglicht erneutes Laden oder ausdrücklich bestätigtes Zurücksetzen.
- Manuelle Bereinigung verschiebt den gespeicherten automatischen Termin nicht mehr. Die HA-Nachbereitung prüft aktuelle Sitzungen nochmals.

### Verständlicher einrichten

- Geöffnete Playerformulare behalten ihre Zuordnung auch bei geänderten Namen oder Aktivitätsanzeigen. Die Änderungsübersicht erfasst alle relevanten Einstellungen, und Entwürfe verändern keine gespeicherten Listen vorzeitig.
- Ungültige gespeicherte Optionen werden sicher behandelt; die automatische Bereinigung bleibt dabei aus, bis die Einstellungen geprüft wurden.
- Deutsche Beschreibungen, Hilfe und Dashboard-Beispiele richten sich an alle Nutzer. Die Playerkachel unterscheidet Einzahl und Mehrzahl und berücksichtigt auch umbenannte Player.
- Diagnosen enthalten Aktualisierungszeitpunkte und verständlichere Zustandsangaben; private und unbekannte Zusatzfelder werden begrenzt beziehungsweise redigiert.

### Bestehende Einrichtung und Update

- Vorhandene Player- und Sensoridentitäten bleiben erhalten. Neue Player erhalten eine zusätzliche Zuordnung zur Integration, damit gleiche Client-IDs verschiedener Server nicht kollidieren.
- Bitte vor dem Update ein Home-Assistant-Backup erstellen. Ein reiner Paket-Downgrade stellt neu angelegte Registry-Identitäten nicht vollständig auf den alten Stand zurück.
- Die automatische Serverbereinigung bleibt bei einer neuen Einrichtung ausgeschaltet. Bereits gespeicherte gültige Einstellungen werden übernommen. Zwischen letzter Prüfung und Serverlöschung bleibt das durch Embys getrennte API-Aufrufe bedingte kurze Zeitfenster bestehen.
- Voraussetzung: Home Assistant ab 2026.7.2. Die CI prüft zusätzlich echte HA-Lebenszyklen auf Mindest- und aktueller Testversion. Bestehende Release-Automatik bleibt erhalten; Teilreleases werden überprüfbar fortgesetzt und Actions sind auf Commit-IDs festgelegt.

## [1.0.8] - 2026-09-06

- Publish all validated repository changes since v1.0.7 through the autonomous dependency and stable-release pipeline.

## [1.0.7] - 2026-09-04

- Publish all validated repository changes since v1.0.6 through the autonomous dependency and stable-release pipeline.

## [1.0.6] - 2026-09-02

- Publish all validated repository changes since v1.0.5 through the autonomous dependency and stable-release pipeline.

## [1.0.5] - 2026-08-30

- Publish all validated repository changes since v1.0.4 through the autonomous dependency and stable-release pipeline.

## [1.0.4] - 2026-07-24

- Publish all validated repository changes since v1.0.3 through the autonomous dependency and stable-release pipeline.

## [1.0.3] - 2026-07-20

- Publish the complete post-cleanup maintenance baseline after the immutable `v1.0.2` tag was created before the final toolchain merge.
- Update `actions/setup-python` to v7 and `actions/upload-artifact` to v7 across the canonical workflows.
- Update the supported test and validation toolchain while retaining Python 3.13 and 3.14 coverage.
- Restore the stable publisher to the canonical `release/${version}` branch contract.
- Preserve the 1.0.2 runtime cleanup, entity and unique-ID contracts, player and sensor behavior, cleanup safety, diagnostics, and published legacy migrations.

## [1.0.2] - 2026-07-20

- Remove confirmed dead player-action helpers, unused enable entry points, and obsolete reconciliation compatibility aliases.
- Remove unused player catalog and Options Flow rendering helpers together with their isolated test-only contract.
- Preserve exact EMBi entity ownership checks, stable entity and unique IDs, player and sensor creation rules, active-playback protection, cleanup safety, and published legacy migrations.
- Extend stable and repository contracts so removed runtime symbols cannot silently return.

## [1.0.1] - 2026-07-20

- Enforce saved media-player visibility after every config-entry setup, reload, and restart instead of treating reconciliation as a one-time migration.
- Remove disallowed technical clients safely even when a fresh media-player platform has not yet rebuilt its local entity maps.
- Keep playing and paused clients protected while continuing to remove idle, off, standby, unavailable, and safely revalidated inactive clients.
- Refresh reconciliation diagnostics after every setup, including idempotent no-op runs, without changing Emby server history or causing reload loops.
- Restore technical clients with their stable unique IDs when the master or exact player option is enabled again.
- Isolate published legacy option upgrades in `legacy_migration.py` and keep current runtime names, tests, workflows, and documentation version-neutral.

## [1.0.0] - 2026-07-19

- Consolidate the Options Flow, player-group UI, and reconciliation runtime into canonical unversioned modules.
- Replace the failing sensor form with one serializable six-item multi-select that remains draft-only until final apply.
- Hide the review step when no semantic changes exist and return stale direct review calls to the root menu.
- Protect only freshly confirmed playing or paused clients; revalidate unknown playback per player and report named blockers.
- Keep the technical master independent from individual player exceptions and remove disallowed entities from the entity platform, state machine, and exact EMBi registry ownership.
- Advance bounded startup reconciliation to version 3 and safely remove inactive or stale-restored states before exact registry cleanup.
- Complete idempotent active-viewer sensor identity migration, including exact duplicate-remnant cleanup and collision safety.
- Standardize dependency-free version resolution through `scripts/read_version.py` before dependency installation in every package and release workflow.
- Clean release-suffixed runtime modules and behavior tests while preserving migration coverage and legal files.

## [0.9.9] - 2026-07-19

- Canonicalize the active-viewer sensor as `sensor.emby_users_watching` and migrate an exact EMBi-owned registry entry in place when the target is free.
- Remove accidental duplicate top-level user visibility options while preserving the effective nested visibility map.
- Use compact mobile-safe player labels with oldest-known access first and unknown timestamps at the end.
- Run registry reconciliation version 2 for safely removable hidden `stale_restored` players while preserving active, paused, live, and ambiguous protections.
- Version cleanup reports so legacy runs without `skipped_recent` show that the value was not recorded instead of a false zero.
- Extend translated error contracts and privacy-safe diagnostics for sensor identities, option duplicates, and report versions.

## [0.9.8] - 2026-07-19

- Add six optional Emby library and active-viewer sensors, enabled by default.
- Remove disabled EMBi sensors from the entity registry after successful option apply and reload.
- Preserve stable sensor unique IDs and documented entity IDs when available.
- Persist and display the automatic-cleanup `skipped_recent` count with the configured age threshold.
- Clarify that manual server-record selection is independent of the automatic age threshold.
- Refresh community documentation, translations, diagnostics, contracts, and regression coverage.

## [0.9.7] - 2026-07-18

- Simplify player management and cleanup navigation while preserving the existing lifecycle safety model.
- Keep player groups fixed oldest-known access first with unknown timestamps at the end.
- Keep normal option pages draft-only until final apply.
