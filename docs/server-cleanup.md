# Alte Emby-Geräteeinträge bereinigen

EMBi unterscheidet zwei Aufgaben: **Player in Home Assistant anzeigen oder ausblenden** und **alte Geräteanmeldungen auf dem Emby-Server löschen**. Eine ausgeblendete HA-Entität löscht keine Emby-Geräteanmeldung.

## Was gelöscht wird

Die Serverbereinigung verwendet ausschließlich Embys Geräte-Endpunkt. Sie entfernt ausgewählte Geräteanmeldungen. EMBi ruft dabei keine Löschfunktionen für Medien, Bibliotheken oder Benutzer auf. Welche weiteren Auswirkungen Emby intern an die Entfernung einer Geräteanmeldung knüpft, bestimmt der Server.

Eine Serverlöschung lässt sich nicht durch einen Reload rückgängig machen. Für eine vollständige Wiederherstellung ist ein passendes Emby-Backup nötig.

## Manuell oder automatisch

**Manuell:** Auswahl sicher inaktiver Einträge mit eigener Bestätigung. Die automatische Altersgrenze ist dabei keine Voraussetzung; die Aktivitäts- und Identitätsprüfungen gelten weiterhin.

**Automatisch:** Standardmäßig ausgeschaltet. Einträge müssen zusätzlich älter als die eingestellte Grenze sein. Der nächste Termin wird gespeichert und bleibt bei einem HA-Neustart erhalten. Ein manueller Lauf verschiebt diesen Termin nicht. Nach regulären automatischen Läufen beträgt der Abstand 24 Stunden.

## Schutz vor falschen Löschungen

Unmittelbar vor jeder Löschung lädt EMBi Geräte und Sitzungen erneut. Der Eintrag muss noch dieselbe eindeutige Identität haben, sicher inaktiv sein und zur Auswahl beziehungsweise Altersregel passen. Wiedergabe, Pause, widersprüchliche Antworten, fehlende Identität und nicht zuverlässig bestimmbare Aktivität führen zum Überspringen.

Ein bestätigter Erfolg wird gespeichert, bevor EMBi fortfährt. Schlägt das Speichern fehl, stoppt der Lauf. Bei einem Timeout während einer Löschung kann die Anfrage bereits angekommen sein: EMBi meldet das Ergebnis als unvollständig und wiederholt sie nicht blind. Nach einem Neustart wird ein unterbrochener Lauf als unterbrochen angezeigt; eine alte Löschliste wird nicht automatisch wieder abgespielt.

Emby bietet keine atomare Funktion „nur löschen, wenn immer noch inaktiv“. Zwischen letzter Sitzungsprüfung und DELETE kann ein Client daher theoretisch aktiv werden. Die erneute Prüfung vor jedem einzelnen Eintrag verkleinert dieses Fenster; eine absolute Garantie kann ein Client der Emby-API nicht geben. Wer dieses Restrisiko vermeiden möchte, lässt die automatische Serverbereinigung ausgeschaltet.

## Passende HA-Entitäten

Die optionale HA-Nachbereitung findet erst nach bestätigter Serverlöschung statt. Sie prüft Eigentümerschaft, Identität und aktuelle Aktivität erneut. Fremde oder aktive Entitäten bleiben geschützt. Ein fehlgeschlagener Nachbereitungsschritt wird getrennt vom Serverergebnis berichtet und kann erneut geprüft werden.

## Wenn die Wartung angehalten wurde

Ein fehlendes oder beschädigtes Protokoll wird nicht still durch einen leeren Speicher ersetzt. Öffne **Wartung wiederherstellen**:

1. **Erneut laden** versucht den vorhandenen Speicher zu lesen.
2. **Zurücksetzen** benötigt eine ausdrückliche Bestätigung und verwirft das alte EMBi-Laufprotokoll samt ausstehender Nachbereitung. Player, Sensoren und Emby-Geräte werden dabei nicht gelöscht. Ein neuer automatischer Termin liegt frühestens 24 Stunden später.

Bearbeite keine `.storage`-Dateien von Hand. Bei unklaren Ergebnissen zuerst den Bericht und die Diagnosedaten prüfen.
