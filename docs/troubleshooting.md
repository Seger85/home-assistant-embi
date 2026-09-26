# Wenn etwas nicht wie erwartet funktioniert

## Ein Player ist nicht verfügbar

Prüfe zuerst, ob der Emby-Client läuft und vom Server als Sitzung gemeldet wird. Im Modus **Player beibehalten** darf ein früher bekannter Client vorübergehend nicht verfügbar sein. Das ist allein kein HA-Systemfehler und kein Anlass zur Registry-Bereinigung. Bei einem neuen Geräte- oder App-Kennzeichen kann Emby einen neuen Player melden.

Sind alle Player betroffen, prüfe Serveradresse, Port, Netzwerk und den API-Schlüssel. Bei Authentifizierungsproblemen nutze die von Home Assistant angebotene erneute Anmeldung. Für HTTPS muss das Zertifikat von Home Assistant als gültig akzeptiert werden.

## Eine Zahl ist 0, unbekannt oder nicht verfügbar

`0` bedeutet ein gültiges leeres Ergebnis. `unavailable` bedeutet, dass für diese Sensorgruppe aktuell keine gültigen Daten vorliegen. `unknown` kann vor dem ersten verwertbaren Wert auftreten. EMBi ersetzt fehlende Zahlen nicht pauschal durch null. Bibliothekszahlen und Benutzer werden getrennt abgefragt; ein Teil kann funktionieren, während der andere nicht verfügbar ist.

## Playerzahl und Benutzerzahl unterscheiden sich

Die Playerkachel zählt Wiedergabe und Pause. `sensor.emby_users_watching` zählt unterschiedliche Benutzer mit laufender Wiedergabe, ohne pausierte Sitzungen. Ein Benutzer mit zwei Playern kann deshalb als ein Benutzer und zwei Player erscheinen.

## Ein Sensor hat eine andere Entitäts-ID

Suche unter **Einstellungen → Geräte & Dienste → Entitäten** nach der Integration EMBi. Eigene Umbenennungen, mehrere Server oder eine schon belegte Standard-ID können andere IDs ergeben. Passe die Karte an die tatsächliche ID an. Lösche keine fremden YAML- oder Template-Sensoren auf Verdacht.

## Eine Einstellung wurde nicht übernommen

Normale Optionsseiten bearbeiten einen Entwurf. Öffne **Änderungen prüfen** und anschließend **Änderungen übernehmen**. Aktive Player bleiben aus Sicherheitsgründen auch bei einer gespeicherten Ausblendung erhalten, bis sie sicher inaktiv sind. Bleibt eine Fehlermeldung nach dem Speichern, prüfe den HA-Hinweis und lade die Integration nach Behebung der Ursache neu.

## Wartung ist angehalten oder ein Lauf unvollständig

Nutze den Laufbericht und gegebenenfalls **Wartung wiederherstellen**. Nach einem Timeout bei einer Serverlöschung kann der Eintrag bereits gelöscht sein; wiederhole die Aktion nicht aufgrund einer Vermutung. Fehlender Speicher wird bewusst nicht still neu angelegt. Mehr dazu unter [Bereinigung](server-cleanup.md).

## Ein Steuerbefehl schlägt fehl

Nicht jede Emby-App unterstützt jede Fernsteuerungsfunktion. Prüfe, ob der Client noch verbunden ist und denselben Befehl über Emby akzeptiert. EMBi meldet fehlgeschlagene Befehle, statt Erfolg vorzutäuschen.

## Einen Fehler melden

Notiere EMBi-, Home-Assistant- und Emby-Version, Client-App, erwartetes und beobachtetes Verhalten sowie die Schritte zum Nachstellen. Lade bei Bedarf die Diagnose über die Integration herunter und prüfe sie vor dem Teilen. Keine API-Schlüssel, privaten Serveradressen oder unbereinigten Screenshots in öffentliche Issues oder Forenbeiträge kopieren.
