# Security Policy

## Unterstützte Version

Sicherheitskorrekturen werden für die jeweils neueste reguläre EMBi-Stable-Version bereitgestellt.

## Sicherheitslücken melden

Keine API-Schlüssel, vollständigen Diagnosedateien oder privaten Geräte-/Benutzerdaten in öffentliche Issues einstellen. Hinweise zunächst privat an den Repository-Eigentümer `Seger85` melden.

## Vertrauliche Daten

API-Schlüssel, Serveradressen, Geräte-Historien-IDs, gemeldete Client-IDs, Geräte-/Clientnamen und Benutzernamen gelten als vertraulich. Diagnostics geben nur redigierte Konfiguration und aggregierte Zähler aus. Eine Datei ist vor externer Weitergabe dennoch manuell zu prüfen.

## Destruktive Funktionen

Serverhistorien-Löschung bleibt standardmäßig deaktiviert und benötigt Auswahl, Bestätigung und frische Validierung. Home-Assistant-Registry-Aktionen prüfen Domain, Plattform, Config Entry, Unique-ID und Wiedergabe. Fremde Entities werden niemals übernommen oder gelöscht. Ein Emby-Server-Backup ist der einzige vollständige Rollback für serverseitige Löschungen.
