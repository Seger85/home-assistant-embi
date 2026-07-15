import pytest

from custom_components.emby.models import CleanupRunReport, MaintenanceState


def test_maintenance_state_round_trip() -> None:
    state = MaintenanceState(
        report=CleanupRunReport(
            status="completed",
            server_deleted=5,
            next_run_at="2026-07-15T12:00:00+00:00",
            result_counts_complete=False,
        ),
        initial_run_completed=True,
    )
    assert MaintenanceState.from_dict(state.as_dict()) == state


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "unknown"),
        ("mode", "unknown"),
        ("follow_up_status", "unknown"),
    ],
)
def test_maintenance_report_rejects_unknown_enum_values(field: str, value: str) -> None:
    data = CleanupRunReport().as_dict()
    data[field] = value
    with pytest.raises(ValueError):
        CleanupRunReport.from_dict(data)
