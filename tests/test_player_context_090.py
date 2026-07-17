from __future__ import annotations

from types import SimpleNamespace

from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.options_model import default_options_090
from custom_components.emby.player_context import (
    CLIENT_CLASS_PLAYBACK,
    CLIENT_CLASS_TECHNICAL,
    CLIENT_CLASS_UNKNOWN,
    GROUP_SHARED,
    GROUP_TECHNICAL,
    GROUP_UNASSIGNED,
    GROUP_USER_PREFIX,
    PLAYBACK_PAUSED,
    PLAYBACK_PLAYING,
    build_player_catalog,
    catalog_stats,
    classify_client,
    filter_player_catalog,
    group_player_catalog,
)


def record(
    *,
    record_id: str,
    reported_id: str,
    app: str,
    name: str = "Living room TV",
    user: str | None = None,
    users: list[str] | None = None,
    client_type: str | None = None,
    supports_playback: bool | None = None,
) -> EmbyDeviceRecord:
    data = {
        "Id": record_id,
        "ReportedDeviceId": reported_id,
        "Name": name,
        "AppName": app,
    }
    if user is not None:
        data["LastUserName"] = user
    if users is not None:
        data["UserNames"] = users
    if client_type is not None:
        data["ClientType"] = client_type
    if supports_playback is not None:
        data["SupportsPlayback"] = supports_playback
    return EmbyDeviceRecord.from_api(data)


def entity(
    unique_id: str,
    *,
    entity_id: str | None = None,
    name: str = "Wohnzimmer Emby",
    disabled: bool = False,
):
    return SimpleNamespace(
        domain="media_player",
        platform="emby",
        config_entry_id="entry",
        unique_id=unique_id,
        entity_id=entity_id
        or f"media_player.{unique_id.casefold().replace(' ', '_').replace('.', '_')}",
        name=name,
        original_name="Emby player",
        disabled_by="user" if disabled else None,
        hidden_by=None,
    )


class States:
    def __init__(self, values: dict[str, str] | None = None) -> None:
        self.values = values or {}

    def get(self, entity_id: str):
        value = self.values.get(entity_id)
        return SimpleNamespace(state=value) if value is not None else None


def test_known_user_shared_and_special_groups() -> None:
    alex = record(record_id="1", reported_id="a", app="TV", user="Alex")
    shared_a = record(
        record_id="2",
        reported_id="shared",
        app="Tablet",
        users=["Alex", "Sam"],
    )
    shared_b = record(
        record_id="3",
        reported_id="shared",
        app="Tablet",
        user="Sam",
    )
    technical = record(
        record_id="4",
        reported_id="api",
        app="Access",
        client_type="api_only",
        supports_playback=False,
    )
    unresolved_but_registered = record(
        record_id="5", reported_id="mystery", app="Emby Toolbox"
    )
    entries = [
        entity(alex.player_key),
        entity(shared_a.player_key),
        entity(technical.player_key),
        entity(unresolved_but_registered.player_key),
    ]

    players = build_player_catalog(
        [alex, shared_a, shared_b, technical, unresolved_but_registered],
        registry_entries=entries,
        states=States(),
        entry_id="entry",
        options=default_options_090(),
    )
    grouped = group_player_catalog(players)

    assert f"{GROUP_USER_PREFIX}Alex" in grouped
    assert grouped[GROUP_SHARED][0].users == ("Alex", "Sam")
    assert grouped[GROUP_TECHNICAL][0].client_class == CLIENT_CLASS_TECHNICAL
    assert grouped[GROUP_UNASSIGNED][0].client_class == CLIENT_CLASS_PLAYBACK
    assert grouped[GROUP_UNASSIGNED][0].classification_reason == "registry_backed_server_player"


def test_product_name_alone_never_classifies_technical_access() -> None:
    suspicious_name = record(
        record_id="1",
        reported_id="tool",
        app="Emby API Manager",
        name="Automation Tool",
    )

    classification, reason = classify_client([suspicious_name])

    assert classification == CLIENT_CLASS_UNKNOWN
    assert reason == "insufficient_evidence"


def test_explicit_api_metadata_classifies_technical_access() -> None:
    technical = record(
        record_id="1",
        reported_id="api",
        app="Client",
        client_type="integration",
        supports_playback=False,
    )

    classification, reason = classify_client([technical])

    assert classification == CLIENT_CLASS_TECHNICAL
    assert reason == "explicit_client_type"


def test_disabled_valid_entity_is_not_orphaned() -> None:
    item = record(
        record_id="1",
        reported_id="client",
        app="TV",
        supports_playback=True,
    )
    registry = entity(item.player_key, disabled=True)

    [player] = build_player_catalog(
        [item],
        registry_entries=[registry],
        states=States(),
        entry_id="entry",
        options=default_options_090(),
    )

    assert player.registry_enabled is False
    assert player.status == "disabled"
    assert player.orphan is False
    assert player.server_missing is False
    assert catalog_stats([player], server_history_records=1).disabled_valid == 1


def test_registry_player_without_current_server_record_uses_server_missing_semantics() -> None:
    registry = entity("client.tv", entity_id="media_player.old_tv")

    [player] = build_player_catalog(
        [],
        registry_entries=[registry],
        states=States(),
        entry_id="entry",
        options=default_options_090(),
    )

    assert player.server_missing is True
    assert player.status == "not_reported"
    assert player.orphan is False
    stats = catalog_stats([player], server_history_records=0)
    assert stats.server_missing == 1
    assert stats.orphans == 0


def test_playing_and_paused_are_both_protected_from_removal() -> None:
    playing_record = record(record_id="1", reported_id="one", app="TV", supports_playback=True)
    paused_record = record(record_id="2", reported_id="two", app="Mobile", supports_playback=True)
    first = entity(playing_record.player_key, entity_id="media_player.playing")
    second = entity(paused_record.player_key, entity_id="media_player.paused")

    players = build_player_catalog(
        [playing_record, paused_record],
        registry_entries=[first, second],
        states=States(
            {
                "media_player.playing": "playing",
                "media_player.paused": "paused",
            }
        ),
        entry_id="entry",
        options=default_options_090(),
    )

    by_id = {player.entity_id: player for player in players}
    assert by_id["media_player.playing"].playback == PLAYBACK_PLAYING
    assert by_id["media_player.playing"].removable is False
    assert by_id["media_player.paused"].playback == PLAYBACK_PAUSED
    assert by_id["media_player.paused"].removable is False


def test_selector_label_is_compact_and_details_are_separate() -> None:
    item = record(
        record_id="private-record",
        reported_id="private-reported-id",
        app="Emby TV",
        user="Alex",
        supports_playback=True,
    )
    registry = entity(
        item.player_key,
        entity_id="media_player.wohnzimmer_emby",
        name="Wohnzimmer Fernseher",
    )

    [player] = build_player_catalog(
        [item],
        registry_entries=[registry],
        states=States({registry.entity_id: "idle"}),
        entry_id="entry",
        options=default_options_090(),
    )

    assert player.selector_label == "Living room TV · Emby TV"
    assert "Wohnzimmer Fernseher" not in player.selector_label
    assert "media_player.wohnzimmer_emby" not in player.selector_label
    assert "Alex" not in player.selector_label
    assert "private-record" not in player.selector_label
    assert "private-reported-id" not in player.selector_label
    assert "Wohnzimmer Fernseher" in player.technical_details
    assert "media_player.wohnzimmer_emby" in player.technical_details
    assert filter_player_catalog([player], "wohnzimmer") == [player]
    assert filter_player_catalog([player], "media_player.wohnzimmer") == [player]
