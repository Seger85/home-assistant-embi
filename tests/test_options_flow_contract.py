from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


def source(name: str) -> str:
    return (COMPONENT / name).read_text(encoding="utf-8")


def function_block(text: str, name: str, next_name: str | None = None) -> str:
    start = text.index(f"async def {name}")
    end = text.index(f"async def {next_name}", start) if next_name else len(text)
    return text[start:end]


def test_normal_options_pages_are_draft_only_and_have_one_apply_write() -> None:
    options_flow = source("options_flow.py")
    clients = source("options_clients.py")
    registry = source("options_registry.py")
    maintenance = source("maintenance_flow.py")

    assert "async_update_entry" not in "\n".join((options_flow, clients, registry, maintenance))
    assert options_flow.count("self.async_create_entry(") == 1
    assert "self._draft_options" in clients
    assert "self._draft_options" in maintenance
    assert "return await self.async_step_init()" in clients
    assert "return await self.async_step_init()" in maintenance


def test_apply_no_change_discard_and_close_contract() -> None:
    options_flow = source("options_flow.py")
    apply_block = function_block(options_flow, "async_step_apply", "async_step_discard")
    discard_block = function_block(options_flow, "async_step_discard", "async_step_about")

    assert "if updated == original_normalized" in apply_block
    assert 'reason="no_changes"' in apply_block
    assert apply_block.index('reason="no_changes"') < apply_block.index("self.async_create_entry(")
    assert "self._draft.discard()" in discard_block
    assert "async_reload" not in options_flow
    assert "__del__" not in options_flow
    assert "async_close" not in options_flow


def test_dirty_draft_blocks_maintenance_actions() -> None:
    registry = source("options_registry.py")
    maintenance = source("maintenance_flow.py")
    guard = 'if self._dirty:\n            return self.async_abort(reason="unsaved_changes")'

    assert guard in registry
    assert maintenance.count('return self.async_abort(reason="unsaved_changes")') >= 1


def test_automatic_warning_uses_boolean_without_text_phrase() -> None:
    maintenance = source("maintenance_flow.py")
    confirm = function_block(
        maintenance,
        "async_step_server_auto_cleanup_confirm",
        "async_step_server_cleanup",
    )

    assert "CONF_CONFIRM_AUTO_CLEANUP" in confirm
    assert "BooleanSelector" in confirm
    assert "TextSelector" not in confirm
    assert "confirmation_text" not in confirm
    assert "AUTO_CLEANUP_CONFIRMATION" not in maintenance


def test_automation_is_not_scheduled_from_the_draft_flow() -> None:
    combined = "\n".join(
        source(name)
        for name in (
            "options_flow.py",
            "options_clients.py",
            "options_registry.py",
            "maintenance_flow.py",
        )
    )

    assert "async_setup_automatic_cleanup" not in combined
    assert "async_schedule_automatic_cleanup" not in combined
