from __future__ import annotations

from pathlib import Path


def source(name: str) -> str:
    return (Path("custom_components/emby") / name).read_text(encoding="utf-8")


def test_098_flow_extension_is_selected_and_keeps_final_apply_backgrounded() -> None:
    config_flow = source("config_flow.py")
    extension = source("options_flow_098.py")
    base = source("options_flow.py")
    assert "from .options_flow_098 import EmbyOptionsFlow" in config_flow
    assert 'menu.insert(1, "sensors")' in extension
    assert "remove_disabled_sensor_entities" in extension
    assert 'return self.async_abort(reason="apply_complete")' in base
    assert "async_create_task" in base


def test_cleanup_copy_separates_automatic_and_manual_age_behavior() -> None:
    strings = source("strings.json")
    german = source("translations/de.json")
    assert "Not yet due for automatic cleanup" in strings
    assert "Noch nicht automatisch fällig" in german
    assert "manual selection is independent" in strings
    assert "manuelle Auswahl ist unabhängig" in german
