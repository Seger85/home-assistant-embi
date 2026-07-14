from custom_components.emby.models import CleanupRunReport, MaintenanceState


def test_maintenance_state_round_trip() -> None:
    state = MaintenanceState(
        report=CleanupRunReport(
            status="completed",
            server_deleted=5,
            next_run_at="2026-07-15T12:00:00+00:00",
        ),
        initial_run_completed=True,
    )
    assert MaintenanceState.from_dict(state.as_dict()) == state
