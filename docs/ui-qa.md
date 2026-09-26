# Oberfläche prüfen

Automatisierte Flow-Tests prüfen Navigation, Entwurf, Bestätigung und Speichern. Sie ersetzen keine Sichtprüfung mit unterschiedlichen Bildschirmgrößen.

## Prüfablauf für Desktop, iPhone und iPad

1. Integration hinzufügen, ungültigen Schlüssel korrigieren und eine erneute Anmeldung durchführen.
2. Optionen öffnen: Player, technische Zugriffe, Benutzergruppen und Sensoren müssen verständlich beschriftet sein.
3. Eine Auswahl ändern, zurückgehen, die Zusammenfassung lesen und verwerfen. Es darf nichts gespeichert werden.
4. Dieselbe Auswahl übernehmen: Dialog schließt, Integration lädt einmal planmäßig neu, Auswahl bleibt erhalten.
5. Eine Gruppe geöffnet lassen, während sich der Wiedergabestatus ändert. Die bestätigte Auswahl muss weiter dieselben Player betreffen.
6. Bereinigungsseiten bis zur Bestätigung prüfen. Löschungen nur mit eigens dafür angelegten Testeinträgen ausführen.
7. Lange Gerätenamen, viele Einträge, leere Gruppen und Verbindungsfehler prüfen. Schaltflächen und Rücknavigation müssen erreichbar bleiben.
8. Dashboard mit null, einem und mehreren aktiven Playern sowie Pause und Nichterreichbarkeit prüfen. Pausierte Player verwenden dieselbe Kartenform wie laufende.

Ein Releasebericht muss unterscheiden zwischen durchgeführten Browserprüfungen, automatisierten Tests und noch ausstehender Prüfung auf einem echten Mobilgerät. Desktop-Viewport-Simulation allein ist kein Nachweis für jede iOS-App-Version.
