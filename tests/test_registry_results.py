from __future__ import annotations

from dataclasses import dataclass

from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.maintenance_registry_commit import apply_exact_registry_removals
from custom_components.emby.maintenance_registry_evaluate import evaluate_registry_targets
from custom_components.emby.models import PendingRegistryTarget


@dataclass
class FakeEntry:
    entry_id: str = "entry-target"


@dataclass
class FakeRegistryEntry:
    entity_id: str
    unique_id: str
    domain: str = "media_player"
    platform: str = "emby"
    config_entry_id: str | None = "entry-target"


class FakeRegistry:
    def __init__(self, entries=()) -> None:
        self.entities = {entry.entity_id: entry for entry in entries}
        self.removed: list[str] = []

    def async_get(self, entity_id: str):
        return self.entities.get(entity_id)

    def async_remove(self, entity_id: str) -> None:
        self.entities.pop(entity_id, None)
        self.removed.append(entity_id)


class FakeStates:
    def __init__(self, present=()) -> None:
        self.present = set(present)

    def get(self, entity_id: str):
        return object() if entity_id in self.present else None


def _device(player_key: str) -> EmbyDeviceRecord:
    reported_id, _, app = player_key.partition(".")
    return EmbyDeviceRecord.from_api(
        {
            "Id": f"history-{reported_id}",
            "ReportedDeviceId": reported_id,
            "AppName": app or None,
            "Name": "Synthetic device",
        }
    )


def test_five_queued_keys_without_registry_entities_are_missing_not_removed() -> None:
    targets = {
        f"client-{index}.App": PendingRegistryTarget(f"client-{index}.App", None)
        for index in range(5)
    }
    evaluation = evaluate_registry_targets(
        registry=FakeRegistry(),
        states=FakeStates(),
        entry=FakeEntry(),
        current_devices=[],
        targets=targets,
    )
    assert evaluation.result.queued == 5
    assert evaluation.result.matched == 0
    assert evaluation.result.removed == 0
    assert evaluation.result.missing == 5
    assert evaluation.entity_ids_to_remove == ()


def test_exact_match_is_proposed_but_not_counted_removed_before_commit() -> None:
    key = "client-1.Emby Windows"
    entity = FakeRegistryEntry("media_player.emby_test", key)
    evaluation = evaluate_registry_targets(
        registry=FakeRegistry([entity]),
        states=FakeStates(),
        entry=FakeEntry(),
        current_devices=[],
        targets={key: PendingRegistryTarget(key, entity.entity_id)},
    )
    assert evaluation.result.matched == 1
    assert evaluation.result.removed == 0
    assert evaluation.entity_ids_to_remove == (entity.entity_id,)


def test_active_state_and_remaining_history_protect_entities() -> None:
    active_key = "client-active.App"
    remaining_key = "client-remaining.App"
    active_entity = FakeRegistryEntry("media_player.active", active_key)
    remaining_entity = FakeRegistryEntry("media_player.remaining", remaining_key)
    evaluation = evaluate_registry_targets(
        registry=FakeRegistry([active_entity, remaining_entity]),
        states=FakeStates([active_entity.entity_id]),
        entry=FakeEntry(),
        current_devices=[_device(remaining_key)],
        targets={
            active_key: PendingRegistryTarget(active_key, active_entity.entity_id),
            remaining_key: PendingRegistryTarget(remaining_key, remaining_entity.entity_id),
        },
    )
    assert evaluation.result.matched == 1
    assert evaluation.result.state_still_present == 1
    assert evaluation.result.protected_remaining_history == 1
    assert evaluation.entity_ids_to_remove == ()


def test_wrong_entry_platform_unique_id_and_ambiguity_are_protected() -> None:
    wrong_entry = FakeRegistryEntry(
        "media_player.wrong_entry", "key-entry", config_entry_id="other-entry"
    )
    wrong_platform = FakeRegistryEntry(
        "sensor.wrong_platform", "key-platform", domain="sensor", platform="other"
    )
    wrong_unique = FakeRegistryEntry("media_player.wrong_unique", "changed-key")
    evaluation = evaluate_registry_targets(
        registry=FakeRegistry([wrong_entry, wrong_platform, wrong_unique]),
        states=FakeStates(),
        entry=FakeEntry(),
        current_devices=[],
        targets={
            "key-entry": PendingRegistryTarget("key-entry", wrong_entry.entity_id),
            "key-platform": PendingRegistryTarget("key-platform", wrong_platform.entity_id),
            "expected-key": PendingRegistryTarget("expected-key", wrong_unique.entity_id),
            "ambiguous-key": PendingRegistryTarget("ambiguous-key", None, ambiguous=True),
        },
    )
    assert evaluation.result.wrong_entry == 1
    assert evaluation.result.wrong_platform == 1
    assert evaluation.result.wrong_unique_id == 1
    assert evaluation.result.revalidation_ambiguous == 1
    assert evaluation.entity_ids_to_remove == ()


def test_no_prefix_or_substring_match_is_used() -> None:
    entity = FakeRegistryEntry("media_player.similar", "client-10.App")
    evaluation = evaluate_registry_targets(
        registry=FakeRegistry([entity]),
        states=FakeStates(),
        entry=FakeEntry(),
        current_devices=[],
        targets={"client-1": PendingRegistryTarget("client-1", None)},
    )
    assert evaluation.result.missing == 1
    assert evaluation.result.matched == 0


def test_actual_remove_count_changes_only_when_registry_commit_runs() -> None:
    entity = FakeRegistryEntry("media_player.remove_me", "client-remove.App")
    registry = FakeRegistry([entity])
    evaluation = evaluate_registry_targets(
        registry=registry,
        states=FakeStates(),
        entry=FakeEntry(),
        current_devices=[],
        targets={entity.unique_id: PendingRegistryTarget(entity.unique_id, entity.entity_id)},
    )
    assert evaluation.result.removed == 0
    removed = apply_exact_registry_removals(registry, evaluation.entity_ids_to_remove)
    assert removed == 1
    assert registry.removed == [entity.entity_id]
    assert registry.async_get(entity.entity_id) is None
