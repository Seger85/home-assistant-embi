# Emby Integration – EMBi

> **EMBi ist die Emby-Integration für alle, die irgendwann mehr Geräte in der Liste haben als im Haus.**
>
> Sie übernimmt bestehende Emby-Media-Player, hält deren Identitäten stabil und bringt kontrolliert Ordnung in historische Clients und Geräte-Einträge.
>
> **Weniger Gerätefriedhof, mehr Kontrolle.**

EMBi verwendet ausschließlich einen Home-Assistant-Config-Entry unter der Domain `emby`. Vorhandene pyemby-Unique-IDs werden nicht verändert. Dadurch können Entity-IDs, individuelle Namen, Dashboards, Automationen, HomeKit- und Siri-Zuordnungen bei einem kontrollierten Upgrade erhalten bleiben.

## Status 0.3.0

`0.3.0` ist als Stable-Code vorbereitet, aber noch nicht öffentlich veröffentlicht. Vor Tag und Release stehen die kontrollierte Home-Assistant-Liveabnahme, die visuelle Prüfung und die ausdrückliche Freigabe des Promotion-PRs.

Die dokumentierte Live-Baseline für die Abnahme umfasst **29 EMBi-Media-Player** und keine zusätzliche Wartungsentity.

## Funktionen

- Config Flow und Reconfigure Flow
- Media-Player-Modi: alle, nur aktive Wiedergaben oder nur ausgewählte Geräte
- getrennte app-spezifische und geräteweite Ignorierregeln
- sichtbare Aufbewahrung nicht eindeutig migrierbarer Altregeln
- zusammenhängender Options-Flow-Entwurf mit **Apply** und **Discard**
- manuelle und automatische altersbasierte Serverbereinigung
- getrennte manuelle und automatische Alterswerte
- Presets 7, 30, 90, 180 und 365 Tage plus benutzerdefinierte Werte
- persistenter absoluter Scheduler mit `next_run_at`
- persistenter, identitätsfreier Laufbericht
- getrennte Registry-Ergebnisse: queued, matched, removed, missing und protected
- Deutsch und Englisch
- HACS-Releaseasset `embi.zip`

EMBi legt keine Wartungsentity an. Die einzige Plattform bleibt `media_player`.

## Identitätsvertrag

| Emby-Feld | Verwendung |
|---|---|
| `Id` | exakter Historieneintrag und Parameter für `DELETE /Devices` |
| `ReportedDeviceId` | exakte geräteweite Ignorierregel |
| `ReportedDeviceId.AppName` | pyemby-Key, bestehende HA-Unique-ID und exakte Registry-Nachbereitung |

`Id` wird niemals als Home-Assistant-Unique-ID verwendet. Präfix-, Teilstring- und Wildcard-Matches sind für Registry-Entfernungen unzulässig.

## Upgrade von v0.3.0-rc3

Die idempotente Migration erhält:

- Config-Entry-ID
- Entity-IDs und Unique IDs
- individuelle Entity-Namen
- aktive Serverbereinigung und aktive Automatik
- den abgeschlossenen rc3-Erstlauf
- vorhandene HA-Mitbereinigung, auch wenn sie `true` ist
- vorhandene benutzerdefinierte Alterswerte

Entfernt werden nur obsolete rc3-Werte:

- separater Cleanup-API-Schlüssel
- Aktivierungsphrase der Automatik
- automatische Ignore-Option nach Serverlöschung
- alte gemischte Ignore-Hilfswerte

Ein gespeicherter Wert von **364 Tagen bleibt 364** und wird als benutzerdefinierter Wert dargestellt. Die bewusste spätere Umstellung auf 365 gehört in den Live-Test und ist keine globale Migration.

## Options Flow

Normale Unterseiten ändern nur den Entwurf. Sie schreiben keine Optionen und laden EMBi nicht neu.

- **Änderungen übernehmen** validiert und speichert genau einmal; Home Assistant lädt den Config Entry höchstens einmal neu.
- **Änderungen verwerfen** verwirft den vollständigen Entwurf ohne Write und ohne Reload.
- Schließen über **X** schreibt nichts.
- Destruktive Aktionen sind bei ungespeicherten Änderungen gesperrt.
- Die Automatik startet erst nach dem finalen Apply.

## Scheduler und Catch-up

Bei einer neuen Aktivierung oder einem überfälligen beziehungsweise fehlenden Termin wird genau ein Catch-up nach **120 Sekunden** geplant. Ein gespeicherter Zukunftstermin bleibt über Reload und Neustart unverändert. Nach Abschluss eines automatischen Laufversuchs wird der nächste Termin auf **24 Stunden nach Abschluss** gesetzt.

Manuelle und automatische Bereinigung teilen sich denselben Lock. Ein paralleler zweiter Lauf wird nicht gestartet.

## Server- und Registry-Sicherheit

- aktive Player sind geschützt
- Datensätze ohne gültigen Aktivitätszeitpunkt sind geschützt
- Kandidaten müssen strikt älter als der UTC-Cutoff sein
- es gibt kein Batchlimit; Einzelfehler stoppen den restlichen Lauf nicht
- Serverbereinigung verwendet ausschließlich den normalen EMBi-Verbindungsschlüssel
- nach einer Serverlöschung wird keine Ignore-Regel automatisch erzeugt
- HA-Mitbereinigung ist bei neuen Aktivierungen standardmäßig `false`; bestehende Werte bleiben erhalten
- ein Registry-Key kann zunächst nur `queued` sein
- `removed` wird ausschließlich gezählt, wenn `registry.async_remove()` tatsächlich ausgeführt wurde
- bei unklarem Zustand, Store-Fehler, Neustart oder mehrdeutiger Revalidierung wird fail-safe nicht entfernt

Der korrigierte Referenzfall 74 → 69 ist abgebildet: fünf erfolgreiche Serverlöschungen, null Serverfehler, fünf Registry-Keys queued, null Matches, null tatsächliche Registry-Removals und fünf missing.

## Logging und Datenschutz

- Erfolg, keine Kandidaten und erwartete Schutzfälle: `INFO`
- Teilerfolg oder unterbrochene Nachbereitung: `WARNING`
- vollständiger technischer Fehler: `ERROR`
- Persistent Notification nur bei Warning oder Error

Diagnostics, Store, Laufbericht und Notifications enthalten keine vollständigen Record-IDs, ReportedDeviceIds, Player-Keys, Benutzernamen oder API-Schlüssel.

## Installation des unveröffentlichten Testpakets

Das finale Testpaket wird als privates GitHub-Actions-Artefakt erzeugt und ist **kein Release**. Nach vollständigem Home-Assistant- und Emby-Backup wird der Inhalt von `embi.zip` nach `/config/custom_components/emby` installiert oder über den vereinbarten kontrollierten Testweg eingespielt. Vorherige Dateien des Komponentenordners müssen vollständig ersetzt werden.

Öffentliche HACS-Stable-Installation ist erst nach Promotion nach `main`, Tag `v0.3.0` und Stable Release möglich.

## Qualität

CI prüft Python 3.13 und 3.14, JSON, YAML, Compileall, Ruff, Ruff-Format, Pytest, Stable-Vertrag, Übersetzungssynchronität, Secret-/Privacy-Scan, HACS Validation, Hassfest, releasegleichen Paketbau, SHA-256 und `BUILD_COMMIT`.

Weitere Details stehen in `docs/`.

## Credits

- Projekt: Seger
- Basis: Home Assistant Emby und pyemby

## Lizenz

Apache License 2.0. Siehe `LICENSE` und `NOTICE.md`.
