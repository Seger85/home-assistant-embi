# EMBi einstellen

Die Optionen erreichst du unter **Einstellungen → Geräte & Dienste → EMBi**. Verbindungsdaten änderst du über **Neu konfigurieren** im Integrationsmenü. Wird der API-Schlüssel ungültig, bietet Home Assistant eine erneute Anmeldung an. Ein anderer Emby-Server muss als eigene Integration eingerichtet werden.

## Erst auswählen, dann speichern

Player- und Sensorseiten ändern zunächst nur einen Entwurf. **Änderungen prüfen** erscheint, sobald eine Einstellung tatsächlich geändert wurde. Erst **Änderungen übernehmen** speichert und lädt die Integration neu. **Verwerfen** setzt den Entwurf zurück; das Schließen des Dialogs speichert ihn nicht.

Manuelle Löschaktionen haben eigene Auswahl- und Bestätigungsseiten. Eine bestätigte Serverlöschung wird sofort ausgeführt und ist nicht Teil eines später verwerfbaren Entwurfs.

## Player

- **Player beibehalten:** Bekannte Player bleiben außerhalb der Wiedergabe erhalten. Ohne aktuelle Verbindung können sie nicht verfügbar sein.
- **Nur aktive Player:** Wiedergabe und Pause halten den Player sichtbar. Sicher inaktive, nicht gewünschte Player werden ausgeblendet.
- **Neue Player automatisch anzeigen:** Neue Clients aufnehmen. Beim Ausschalten bleiben bisher erlaubte Player berücksichtigt.
- **Technische Zugriffe:** API-Clients und ähnliche Zugriffe getrennt anzeigen oder ausblenden. Einzelne Ausnahmen bleiben gespeichert, auch wenn der übergeordnete Schalter ausgeschaltet ist.
- **Benutzer und Geräte:** Gruppen helfen bei der Auswahl. Ein Gerät mit mehreren Apps kann mehrere Player besitzen. Geteilte oder nicht eindeutig zuordenbare Clients werden entsprechend getrennt aufgeführt.

Eine Ausblendung beendet keine Wiedergabe. Beginnt ein ausgeblendeter Client zu spielen, hat der Schutz der aktiven Sitzung Vorrang. Eine neue Emby-Client-ID gilt zunächst als neuer Client; EMBi führt Geräte nicht allein anhand ähnlicher Namen zusammen.

## Sensoren

Alle sieben Sensoren lassen sich über die Oberfläche auswählen; YAML ist nicht nötig. **Aktive Player** zählt Geräte-/App-Kombinationen mit Wiedergabe oder Pause, auch wenn du ihren HA-Player ausblendest. **Schauende Benutzer** zählt unterschiedliche Benutzer mit laufender Wiedergabe; Pause zählt dort nicht mit. Bei Updates bleibt die bisherige Auswahl erhalten. Schalte den neuen Player-Sensor bei Bedarf selbst ein.

Wähle die gewünschten Werte aus der Liste. Das Abwählen entfernt nach dem Übernehmen nur die zu dieser Integration gehörende Sensorentität. Beim erneuten Aktivieren wird dieselbe eindeutige Identität verwendet. Eigene Namen und Zuordnungen werden durch Home Assistants Registry-Verhalten wiederhergestellt, soweit HA sie noch vorhält.

Bei einer belegten Standard-ID bleibt die fremde Entität unangetastet. Verwende im Dashboard die tatsächliche EMBi-ID oder ändere sie bewusst über die HA-Oberfläche. Ein zusätzlicher YAML-Sensor muss nicht vorsorglich gelöscht werden.

## Bereinigung

Die automatische Bereinigung ist bei neuen Installationen aus. Die Altersgrenze liegt zunächst bei 365 Tagen und kann zwischen 1 und 3650 Tagen eingestellt werden. Die zusätzliche Entfernung passender HA-Entitäten ist getrennt steuerbar. Das Aktivieren oder Ändern der Automatik kann nach dem Übernehmen einen ersten Lauf auslösen. Lies vorher die [Schutzregeln](server-cleanup.md).

## Fehlerhafte gespeicherte Einstellungen

Kann EMBi gespeicherte Werte nicht sicher verwenden, stellt es gültige Werte her und schaltet die automatische Bereinigung aus. Home Assistant zeigt einen Hinweis. Prüfe danach die Optionen und aktiviere die Automatik nur wieder, wenn Auswahl und Altersgrenze stimmen.

Fehlt das Wartungsprotokoll oder ist es beschädigt, bleibt die Bereinigung angehalten. **Wartung wiederherstellen** bietet einen erneuten Ladeversuch und ein ausdrücklich zu bestätigendes Zurücksetzen. Das normale Speichern der Optionen umgeht diese Sperre nicht.
