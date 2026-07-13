# Fehleranalyse

## Duplicate Unique IDs nach Neustart

Wahrscheinlich ist der alte YAML-Plattformblock noch aktiv. EMBi und YAML starten dann parallel.

Prüfen:

- `configuration.yaml`
- Logs nach `already exists`
- Config-Entry-Zuordnung der Entitäten

## Gewählte Geräte werden trotzdem nicht angezeigt

Prüfen:

- Modus „Nur ausgewählte Geräte“ aktiv?
- Gerät gleichzeitig ignoriert? Ignorieren hat Vorrang.
- Client meldet sich mit einer anderen App-Variante?
- Optionsmigration von einer 0.2-Version abgeschlossen?

EMBi 0.3 verwendet `ReportedDeviceId.AppName`; alte numerische `Id`-Werte werden beim Setup migriert, sofern der historische Eintrag noch auf dem Server vorhanden ist.

## Gelöschtes Emby-Gerät erscheint wieder

Das ist möglich, wenn der Client erneut verwendet wird. Emby registriert ihn dann wieder. Zusätzliches Ignorieren in EMBi verhindert die erneute Home-Assistant-Entity-Erzeugung.

## Serverbereinigung wird nicht angezeigt

Die Funktion ist standardmäßig deaktiviert. Unter **Optionale Serverbereinigung einrichten** aktivieren.

## Bereinigungsschlüssel wird akzeptiert, Löschung schlägt fehl

Die Verbindungsprüfung belegt nur, dass der Schlüssel `/System/Info` lesen kann. Der Schlüssel kann trotzdem unzureichende Rechte für `DELETE /Devices` besitzen.

## Auswahlfelder sind zu hell oder weiß

EMBi verwendet native Home-Assistant-Selektoren. Deren Farben stammen aus dem aktiven Frontend-Theme. Die Korrektur muss global im Theme erfolgen; integrationsspezifisches CSS im Config Flow wäre fragil und wird bewusst nicht eingesetzt.

## Entität nach Ignorieren noch in der Registry

Filterung und Registry sind getrennt. Ignorieren verhindert die aktive Anlage bzw. macht die Entität nicht verfügbar. Die Registry-Bereinigung kann den bereits ignorierten Eintrag anschließend kontrolliert entfernen.
