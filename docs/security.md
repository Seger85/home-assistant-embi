# Datenschutz und Sicherheit

Der Emby-API-Schlüssel wird in Home Assistants Integrationskonfiguration gespeichert. HTTP-, WebSocket- und Coveranfragen verwenden den Authentifizierungsheader. Cover-URLs in Entity-Attributen enthalten keinen API-Schlüssel. HTTPS verwendet die Zertifikatsprüfung der gemeinsamen HA-Session; bei einem lokalen HTTP-Zugang ist die Verbindung nicht verschlüsselt.

Diagnosen erlauben nur bekannte Konfigurationsfelder. Zugangsdaten, Serveradressen und identifizierende Optionswerte werden redigiert; unbekannte Zusatzfelder werden nicht ungeprüft ausgegeben. Die Diagnose enthält Zähler, Aktualisierungszeitpunkte und Fehlergründe. Normale HA-Protokolle können weiterhin Entitätsnamen oder technische Identifikatoren enthalten. Prüfe Dateien und Screenshots deshalb vor dem Veröffentlichen.

Registry-Aktionen prüfen Domain, Plattform, ConfigEntry und eindeutige Identität. Fremde Entitäten bleiben unangetastet. Unklare Wiedergabe gilt nicht als inaktiv. Serverlöschungen benötigen die dafür gewählten Einstellungen beziehungsweise eine manuelle Bestätigung und frische Einzelprüfungen. Die Grenzen der Emby-API sind unter [Bereinigung](server-cleanup.md) erläutert.

GitHub Actions sind auf konkrete Commits festgelegt und werden über Dependabot aktualisiert. Prüfworkflows verwenden Leserechte; schreibende Automatisierung bleibt auf vertrauenswürdige Repository-Ereignisse begrenzt. Ein Pin des äußeren Workflows fixiert nicht automatisch sämtliche von externen Actions nachgeladenen Werkzeuge oder Container. Die Repository-Prüfung auf verdächtige Geheimnisse ist eine ergänzende Kontrolle und keine Garantie, dass nie ein Geheimnis veröffentlicht wurde.

Sicherheitsprobleme bitte gemäß [SECURITY.md](../SECURITY.md) vertraulich melden. Bearbeite keine internen `.storage`-Dateien von Hand.
