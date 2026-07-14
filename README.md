# Emby Integration – EMBi

> **EMBi ist die Emby-Integration für alle, die irgendwann mehr Geräte in der Liste haben als im Haus.**
>
> Sie holt Emby aus der YAML-Ecke, übernimmt bestehende Media-Player und bringt Ordnung in alte Clients, doppelte App-Einträge und historische Geräte.
>
> **Weniger Gerätefriedhof, mehr Kontrolle.**

EMBi verwendet ausschließlich einen Config Entry unter der Domain `emby`. Bestehende pyemby-Unique-IDs bleiben unverändert, sodass ein kontrolliertes Upgrade Entity-IDs, individuelle Namen und Referenzen erhalten kann.

## Funktionen in 0.3.0

- Config Flow und Reconfigure Flow
- Media-Player-Modi: alle, nur aktive Wiedergaben oder nur ausgewählte Geräte
- getrennte app-spezifische und geräteweite Ignorierregeln
- sichtbare Aufbewahrung nicht eindeutig migrierbarer Altregeln
- zusammenhängender Options Flow mit Entwurf, Apply und Discard
- manuelle und automatische altersbasierte Serverbereinigung
- persistenter absoluter Scheduler und datenschutzfreundlicher Laufbericht
- getrennte Registry-Ergebnisse: queued, matched, removed, missing und protected
- Deutsch und Englisch
- HACS-Releaseasset `embi.zip`

EMBi legt keine zusätzliche Wartungsentity an. Die Plattform bleibt ausschließlich `media_player`.

## Identitäten

| Feld | Zweck |
|---|---|
| `Id` | konkreter Historieneintrag und Parameter für `DELETE /Devices` |
| `ReportedDeviceId` | exakte geräteweite Ignorierregel |
| `ReportedDeviceId.AppName` | pyemby-Key, HA-Unique-ID und exakte Registry-Nachbereitung |

`Id` wird niemals als Home-Assistant-Unique-ID verwendet.

## Upgrade von v0.3.0-rc3

Die idempotente Migration erhält Config Entry, Entity-IDs, Unique IDs, Namen, gültige Filterentscheidungen, aktive Bereinigungsschalter und benutzerdefinierte Zahlenwerte. Obsolete rc3-Werte wie ein zweiter Cleanup-Schlüssel, der Aktivierungssatz und die automatische Ignore-Option werden entfernt.

Ein aktiver rc3-Scheduler ohne persistenten Termin erhält genau einen Catch-up-Termin nach 120 Sekunden. Zukünftige gespeicherte Termine werden durch Reload oder Neustart nicht verschoben.

Vor dem Upgrade sind ein vollständiges Home-Assistant-Backup und ein belastbarer Emby-Wiederherstellungsweg erforderlich.

## Options Flow

Normale Einstellungen werden nur im Entwurf geändert. Unterseiten schreiben nichts und laden die Integration nicht neu. Erst **Änderungen übernehmen** speichert genau einmal; **Änderungen verwerfen** verwirft alles. Destruktive Aktionen sind bei ungespeichertem Entwurf gesperrt.

## Altersgrenzen und Automatik

Manuelle und automatische Bereinigung haben getrennte Zahlenwerte und dieselben Presets: 7, 30, 90, 180, 365 Tage oder Benutzerdefiniert. Der Zahlenwert ist die alleinige Quelle der Wahrheit; 364 Tage bleiben bei der Migration 364 Tage. Kandidaten müssen strikt älter als der UTC-Cutoff sein.

Die Automatik ist bei neuen Installationen aus. Aktivierung erfolgt über eine Warnseite mit Bestätigungsschalter, ohne Texteingabe. Der erste Lauf beginnt nach 120 Sekunden, weitere Läufe 24 Stunden nach Abschluss des vorherigen Versuchs. Aktive Player und Einträge ohne gültige Aktivität sind geschützt. Es gibt kein Löschlimit pro Lauf.

## HA-Media-Player-Mitbereinigung

Für neue Aktivierungen ist sie aus; bestehende Werte bleiben erhalten. Eine Entity wird erst nach erfolgreichem Server-DELETE, frischer `/Devices`-Abfrage, fehlender gleicher Historie, Inaktivität sowie exakter Domain-, Plattform-, Config-Entry- und Unique-ID-Prüfung entfernt. `queued` ist keine Entfernung; nur `registry.async_remove()` zählt als `removed`.

Eine echte Registry-Entfernung kann individuelle Namen, Entity-ID-Anpassungen, Dashboards, Automationen, HomeKit und Siri betreffen.

## Logging und Datenschutz

- Erfolg, keine Kandidaten und erwartete Schutzfälle: INFO
- Teilerfolg: WARNING
- technischer Abbruch: ERROR
- Persistent Notification nur bei Teilerfolg oder Fehler

Diagnostics und Laufbericht enthalten keine vollständigen Record-IDs, ReportedDeviceIds, Player-Keys, Benutzernamen oder API-Schlüssel.

## Qualität

CI prüft Python 3.13 und 3.14, Ruff, Format, JSON, YAML, Compileall, Pytest, Stable-Vertrag, Datenschutzscan, HACS Validation, Hassfest, ZIP-Inhalt und SHA-256.

Weitere Details stehen in `docs/`.

## Credits

- Projekt: Seger
- Basis: Home Assistant Emby und pyemby

## Lizenz

Apache License 2.0. Siehe `LICENSE` und `NOTICE.md`.
