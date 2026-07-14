# Konfiguration und Gerätefilter

## Verbindung

Pflichtfelder:

- Anzeigename
- Host/IP ohne Protokollpräfix
- Port
- HTTPS-Schalter
- API-Schlüssel

Empfohlene Standardports:

- HTTP: 8096
- HTTPS: 8920

Der API-Schlüssel wird in den Config-Entry-Daten gespeichert und in Diagnostics redigiert. Bei der Rekonfiguration wird ein gespeicherter Schlüssel nie in das Passwortfeld zurückgegeben. Ein leeres Feld behält den vorhandenen Schlüssel bei.

## Gerätemodus

### Alle Geräte anzeigen

Kompatibler Standard. Alle von pyemby gelieferten Geräte dürfen Entitäten erzeugen, sofern sie nicht ignoriert sind.

### Nur aktive Wiedergaben

Zulässig sind die Zustände:

- `playing`
- `paused`

Leerlaufende oder ausgeschaltete Clients werden nicht als verfügbar geführt. Dieser Modus eignet sich für temporäre Statusanzeigen, nicht für eine dauerhaft vollständige Geräteübersicht.

### Nur ausgewählte Geräte

Die Liste **Anzuzeigende Geräte** speichert eine konkrete Kombination aus gemeldeter Client-ID und App-Name. Dadurch können zwei Apps auf demselben Gerät getrennt behandelt werden.

Beispiel:

```text
client-123.AndroidTv
client-123.Emby for Android
```

## Ignorierliste

Die Ignorierliste hat immer Vorrang. Sie speichert standardmäßig die rohe gemeldete Client-ID. Dadurch werden auch mehrere App-Varianten desselben Geräts ausgeschlossen.

## Sammelaktionen

Native Mehrfachselektoren bieten nicht in jeder Home-Assistant-Version eine verlässliche „Alle auswählen“-Schaltfläche. EMBi stellt deshalb explizite Sammelaktionen bereit:

- alle aktuellen Geräte als anzuzeigende Geräte auswählen
- Auswahl anzuzeigender Geräte leeren
- alle aktuellen Geräte ignorieren
- Ignorierliste leeren

Jede Aktion hat einen eigenen Bestätigungsdialog. Historische `/Devices`-Datensätze werden dabei auf eindeutige Client-/App-Identitäten beziehungsweise rohe Client-IDs dedupliziert. Die besonders weitreichende Aktion „alle ignorieren“ weist ausdrücklich auf die Folgen hin.

## Verhalten bei fehlenden Geräten

Bereits konfigurierte IDs bleiben im Selektor sichtbar, auch wenn sie vom Server momentan nicht gemeldet werden. Sie erhalten den Hinweis „nicht aktuell vom Server gemeldet“.
