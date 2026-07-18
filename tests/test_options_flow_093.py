from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.cleanup import plan_device_cleanup
from custom_components.emby.player_context import CLIENT_CLASS_TECHNICAL, classify_client


def _record(*, record_id: str, days_old: int, name: str = "TV", app: str = "Emby TV"):
    day = datetime(2026, 7, 18, tzinfo=UTC).timestamp() - days_old * 86400
    stamp = datetime.fromtimestamp(day, tz=UTC).isoformat()
    return EmbyDeviceRecord(
        record_id=record_id,
        reported_device_id=record_id,
        name=name,
        app_name=app,
        last_user_name="EmbyAdmin_Seger",
        last_activity_date=stamp,
    )


def test_manual_all_safe_scope_includes_recent_but_never_active() -> None:
    now = datetime(2026, 7, 18, tzinfo=UTC)
    recent = _record(record_id="recent", days_old=2)
    active = _record(record_id="active", days_old=1)
    normal = plan_device_cleanup([recent, active], now=now, age_days=180)
    assert normal.candidates == ()
    all_safe = plan_device_cleanup(
        [recent, active],
        now=now,
        age_days=180,
        active_player_keys={active.player_key},
        ignore_age=True,
    )
    assert all_safe.candidates == (recent,)
    assert all_safe.skipped_active == (active,)


def test_explicit_technical_device_with_admin_user_is_technical() -> None:
    record = _record(
        record_id="homarr",
        days_old=1,
        name="Emby Homarr",
        app="Emby",
    )
    client_class, reason = classify_client([record], registry_backed=True)
    assert client_class == CLIENT_CLASS_TECHNICAL
    assert reason == "explicit_technical_identity"


def test_active_technical_identity_remains_playback_protected() -> None:
    record = _record(
        record_id="ha",
        days_old=1,
        name="Home Assistant player",
        app="Emby",
    )
    client_class, reason = classify_client([record], runtime_state="playing")
    assert client_class != CLIENT_CLASS_TECHNICAL
    assert reason == "observed_active_playback"


def test_automatic_path_cannot_bypass_age_contract_source() -> None:
    source = Path("custom_components/emby/maintenance_cycle_execute.py").read_text(encoding="utf-8")
    assert "ignore_age=ignore_age if mode != RUN_MODE_AUTOMATIC else False" in source


def test_apply_returns_root_and_group_uses_boolean_switches_source() -> None:
    flow = Path("custom_components/emby/options_flow.py").read_text(encoding="utf-8")
    devices = Path("custom_components/emby/options_devices.py").read_text(encoding="utf-8")
    apply_tail = flow.split("async def async_step_apply_changes", 1)[1]
    assert 'return self.async_abort(reason="apply_complete")' in apply_tail
    assert "await self.hass.config_entries.async_reload" not in apply_tail
    group = devices.split("async def async_step_player_group", 1)[1].split(
        "async def async_step_player_exceptions", 1
    )[0]
    assert "selector.BooleanSelector()" in group
    assert "CONF_HIDDEN_PAGE_PLAYER_KEYS" not in group
    assert "CONF_PLAYER_ACTION" not in devices
    assert "CONF_SELECTED_PLAYER_KEY" not in group
