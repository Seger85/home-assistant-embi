## Zusammenfassung

<!-- Was wird geändert und warum? -->

## Risiko und Migration

- [ ] bestehende Entity-IDs/Unique IDs unverändert
- [ ] keine Migration erforderlich
- [ ] Migration beschrieben und getestet
- [ ] destruktive Funktion betroffen

## Verifikation

- [ ] `python -m compileall -q custom_components/emby`
- [ ] JSON validiert
- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] `pytest -q`
- [ ] deutsche und englische Texte geprüft
- [ ] Diagnostics auf sensible Daten geprüft
- [ ] visuelle QA durchgeführt oder nachvollziehbar als offen dokumentiert

## Rollback

<!-- Wie wird die Änderung sicher zurückgenommen? -->
