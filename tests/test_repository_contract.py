from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


def test_manifest_points_to_canonical_repository() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text())
    assert manifest["domain"] == "emby"
    assert manifest["name"] == "Emby Integration - EMBi"
    assert manifest["version"] == "0.9.3"
    assert manifest["codeowners"] == ["@Seger85"]
    assert manifest["documentation"].endswith("Seger85/home-assistant-embi")
    assert manifest["issue_tracker"].endswith("Seger85/home-assistant-embi/issues")
    assert manifest["requirements"] == ["pyEmby==1.10"]
    assert manifest["loggers"] == ["pyemby"]


def test_legacy_yaml_platform_is_removed() -> None:
    media_player = (COMPONENT / "media_player.py").read_text()
    assert "PLATFORM_SCHEMA" not in media_player
    assert "async_setup_platform" not in media_player
    assert "Legacy YAML" not in media_player


def test_english_strings_match_translation_source() -> None:
    strings = json.loads((COMPONENT / "strings.json").read_text())
    english = json.loads((COMPONENT / "translations" / "en.json").read_text())
    assert strings == english


def test_cleanup_uses_only_main_connection_key_and_diagnostics_redact_it() -> None:
    diagnostics = (COMPONENT / "diagnostics.py").read_text()
    cleanup_flow = (COMPONENT / "options_cleanup.py").read_text()
    options_flow = (COMPONENT / "options_flow.py").read_text()
    runtime_setup = (COMPONENT / "entry_setup.py").read_text()
    assert "from homeassistant.const import CONF_API_KEY, CONF_HOST" in diagnostics
    assert '"title": "<redacted>"' in diagnostics
    assert "async_redact_data(dict(entry.data), {CONF_API_KEY, CONF_HOST})" in diagnostics
    assert "CONF_SERVER_CLEANUP_API_KEY" not in diagnostics
    assert "server_cleanup_api_key" not in cleanup_flow
    assert "await self._devices()" in cleanup_flow
    assert "return await self._runtime.api_client.async_get_devices()" in options_flow
    assert "api_key=entry.data[CONF_API_KEY]" in runtime_setup


def test_password_field_does_not_reuse_stored_secret_as_default() -> None:
    config_flow = (COMPONENT / "config_flow.py").read_text()
    assert "defaults.get(CONF_API_KEY" not in config_flow
    assert "submitted_api_key or entry.data[CONF_API_KEY]" in config_flow


def test_media_player_unique_id_contract_is_unchanged() -> None:
    media_player = (COMPONENT / "media_player.py").read_text()
    assert "self._attr_unique_id = device_id" in media_player


def test_diagnostics_redact_identity_options_and_expose_aggregate_evidence() -> None:
    diagnostics = (COMPONENT / "diagnostics.py").read_text()
    models = (COMPONENT / "models.py").read_text()
    api = (COMPONENT / "api.py").read_text()
    for identity_option in (
        "CONF_ALLOWED_DEVICE_IDS",
        "CONF_HIDDEN_EXACT_PLAYERS",
        "CONF_HIDDEN_WHOLE_DEVICES",
        "CONF_UNRESOLVED_LEGACY_RULES",
        "CONF_USER_MASTER_VISIBILITY",
    ):
        assert identity_option in diagnostics
    assert '"last_run": runtime.maintenance_state.report.as_dict()' in diagnostics
    assert '"last_player_action"' in diagnostics
    assert '"last_restore"' in diagnostics
    assert '"migration"' in diagnostics
    assert '"server_missing_entities"' in diagnostics
    assert '"home_assistant_orphans"' in diagnostics
    for forbidden_report_field in (
        "record_id",
        "reported_device_id",
        "player_key",
        "user_name",
        "api_key",
    ):
        assert (
            forbidden_report_field
            not in models.split("class CleanupRunReport", 1)[1].split(
                "class MaintenanceActionSummary", 1
            )[0]
        )
    assert "def as_diagnostics" not in api


def test_automatic_cleanup_contract_is_explicit_persistent_and_uncapped() -> None:
    constants = (COMPONENT / "const.py").read_text()
    cleanup = (COMPONENT / "cleanup.py").read_text()
    execution = (COMPONENT / "maintenance_cycle_execute.py").read_text()
    scheduler = (COMPONENT / "maintenance_scheduler.py").read_text()
    assert "AUTO_CLEANUP_INITIAL_DELAY_SECONDS = 10" in constants
    assert "AUTO_CLEANUP_INTERVAL_HOURS = 24" in constants
    assert "DEFAULT_SERVER_CLEANUP_AGE_DAYS = 365" in constants
    assert "there is deliberately no run cap" in cleanup
    assert "candidates = plan.candidates" in execution
    assert "[:" not in execution
    assert "async_track_point_in_utc_time" in scheduler
    assert "report.next_run_at" in scheduler


def test_registry_removal_requires_exact_post_delete_revalidation() -> None:
    execution = (COMPONENT / "maintenance_cycle_execute.py").read_text()
    evaluator = (COMPONENT / "maintenance_registry_evaluate.py").read_text()
    committer = (COMPONENT / "maintenance_registry_commit.py").read_text()
    assert "remaining = await client.async_get_devices()" in execution
    assert "plan_registry_followup" in execution
    assert "remaining_player_keys" in evaluator
    assert "states.get(entity.entity_id) is not None" in evaluator
    assert "entity.config_entry_id != entry.entry_id" in evaluator
    assert "str(entity.unique_id) != key" in evaluator
    assert "apply_exact_registry_removals" in committer


def test_release_assets_and_request_branch_contract() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text()
    publish_block = workflow.split("files: |", 1)[1].split("fail_on_unmatched_files", 1)[0]
    assert "dist/embi.zip" in publish_block
    assert "dist/embi.zip.sha256" in publish_block
    assert "BUILD_COMMIT" not in publish_block
    assert "cmp dist/embi.zip verify-release/embi.zip" in workflow
    assert "origin/main" in workflow
    assert 'tags:\n      - "v*"' in workflow
    assert 'branches:\n      - "release/v*"' in workflow
    assert '"[0-9]*"' not in workflow
    assert "^v[0-9]+" in workflow
    assert "Remove verified release request branch" in workflow
    assert "prerelease: false" in workflow
    assert "make_latest: true" in workflow


def test_test_package_is_bound_to_exact_source_commit() -> None:
    workflow = (ROOT / ".github" / "workflows" / "test-artifact.yml").read_text()
    assert "github.event.pull_request.head.sha || github.sha" in workflow
    assert "ref: ${{ env.BUILD_COMMIT_SHA }}" in workflow
    assert '--commit "${BUILD_COMMIT_SHA}"' in workflow
    assert 'test "$(cat dist/BUILD_COMMIT)" = "${BUILD_COMMIT_SHA}"' in workflow
    assert "embi-test-${{ env.BUILD_COMMIT_SHA }}" in workflow
    assert "--expected-version 0.9.3" in workflow
