# Workflows und Repository-Historie

Inventar vom 26. September 2026: GitHub meldete 58 Workflow-Registrierungen. Im aktuellen Quellbaum liegen sechs Workflowdateien. Dazu kommt GitHubs dynamischer Dependabot-Workflow. Die übrigen 51 sind deaktivierte historische Registrierungen und werden nicht erneut ausgeführt.

## Für den heutigen Betrieb erforderlich

| Datei / Registrierung | Aufgabe |
|---|---|
| `quality.yml` | Python-Prüfungen, Ruff, Typen, Verträge, Datenschutzprüfung und Tests mit echtem HA |
| `test-artifact.yml` | Unveröffentlichtes, reproduzierbares Testpaket |
| `hacs.yml` | HACS-Validierung |
| `hassfest.yml` | HA-Metadaten und Übersetzungen |
| `dependabot-automerge.yml` | Geprüfte Abhängigkeitsupdates und begrenzte automatische Reparatur |
| `release.yml` | Geschützter stabiler Release samt Paketprüfung und Wiederanlauf |
| Dependabot updates | Von GitHub verwaltete Abhängigkeitsaktualisierung |

Die Release-Automatisierung bleibt erhalten. Neue Einmal-Patchworkflows sind nicht nötig. Historische Laufprotokolle und Commitverweise dienen der Nachvollziehbarkeit; ihre alten Fehler sind keine offenen Fehler des aktuellen Produkts.

## Historische Registrierungen

**Kategorie 2:** historischer Beweis-/Diagnosewert; ausgewählte Ergebnisse und Commits erhalten, nicht als laufende Automatik reaktivieren. **Kategorie 3:** technisch erledigter Einmalmechanismus bzw. durch aktuelle CI ersetzt; kein Bestandteil des heutigen Produktbetriebs. Die historischen Einträge bleiben deaktiviert erhalten. Links zeigen auf einen tatsächlich abgerufenen damaligen Run-Commit. Die Snapshots wurden hinsichtlich Trigger, Berechtigungen, Schritten und Einmalzweck eingeordnet; alte eingebettete Patch-Payloads wurden nicht ausgeführt oder als heutiger Produktcode bewertet.

| Historische Datei | Kategorie | Begründung |
|---|---|---|
| [apply-embi-0.9.2.yml](https://github.com/Seger85/home-assistant-embi/blob/f978675a1a7a60ab3080e203d946f6e95d8f3e57/.github/workflows/apply-embi-0.9.2.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [apply-embi-0.9.4.yml](https://github.com/Seger85/home-assistant-embi/blob/b058c788a3d664d3ce53fd60e225dfe21baabe2b/.github/workflows/apply-embi-0.9.4.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [apply-embi-0.9.5-pr-v2.yml](https://github.com/Seger85/home-assistant-embi/blob/e2c68dde93ddf8e1d37f46e4d3ca9b7361329cf6/.github/workflows/apply-embi-0.9.5-pr-v2.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [apply-embi-0.9.5-pr.yml](https://github.com/Seger85/home-assistant-embi/blob/e7f550091b71c7e2859ae8945c7b64a41e69a20e/.github/workflows/apply-embi-0.9.5-pr.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [apply-embi-0.9.5.yml](https://github.com/Seger85/home-assistant-embi/blob/0ee81bca9c53273aaf892cb703ed49023f19fdcf/.github/workflows/apply-embi-0.9.5.yml) | 3 | Alter eingebetteter Patch; gelesener Snapshot zudem YAML-ungültig |
| [apply-stable-update.yml](https://github.com/Seger85/home-assistant-embi/blob/ff5af2a701d3d06d3faef0bcd14743cb0d759018/.github/workflows/apply-stable-update.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [contract-test-fix-once.yml](https://github.com/Seger85/home-assistant-embi/blob/910643d5168f00f30d1506fddb27cca8238846ec/.github/workflows/contract-test-fix-once.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [embi-09-cleanup-temp.yml](https://github.com/Seger85/home-assistant-embi/blob/4c31f6d5ef5c0f974f4c6ded53d38fab48a41276/.github/workflows/embi-09-cleanup-temp.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [embi-09-diagnostic.yml](https://github.com/Seger85/home-assistant-embi/blob/4c31f6d5ef5c0f974f4c6ded53d38fab48a41276/.github/workflows/embi-09-diagnostic.yml) | 2 | Historische Contractdiagnose |
| [embi-09-ensure-final.yml](https://github.com/Seger85/home-assistant-embi/blob/097b40b581de55e03f0412ecbef073121290aa9e/.github/workflows/embi-09-ensure-final.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [embi-09-evidence-complete.yml](https://github.com/Seger85/home-assistant-embi/blob/6af5a4836f0faf1989bfd706cc53c7e05eb828d9/.github/workflows/embi-09-evidence-complete.yml) | 2 | Damals erzeugte Anforderungs-/Evidenzzuordnung erhalten |
| [embi-09-evidence-update.yml](https://github.com/Seger85/home-assistant-embi/blob/c1f299effdff3ebe0f2d5897e639c81df1c657b8/.github/workflows/embi-09-evidence-update.yml) | 2 | Historische Implementierungs-/Nachweiszuordnung |
| [embi-09-finalize.yml](https://github.com/Seger85/home-assistant-embi/blob/c36fb30c9a1b131b9c104789046d37c5aa0d26e1/.github/workflows/embi-09-finalize.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [embi-09-listener-fix.yml](https://github.com/Seger85/home-assistant-embi/blob/32bd1819224ea605944eaf7486c8969fa8d9631b/.github/workflows/embi-09-listener-fix.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [embi-09-pytest-diagnostic.yml](https://github.com/Seger85/home-assistant-embi/blob/4c31f6d5ef5c0f974f4c6ded53d38fab48a41276/.github/workflows/embi-09-pytest-diagnostic.yml) | 2 | Historischer pytest-Nachweis |
| [embi-09-remove-dead-modules.yml](https://github.com/Seger85/home-assistant-embi/blob/5a4cdffedc4b878cafddd03cfad682aed64caeb8/.github/workflows/embi-09-remove-dead-modules.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [embi-09-safety-fix.yml](https://github.com/Seger85/home-assistant-embi/blob/54da539cafefe6412d072d297b729c7484753c4a/.github/workflows/embi-09-safety-fix.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [embi-09-style-fix.yml](https://github.com/Seger85/home-assistant-embi/blob/4ddcf9682d05e152533d36c49c5d5cd972eb21ed/.github/workflows/embi-09-style-fix.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [embi-09-test-fix.yml](https://github.com/Seger85/home-assistant-embi/blob/38788426a0ef32841197f16e71516e7b67d0f4e4/.github/workflows/embi-09-test-fix.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [embi-093-patch.yml](https://github.com/Seger85/home-assistant-embi/blob/9bff8af87a8af6ad6d3a783717906ebe479795c7/.github/workflows/embi-093-patch.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [embi-rc2-apply.yml](https://github.com/Seger85/home-assistant-embi/blob/da8f150028154c17c2cb0e6fb38ee805996b3908/.github/workflows/embi-rc2-apply.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [embi-rc2-sync.yml](https://github.com/Seger85/home-assistant-embi/blob/de8ed27a7333dcb120c45e5698ded205eb2848f4/.github/workflows/embi-rc2-sync.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [final-test-count.yml](https://github.com/Seger85/home-assistant-embi/blob/bd72269cf208196d4b994b27deeb88481b51982d/.github/workflows/final-test-count.yml) | 2 | Historische Testzahl und Releasebeleg |
| [fix-092-hassfest-once.yml](https://github.com/Seger85/home-assistant-embi/blob/32a8633b30b0416e537d50c06db667468f30e93c/.github/workflows/fix-092-hassfest-once.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [fix-092-ruff-once.yml](https://github.com/Seger85/home-assistant-embi/blob/96ef02ac586f7878401e69ae56c9321e7cf7536e/.github/workflows/fix-092-ruff-once.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [fix-092-style.yml](https://github.com/Seger85/home-assistant-embi/blob/b47ed3ecd09ae840eee892e7476a528bdb05460d/.github/workflows/fix-092-style.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [fix-092-test-once.yml](https://github.com/Seger85/home-assistant-embi/blob/4d5890104053d690cedd17f745f71481b76608c3/.github/workflows/fix-092-test-once.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [format-091-once.yml](https://github.com/Seger85/home-assistant-embi/blob/9aae8ca20d1b496456dac88393da3bb1c3012692/.github/workflows/format-091-once.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [format-autofix.yml](https://github.com/Seger85/home-assistant-embi/blob/427164f3ecc248687d87f42e6174e488952ff3f1/.github/workflows/format-autofix.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [format-diagnostic.yml](https://github.com/Seger85/home-assistant-embi/blob/d458dd25d565ae5a9379189e01d8b743f5d76a1d/.github/workflows/format-diagnostic.yml) | 2 | Historische Formatdiagnose; kein produktiver Bedarf |
| [format-final-once.yml](https://github.com/Seger85/home-assistant-embi/blob/8d00bf96a1565db77b48b722d25c3345eeea69d2/.github/workflows/format-final-once.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [format-report.yml](https://github.com/Seger85/home-assistant-embi/blob/427164f3ecc248687d87f42e6174e488952ff3f1/.github/workflows/format-report.yml) | 2 | Historischer Formatbericht |
| [inspect-092-ci.yml](https://github.com/Seger85/home-assistant-embi/blob/714979e7d8b2c22eefce29850c85604ce040addf/.github/workflows/inspect-092-ci.yml) | 3 | Trotz Inspect-Name mutierender einmaliger Source-/Übersetzungsfix |
| [inspect-092-generator.yml](https://github.com/Seger85/home-assistant-embi/blob/96d80423517275e8fb8ccc2d7b9efacd68c7fb94/.github/workflows/inspect-092-generator.yml) | 2 | Fehlerdiagnose des damaligen Generators |
| [inspect-092-hassfest.yml](https://github.com/Seger85/home-assistant-embi/blob/32a8633b30b0416e537d50c06db667468f30e93c/.github/workflows/inspect-092-hassfest.yml) | 3 | Trotz Inspect-Name mutierender einmaliger Source-/Übersetzungsfix |
| [inspect-stable-release-runs.yml](https://github.com/Seger85/home-assistant-embi/blob/d8553b0e53884bfc05a705a7924f033c5f99cc3b/.github/workflows/inspect-stable-release-runs.yml) | 2 | Historische Veröffentlichungsdiagnose |
| [legacy-migration-contract.yml](https://github.com/Seger85/home-assistant-embi/blob/dffed77069c1c020919b106646fcf5376d36fc2e/.github/workflows/legacy-migration-contract.yml) | 2 | Ehemaliger separater Contractjob; Inhalt heute in Quality integriert |
| [one-shot-format.yml](https://github.com/Seger85/home-assistant-embi/blob/6e959c8636afc9290d29b044e88ec16c6fe5db5c/.github/workflows/one-shot-format.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [patch-release-cleanup.yml](https://github.com/Seger85/home-assistant-embi/blob/afa3a934dd52759ce3428103b592580a89ba5e9e/.github/workflows/patch-release-cleanup.yml) | 3 | Einmalige Patch-/Releasebereinigung; gelesener Snapshot YAML-ungültig |
| [post-merge-repository-cleanup.yml](https://github.com/Seger85/home-assistant-embi/blob/c4196b0f291b2c322293b6c47b53796f614c417f/.github/workflows/post-merge-repository-cleanup.yml) | 3 | Abgeschlossene Repository-/Historienbereinigung mit Schreibrechten |
| [post-merge-verification.yml](https://github.com/Seger85/home-assistant-embi/blob/88b7d8db8edad34bcf57c5795c6ea0257d3eb178/.github/workflows/post-merge-verification.yml) | 2 | Exakte damalige Workflow-/Paketnachweise |
| [publish-embi-0.9.4.yml](https://github.com/Seger85/home-assistant-embi/blob/020e06f0b694d317a253950285bfd977ff993d96/.github/workflows/publish-embi-0.9.4.yml) | 3 | Versionsgebundener Publisher; durch kanonische Releasepipeline ersetzt |
| [pytest-diagnostic.yml](https://github.com/Seger85/home-assistant-embi/blob/8d5134364bbe7a33c26662771bd580730611a9aa/.github/workflows/pytest-diagnostic.yml) | 2 | Historische Testdiagnose |
| [pytest-report-once.yml](https://github.com/Seger85/home-assistant-embi/blob/ff0134a3348590ca35ae9547990a92c5641c53a4/.github/workflows/pytest-report-once.yml) | 2 | Einmaliger vollständiger Testbericht |
| [release-proof.yml](https://github.com/Seger85/home-assistant-embi/blob/c47ce2c817e50b0a35c622d10d4f4934976a689c/.github/workflows/release-proof.yml) | 2 | Release-/Assetnachweis; enthielt auch temporäre Branchlöschung |
| [release-request-finalize.yml](https://github.com/Seger85/home-assistant-embi/blob/a596d8fa20143004d89da2765255713897b4dbc2/.github/workflows/release-request-finalize.yml) | 3 | Alter Veröffentlichungsmechanismus; aktuelle Pipeline übernimmt Aufgabe |
| [release-verification-audit.yml](https://github.com/Seger85/home-assistant-embi/blob/5544b5a5a05f07f86f7c6aa3359e511f6b7b456b/.github/workflows/release-verification-audit.yml) | 2 | Historischer Release-/Checksum-Nachweis |
| [source-snapshot.yml](https://github.com/Seger85/home-assistant-embi/blob/064d94d79cb073832f9330539686e327d1c4458f/.github/workflows/source-snapshot.yml) | 2 | Historischer Sourcebeleg; aktuelle Commitreferenz ersetzt laufenden Job |
| [stable-autofix.yml](https://github.com/Seger85/home-assistant-embi/blob/d4e0b6fc2ada43ab31d930087bf4f616748a3a69/.github/workflows/stable-autofix.yml) | 3 | Versionsgebundener Patch-/Fix-/Synchronisations- oder Selbstentfernungsjob; erledigt |
| [verify-rc2-release-final.yml](https://github.com/Seger85/home-assistant-embi/blob/f54b67373e146b7492fda67ca118735e8e38dffd/.github/workflows/verify-rc2-release-final.yml) | 2 | Abschließender RC2-Nachweis; enthielt Branch-/Issue-/PR-Schreibrechte |
| [verify-rc2-release.yml](https://github.com/Seger85/home-assistant-embi/blob/9cefb55ccf1d2b0243302ebda39c17428166e0bd/.github/workflows/verify-rc2-release.yml) | 2 | RC2-Nachweis; enthielt auch temporäre Branchbereinigung |

Einordnung: **18 historische Einträge mit vorrangigem Nachweiswert**, **33 erledigte technische Einmalmechanismen**. Zusammen mit den sieben aktiven Registrierungen ergibt das die verifizierten 58 API-Einträge. Historische Fehlruns sind keine offenen Fehler der heutigen sechs Workflowdateien.

