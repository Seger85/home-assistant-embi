# EMBi Roadmap

## 0.3.0 – erste stabile Basis

Status: veröffentlicht.

Schwerpunkte:

- Config Flow und Options Flow
- Erhalt bestehender Entity-IDs und Unique IDs
- manuelle und automatische Bereinigung alter Emby-Gerätedatensätze
- persistenter Wartungsstatus und absoluter Scheduler
- exakte Registry-Nachbereitung mit getrennten Ergebniszählern
- HACS-ZIP-Releasevertrag

## 0.9.0 – Geräte, Benutzer und sichere Player-Verwaltung

Status: frozen Contract implementiert auf `feature/embi-0.9.0`; private Home-Assistant-Abnahme und anschließende Stable-Promotion stehen noch aus.

Enthalten:

- produktorientierter Bereich **Geräte & Player**
- bekannte Emby-Benutzer als primäre Gruppen
- **Gemeinsam genutzt** mit allen bekannten Benutzern
- **Ohne Benutzerzuordnung**
- **Technische Zugriffe** nur bei belastbarer Metadaten- oder Verhaltensgrundlage
- **Unklare Clients** ohne automatische Umklassifizierung
- verständliche App-, Geräte-, HA-Namens-, Entity-ID- und Statusangaben
- exakte Player-, Geräte- und Benutzer-Sichtbarkeitsregeln
- sichtbare nicht eindeutig auflösbare ältere Regeln
- semantische Entwurfsprüfung mit Apply und Discard
- ein gemeinsamer Bereich **Bereinigung**
- weiterhin getrennte Serverhistorien-Löschung und Home-Assistant-Player-Entfernung
- Schutz für `playing`, `paused` und unklaren Wiedergabestatus
- Entfernen normaler nicht spielender EMBi-Player aus Home Assistant
- exakte Hidden-Rule vor Registry-Entfernung
- Reload und Verifikation, dass entfernte Player nicht zurückkehren
- Wiederherstellung und Verifikation der resultierenden Entity
- deaktivierte gültige Entities werden nicht als verwaist behandelt
- idempotente Migration von 0.3.0
- Erhalt exakter Alterswerte wie `364` und `365`
- Erhalt der automatischen Bereinigungsstellung und des Schedulerzustands
- Erhalt von Entity-IDs, Unique IDs, Namen, Aliasen, Areas, Labels und deaktiviertem Zustand
- redigierte Migration-, Klassifizierungs-, Cleanup- und Restore-Diagnostics
- genau eine Bestätigung je destruktiver Aktion
- private releasegleiche CI-Artefakte vor der Stable-Promotion

Release-Gates:

- vollständige automatisierte Anforderungs- und Akzeptanzmatrix grün
- Python 3.13 und 3.14 grün
- Ruff, Format, HACS Validation, Hassfest und Spec Contract grün
- privates `0.9.0`-Testpaket exakt an den getesteten Commit gebunden
- produktives Home-Assistant-Backup
- Upgrade `0.3.0` → privates `0.9.0`-Paket
- 29-Player-Baseline und sämtliche Identitäten/Metadaten erhalten
- Benutzer-, Shared-, Unassigned-, Technical- und Unknown-Gruppen live geprüft
- Apply, Discard, X und semantische Review-Ausgabe auf iPhone, iPad und Desktop geprüft
- `playing` und `paused` live geschützt
- ein normaler nicht spielender Player kontrolliert entfernt und wiederhergestellt
- Serverhistorien-Bereinigung separat geprüft
- Scheduler, Reload und Neustart geprüft
- Rollbackweg demonstriert
- Promotion `develop` → `main` erst nach dokumentierter Live-Freigabe

## Nach 0.9.0

Diese Themen gehören nicht zum eingefrorenen 0.9.0-Vertrag:

- Report-only-Modus
- Bibliothekszahlen und Bibliothekssensoren
- Filme-, Serien- und Episodensensoren
- zuletzt hinzugefügte Medien
- Benutzerstatistiken
- Wiedergabezeitstatistiken
- neue Entity-Plattformen
- weitere Serververwaltungsfunktionen

## 1.0.0 – Veröffentlichung und langfristiger Vertrag

Für 1.0.0 reserviert:

- breitere externe Testbasis
- dokumentierte Home-Assistant- und Emby-Kompatibilitätsmatrix
- abschließendes Datenschutz- und Sicherheitsreview
- stabiler Migrationspfad über mehrere veröffentlichte Versionen
- Community-Dokumentation und Supportprozess
- erneute Priorisierung der ausdrücklich zurückgestellten Produktfunktionen

Premium-Code bleibt höchstens eine entfernte Post-1.0-Idee und ist kein zugesagter Produktumfang.
