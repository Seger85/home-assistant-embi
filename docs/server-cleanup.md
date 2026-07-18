# Serverbereinigung

## Trennung der Aufgaben

EMBi trennt weiterhin:

- **Home-Assistant-Player:** Sichtbarkeit und Registry-Lifecycle
- **Emby-Serverhistorie:** historische Gerätedatensätze auf dem Server
- **Automatische Bereinigung:** altersbasierter, geplanter Wartungslauf
- **Manuelle Bereinigung:** ausdrücklich ausgewählte sichere Einzelrecords

## Automatische Bereinigung

Die automatische Bereinigung bleibt altersbasiert. Bestehende Werte, Aktivierungsstatus, persistenter Scheduler und `next_run_at` bleiben erhalten. Ein geänderter und aktivierter Entwurf wird erst nach finalem Apply wirksam.

Die Einstellungsseite zeigt zugleich letzten Lauf, Modus, verwendete Altersgrenze, gelöschte/geschützte/fehlgeschlagene Einträge und nächsten Lauf. Eine separate Seite „Letzter Bereinigungslauf“ existiert nicht mehr.

## Manuelle Bereinigung

Die manuelle Auswahl ist ab 0.9.7 immer:

- unabhängig vom Alter
- fest älteste bekannte Aktivität zuerst
- ohne manuelle Altersgrenze
- ohne Scope-Selektor
- ohne Änderung der automatischen Altersgrenze

Einträge ohne verlässlichen Aktivitätszeitpunkt werden nicht angeboten. Aktive, pausierte und nicht eindeutig bewertbare Player bleiben geschützt.

## Ablauf einer manuellen Löschung

1. Serverdaten und Home-Assistant-Zustände frisch lesen.
2. Nur eindeutig sichere Kandidaten anbieten.
3. Auswahl als Vorschau anzeigen.
4. Löschung ausdrücklich bestätigen.
5. Jeden ausgewählten Serverrecord separat löschen.
6. Nach erfolgreicher Serverlöschung verbleibende Serverhistorie erneut lesen.
7. Einen Registry-Eintrag nur bei exakter Domain-, Plattform-, Config-Entry-, Entity-ID- und Unique-ID-Zuordnung entfernen.
8. Aktive, unklare, `stale_restored`-mehrdeutige oder weiterhin serverseitig vorhandene Identitäten schützen.

`queued` oder `matched` bedeutet nicht automatisch `removed`. Eine pauschale Registry-Bereinigung ist ausgeschlossen.

## Player-Lifecycle

- Ausgeschalteter, sicher inaktiver Player: nach Apply aus Home Assistant entfernt; Serverrecord bleibt und ermöglicht Wiederherstellung.
- Manuell gelöschter Serverrecord: nach erfolgreicher Löschung und sicherer Registry-Nachbereitung dauerhaft aus EMBi verschwunden.
- `playing`, `paused`, `unknown`: immer geschützt.
- `stale_restored`: nur bei exakt passender Eigentümerschaft und eindeutiger Revalidierung entfernbar.

## Backup und Rollback

Vor Live-Abnahme ein vollständiges Home-Assistant-Backup erstellen und die installierte Vorgängerversion dokumentieren. Rollback erfolgt über HACS auf `v0.9.6` oder über das vollständige Backup, nicht durch direkte `.storage`-Änderungen.
