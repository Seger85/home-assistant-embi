from __future__ import annotations

import json
from pathlib import Path

from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.helpers import (
    server_device_confirmation_details,
    server_device_selector_options,
)

ROOT = Path(__file__).resolve().parents[1]


def _record(
    record_id: str,
    *,
    app_version: str = "9.9.9",
    timestamp: str = "2026-01-05T10:30:00Z",
) -> EmbyDeviceRecord:
    return EmbyDeviceRecord.from_api(
        {
            "Id": record_id,
            "ReportedDeviceId": f"reported-{record_id}",
            "Name": "Living Room",
            "AppName": "Emby TV",
            "AppVersion": app_version,
            "LastUserName": "Alex",
            "DateLastActivity": timestamp,
            "SupportsPlayback": True,
        }
    )


def test_mobile_cleanup_labels_hide_versions_utc_and_internal_ids() -> None:
    records = [_record("private-record-a"), _record("private-record-b")]
    options = server_device_selector_options(
        records,
        time_zone="Europe/Berlin",
        german=True,
    )
    labels = list(options.values())
    assert labels[0].startswith("Living Room · Emby TV · Alex · zuletzt 05.01.2026")
    assert labels[0] != labels[1]
    for label in labels:
        assert "9.9.9" not in label
        assert "UTC" not in label
        assert "private-record" not in label
        assert "reported-" not in label
    details = server_device_confirmation_details(
        records,
        time_zone="Europe/Berlin",
        german=True,
    )
    assert "9.9.9" in details
    assert "CET" in details
    assert "Record" in details


def _key_paths(value, prefix=()):
    if not isinstance(value, dict):
        return set()
    result = set()
    for key, child in value.items():
        path = (*prefix, str(key))
        result.add(path)
        result.update(_key_paths(child, path))
    return result


def test_translation_structures_remain_identical() -> None:
    strings = json.loads((ROOT / "custom_components/emby/strings.json").read_text(encoding="utf-8"))
    english = json.loads(
        (ROOT / "custom_components/emby/translations/en.json").read_text(encoding="utf-8")
    )
    german = json.loads(
        (ROOT / "custom_components/emby/translations/de.json").read_text(encoding="utf-8")
    )
    assert strings == english
    assert _key_paths(strings) == _key_paths(german)


def test_legacy_back_is_not_a_boolean_selector_in_options_sources() -> None:
    for name in ("options_devices.py", "options_cleanup.py", "options_ha_cleanup.py"):
        source = (ROOT / "custom_components/emby" / name).read_text(encoding="utf-8")
        assert "vol.Optional(CONF_BACK" not in source
        assert "vol.Required(CONF_BACK" not in source
        assert "CONF_BACK, default=False" not in source
