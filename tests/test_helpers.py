from __future__ import annotations

import pytest

from custom_components.emby.const import (
    AGE_PRESET_7,
    AGE_PRESET_30,
    AGE_PRESET_90,
    AGE_PRESET_180,
    AGE_PRESET_365,
    AGE_PRESET_CUSTOM,
)
from custom_components.emby.helpers import age_days_from_input, age_preset_for_days


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
    assert age_days_from_input(AGE_PRESET_CUSTOM, 417) == 417
    assert age_preset_for_days(364) == AGE_PRESET_CUSTOM
    with pytest.raises(ValueError):
        age_days_from_input(AGE_PRESET_CUSTOM, None)
