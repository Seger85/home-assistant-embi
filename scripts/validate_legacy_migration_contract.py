#!/usr/bin/env python3
"""Validate the isolated published-upgrade contract."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"
MIGRATION = COMPONENT / "legacy_migration.py"
MIGRATION_TEST = ROOT / "tests" / "migration" / "test_legacy_options.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def local_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def main() -> None:
    require(MIGRATION.is_file(), "legacy migration module is missing")
    require(MIGRATION_TEST.is_file(), "legacy migration behavior tests are missing")

    migration = MIGRATION.read_text(encoding="utf-8")
    tests = MIGRATION_TEST.read_text(encoding="utf-8")
    functions = local_names(MIGRATION)

    require(
        {"legacy_cleanup_completed", "migrate_options"} <= functions,
        "migration API differs",
    )
    for legacy_key in (
        "client_mode",
        "ignored_player_keys",
        "ignored_reported_device_ids",
        "unresolved_ignored_ids",
        "ignored_device_ids",
        "server_cleanup_api_key",
    ):
        require(
            legacy_key in migration, f"legacy key is no longer handled: {legacy_key}"
        )

    for behavior in (
        "test_published_upgrade_preserves_cleanup_values",
        "test_published_visibility_modes_keep_effective_behavior",
        "test_published_ignore_rules_are_normalized_without_data_loss",
        "test_ambiguous_numeric_history_id_remains_unresolved",
        "test_published_upgrade_is_idempotent",
    ):
        require(behavior in tests, f"legacy migration coverage is missing: {behavior}")

    current_runtime = "\n".join(
        path.read_text(encoding="utf-8")
        for path in COMPONENT.glob("*.py")
        if path.name != "legacy_migration.py"
    )
    for legacy_name in (
        "client_mode",
        "ignored_player_keys",
        "ignored_reported_device_ids",
        "unresolved_ignored_ids",
        "ignored_device_ids",
        "server_cleanup_api_key",
    ):
        require(
            legacy_name not in current_runtime,
            f"legacy key escaped isolation: {legacy_name}",
        )

    require(
        not (ROOT / "docs" / "specs").exists(),
        "historical product specifications remain public",
    )
    print("Isolated legacy migration contract passed")


if __name__ == "__main__":
    main()
