from __future__ import annotations

from custom_components.emby.options_draft import OptionsDraft


def test_multiple_pages_change_only_the_draft_until_apply() -> None:
    stored = {"client_mode": "all", "server_cleanup_enabled": False}
    draft = OptionsDraft.from_options(stored)
    draft.update({"client_mode": "allowlist"})
    draft.update({"server_cleanup_enabled": True})
    assert stored == {"client_mode": "all", "server_cleanup_enabled": False}
    assert draft.original == stored
    assert draft.current == {"client_mode": "allowlist", "server_cleanup_enabled": True}
    assert draft.dirty is True
    applied = draft.applied()
    assert applied == draft.current
    assert applied is not draft.current


def test_discard_and_close_without_apply_leave_stored_options_unchanged() -> None:
    stored = {"server_auto_cleanup_age_days": 364}
    draft = OptionsDraft.from_options(stored)
    draft.update({"server_auto_cleanup_age_days": 365})
    draft.discard()
    assert draft.current == stored
    assert draft.dirty is False
    assert stored["server_auto_cleanup_age_days"] == 364
