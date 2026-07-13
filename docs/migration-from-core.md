# Migration von Home Assistant Core/YAML zu EMBi

## Voraussetzungen

- vollständiges Home-Assistant-Backup
- Zugriff auf die Home-Assistant-Logs
- aktuelle Liste der vorhandenen `media_player.emby_*`-Entity-IDs
- Installationsdateien von EMBi

## Kontrollierte Reihenfolge

1. EMBi unter `/config/custom_components/emby` installieren.
2. Home Assistant neu starten.
3. EMBi über den Config Flow mit demselben lokalen Emby-Server verbinden.
4. Prüfen, dass die vorhandenen Entity-IDs dem neuen Config Entry zugeordnet wurden.
5. Wiedergabestatus mindestens eines aktiven Clients prüfen.
6. Ausschließlich den alten YAML-Block entfernen:

   ```yaml
   media_player:
     - platform: emby
       host: ...
       port: ...
       api_key: ...
   ```

7. Separat vorhandene REST-Sensoren, Templates oder Dashboard-Karten nicht beiläufig löschen.
8. Konfiguration validieren.
9. Home Assistant neu starten.
10. Logs auf `Legacy YAML` und `already exists`/Duplicate-Unique-ID prüfen.
11. Anzahl, Entity-IDs, Config-Entry-Zuordnung und Wiedergabestatus erneut prüfen.

## Erfolgsbedingungen

- genau ein geladener EMBi-Config-Entry
- kein Emby-YAML-Plattformblock
- keine Duplicate-Unique-ID-Meldungen
- keine EMBi-Repairs
- alle gewünschten Entity-IDs erhalten
- aktive Wiedergabestatus korrekt

## Rollback

Bei einem Fehler:

1. Home Assistant stoppen bzw. die Integration deaktivieren.
2. vorherige Custom-Component-Version wiederherstellen oder das vollständige Backup einspielen.
3. falls nötig den alten YAML-Block wiederherstellen.
4. Konfiguration prüfen und neu starten.

Keine Entity-Registry-Einträge löschen, solange nicht eindeutig feststeht, welcher Runtime-Pfad aktiv ist.
