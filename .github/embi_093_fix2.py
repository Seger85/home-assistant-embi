from pathlib import Path

root = Path(__file__).resolve().parents[1]

replacements = {
    "tests/test_active_visibility_safety_090.py": [
        (
            '    assert "hide_user_group" in devices\n',
            '    assert "visibility[user_name] = any_visible" in devices\n'
            '    assert "not requested.get(player.player_key" in devices\n',
        ),
    ],
    "tests/test_maintenance_scheduler.py": [
        ("test_rc3_migration_schedules_once_after_120_seconds_and_persists", "test_migration_schedules_once_after_10_seconds_and_persists"),
        ("timedelta(seconds=120)", "timedelta(seconds=10)"),
    ],
    "tests/test_options_flow_contract.py": [
        (
            '    assert \'errors["base"] = "unsaved_changes"\' in server\n',
            '    assert "MANUAL_CLEANUP_SCOPE_ALL_SAFE" in server\n'
            '    assert \'errors["base"] = "invalid_selection"\' in server\n',
        ),
    ],
    "tests/test_player_context_090.py": [
        ('assert reason == "technical_app_without_playback"', 'assert reason == "explicit_technical_identity"'),
    ],
    "tests/test_repository_contract.py": [
        ('AUTO_CLEANUP_INITIAL_DELAY_SECONDS = 120', 'AUTO_CLEANUP_INITIAL_DELAY_SECONDS = 10'),
    ],
}

for relative, changes in replacements.items():
    path = root / relative
    text = path.read_text(encoding="utf-8")
    for old, new in changes:
        if old not in text:
            raise RuntimeError(f"Missing expected test contract in {relative}: {old!r}")
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
