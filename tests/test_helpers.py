from __future__ import annotations

from datetime import UTC, datetime

import pytest
from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.const import (
    AGE_PRESET_7,
    AGE_PRESET_30,
    AGE_PRESET_90,
    AGE_PRESET_180,
    AGE_PRESET_365,
    AGE_PRESET_CUSTOM,
)
from custom_components.emby.helpers import (
    age_days_from_input,
    age_preset_for_days,
    server_device_confirmation_details,
    server_device_selector_options,
)


@pytest.mark.parametrize(
    ("preset", "days"),
    [
        (AGE_PRESET_7, 7),
        (AGE_PRESET_30, 30),
        (AGE_PRESET_90, 90),
        (AGE_PRESET_180, 180),
        (AGE_PRESET_365, 365),
    ],
)
def test_age_presets_are_numeric_source_of_truth(preset: str, days: int) -> None:
    assert age_days_from_input(preset, 364) == days
    assert age_preset_for_days(days) == preset


def test_custom_age_values_are_preserved() -> None:
    assert age_days_from_input(AGE_PRESET_CUSTOM, 364) == 364
    assert age_preset_for_days(364) == AGE_PRESET_CUSTOM
    with pytest.raises(ValueError):
        age_days_from_input(AGE_PRESET_CUSTOM, None)


def _record(record_id: str, *, app: str = "Emby TV") -> EmbyDeviceRecord:
    return EmbyDeviceRecord.from_api(
        {
            "Id": record_id,
            "ReportedDeviceId": "same-device",
            "Name": "Living room",
            "AppName": app,
            "LastUserName": "Alex",
            "DateLastActivity": datetime(2026, 7, 19, 12, tzinfo=UTC).isoformat(),
        }
    )


def test_server_selectors_are_stable_and_do_not_expose_internal_ids() -> None:
    records = [_record("private-a"), _record("private-b")]
    options = server_device_selector_options(records, time_zone="UTC", german=False)
    assert set(options) == {"private-a", "private-b"}
    assert all("private-" not in label for label in options.values())
    assert all("record" in label for label in options.values())


def test_confirmation_details_are_separate_from_compact_selector_labels() -> None:
    [item] = [_record("private-record")]
    details = server_device_confirmation_details([item], time_zone="UTC", german=True)
    assert "Living room" in details
    assert "Emby TV" in details
    assert item.short_record_id in details
