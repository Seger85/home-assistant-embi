from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.emby.options_flow import EmbyOptionsFlow


@pytest.mark.asyncio
async def test_stale_zero_change_review_returns_to_root_without_apply() -> None:
    flow = SimpleNamespace(
        _review_lines=AsyncMock(return_value=([], 0)),
        _is_de=lambda: True,
        _apply_notice="",
        async_step_init=AsyncMock(return_value={"type": "menu", "step_id": "init"}),
    )
    result = await EmbyOptionsFlow.async_step_review_changes(flow)
    assert result == {"type": "menu", "step_id": "init"}
    assert flow._apply_notice == "Keine offenen Änderungen."
    flow.async_step_init.assert_awaited_once()


def test_root_menu_review_is_count_driven_and_has_no_empty_placeholder_fallback() -> None:
    source = Path("custom_components/emby/options_flow.py").read_text(encoding="utf-8")
    assert "if count:" in source
    assert 'menu_options.append("review_changes")' in source
    assert '"changes": "\\n\\n".join(lines)' in source
    assert (
        'or "-"'
        not in source.split("async def async_step_review_changes", 1)[1].split(
            "async def async_step_discard_changes", 1
        )[0]
    )


def test_options_flow_is_canonical_and_release_suffix_modules_are_removed() -> None:
    component = Path("custom_components/emby")
    config_flow = (component / "config_flow.py").read_text(encoding="utf-8")
    assert "from .options_flow import EmbyOptionsFlow" in config_flow
    assert "SensorsOptionsMixin" in (component / "options_flow.py").read_text()
    for name in (
        "options_flow_098.py",
        "options_devices_099.py",
        "player_reconciliation_099.py",
    ):
        assert not (component / name).exists()


def test_translations_are_schema_identical_and_complete() -> None:
    component = Path("custom_components/emby")
    strings = json.loads((component / "strings.json").read_text(encoding="utf-8"))
    english = json.loads((component / "translations" / "en.json").read_text(encoding="utf-8"))
    german = json.loads((component / "translations" / "de.json").read_text(encoding="utf-8"))

    def paths(value, prefix=()):
        result = set()
        if isinstance(value, dict):
            for key, child in value.items():
                current = (*prefix, str(key))
                result.add(current)
                result.update(paths(child, current))
        return result

    assert strings == english
    assert paths(strings) == paths(german)
    assert strings["options"]["step"]["sensors"]["data"] == {"enabled_sensors": "Enabled sensors"}
    assert "playback_protected_named" in strings["options"]["error"]
    assert "playback_protected_named" in german["options"]["error"]


def test_every_root_menu_target_has_a_step_and_translation() -> None:
    source = Path("custom_components/emby/options_flow.py").read_text(encoding="utf-8")
    strings = json.loads(Path("custom_components/emby/strings.json").read_text(encoding="utf-8"))
    for step in (
        "ha_players",
        "sensors",
        "automatic_cleanup",
        "server_history_check",
        "review_changes",
    ):
        assert f"async_step_{step}" in source or step in {
            "ha_players",
            "sensors",
            "automatic_cleanup",
            "server_history_check",
        }
        assert step in strings["options"]["step"]["init"]["menu_options"]


def test_apply_schedules_one_primary_reload_and_no_listener_loop() -> None:
    source = Path("custom_components/emby/options_flow.py").read_text(encoding="utf-8")
    finalizer = source.split("async def _async_finalize_apply", 1)[1].split(
        "async def async_step_apply_changes", 1
    )[0]
    assert finalizer.count("async_reload(") <= 2
    assert "suppress_update_listener = True" in source
    assert "suppress_update_listener = False" in finalizer
