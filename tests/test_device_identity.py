from __future__ import annotations

from datetime import UTC, datetime

from custom_components.emby.api import EmbyDeviceRecord


def test_devices_response_separates_record_and_client_identity() -> None:
    record = EmbyDeviceRecord.from_api(
        {
            "Id": "341",
            "ReportedDeviceId": "synthetic-client-1",
            "Name": "Synthetic device",
            "AppName": "Emby Windows",
            "AppVersion": "2.315.2.0",
            "LastUserName": "Example User",
            "DateLastActivity": "2026-07-13T18:35:44.0000000Z",
        }
    )

    assert record.record_id == "341"
    assert record.reported_device_id == "synthetic-client-1"
    assert record.player_key == "synthetic-client-1.Emby Windows"
    assert record.record_id not in record.player_key


def test_missing_reported_device_id_falls_back_to_record_id() -> None:
    record = EmbyDeviceRecord.from_api(
        {"Id": "42", "Name": "Legacy client", "AppName": "Old App"}
    )

    assert record.reported_device_id == "42"
    assert record.player_key == "42.Old App"


def test_label_contains_human_context_but_not_internal_record_id() -> None:
    record = EmbyDeviceRecord.from_api(
        {
            "Id": "99",
            "ReportedDeviceId": "client-1",
            "Name": "Living room",
            "AppName": "AndroidTv",
            "LastUserName": "Alex",
        }
    )

    assert record.label == "Living room · AndroidTv · Alex"
    assert "99" not in record.label


def test_server_cleanup_label_contains_no_reported_client_id() -> None:
    record = EmbyDeviceRecord.from_api(
        {
            "Id": "history-record-0001",
            "ReportedDeviceId": "private-client-identity",
            "Name": "Living room",
            "AppName": "AndroidTv",
            "AppVersion": "3.4.5",
            "DateLastActivity": "2026-07-13T18:35:44Z",
        }
    )

    assert "private-client-identity" not in record.server_cleanup_label
    assert "AndroidTv 3.4.5" in record.server_cleanup_label
    assert "ID hist…0001" in record.server_cleanup_label


def test_seven_digit_emby_timestamp_is_parsed_as_utc() -> None:
    record = EmbyDeviceRecord.from_api(
        {
            "Id": "history-record-0001",
            "ReportedDeviceId": "synthetic-client",
            "Name": "Synthetic device",
            "AppName": "Emby App",
            "DateLastActivity": "2026-07-13T18:35:44.1234567Z",
        }
    )

    assert record.last_activity_datetime == datetime(
        2026,
        7,
        13,
        18,
        35,
        44,
        123456,
        tzinfo=UTC,
    )
    assert record.activity_label == "2026-07-13 18:35 UTC"


def test_invalid_activity_timestamp_is_not_cleanup_eligible() -> None:
    record = EmbyDeviceRecord.from_api(
        {
            "Id": "history-record-0001",
            "ReportedDeviceId": "synthetic-client",
            "Name": "Synthetic device",
            "AppName": "Emby App",
            "DateLastActivity": "not-a-date",
        }
    )

    assert record.last_activity_datetime is None
