from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .api import EmbyDeviceRecord
from .const import (
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_HIDDEN_WHOLE_DEVICES,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_USER_MASTER_VISIBILITY,
    DOMAIN,
)

CLIENT_CLASS_PLAYBACK = "playback"
CLIENT_CLASS_TECHNICAL = "technical"
CLIENT_CLASS_UNKNOWN = "unknown"

PLAYBACK_PLAYING = "playing"
PLAYBACK_PAUSED = "paused"
PLAYBACK_NON_PLAYING = "non_playing"
PLAYBACK_UNKNOWN = "unknown"
ACTIVE_PLAYBACK_STATES = {PLAYBACK_PLAYING, PLAYBACK_PAUSED}

GROUP_SHARED = "shared"
GROUP_UNASSIGNED = "unassigned"
GROUP_TECHNICAL = "technical"
GROUP_UNKNOWN = "unknown"
GROUP_USER_PREFIX = "user::"

_EXPLICIT_TECHNICAL_TYPES = {
    "api",
    "api_only",
    "automation",
    "integration",
    "service",
    "tool",
    "webhook",
}


@dataclass(frozen=True, slots=True)
class PlayerContext:
    """One logical EMBi player with user-facing and safety metadata."""

    player_key: str
    reported_device_id: str | None
    app_name: str
    device_name: str
    users: tuple[str, ...]
    latest_user: str | None
    last_activity: datetime | None
    client_class: str
    classification_reason: str
    entity_id: str | None
    ha_name: str
    registry_present: bool
    registry_enabled: bool
    registry_hidden: bool
    runtime_state: str | None
    playback: str
    emby_present: bool
    visible_in_embi: bool
    orphan: bool
    removable: bool
    protected_reason: str | None

    @property
    def group_key(self) -> str:
        if len(self.users) > 1:
            return GROUP_SHARED
        if len(self.users) == 1:
            return f"{GROUP_USER_PREFIX}{self.users[0]}"
        if self.client_class == CLIENT_CLASS_TECHNICAL:
            return GROUP_TECHNICAL
        if self.client_class == CLIENT_CLASS_UNKNOWN:
            return GROUP_UNKNOWN
        return GROUP_UNASSIGNED

    @property
    def status(self) -> str:
        if self.playback == PLAYBACK_PLAYING:
            return "playing"
        if self.playback == PLAYBACK_PAUSED:
            return "paused"
        if not self.registry_enabled and self.registry_present:
            return "disabled"
        if not self.visible_in_embi:
            return "hidden"
        if self.server_missing:
            return "not_reported"
        return "ready"

    @property
    def selector_label(self) -> str:
        """Return a compact mobile-safe selector label without internal identifiers."""
        return f"{self.device_name} · {self.app_name}"

    def compact_label(self, *, include_user: bool = False) -> str:
        """Return the normal selector label and add a user only for disambiguation."""
        label = self.selector_label
        if include_user and self.users:
            label = f"{label} · {self.users[0]}"
        return label

    @property
    def server_missing(self) -> bool:
        """Return whether HA still has the player but Emby no longer reports it."""
        return self.registry_present and not self.emby_present

    @property
    def technical_details(self) -> str:
        """Return technical context for a dedicated detail or preview page only."""
        details = [f"Home Assistant: {self.ha_name}"]
        if self.entity_id:
            details.append(self.entity_id)
        if self.users:
            details.append(f"Users: {', '.join(self.users)}")
        details.extend((f"Class: {self.client_class}", f"Status: {self.status}"))
        return " · ".join(details)

    @property
    def search_text(self) -> str:
        values = [
            self.app_name,
            self.device_name,
            self.ha_name,
            self.entity_id or "",
            *self.users,
        ]
        return " ".join(values).casefold()


@dataclass(frozen=True, slots=True)
class PlayerCatalogStats:
    server_history_records: int
    ha_players: int
    protected_playback: int
    removable_from_ha: int
    known_users: int
    technical_accesses: int
    unknown_clients: int
    disabled_valid: int
    server_missing: int
    orphans: int


def _entry_value(entry: Any, name: str, default: Any = None) -> Any:
    return getattr(entry, name, default)


def _state_value(states: Any, entity_id: str | None) -> str | None:
    if not entity_id or states is None:
        return None
    getter = getattr(states, "get", None)
    if getter is None:
        return None
    state = getter(entity_id)
    if state is None:
        return None
    return str(getattr(state, "state", state)).casefold()


def _pyemby_state(pyemby_devices: Mapping[str, Any] | None, player_key: str) -> str | None:
    if not pyemby_devices:
        return None
    device = pyemby_devices.get(player_key)
    if device is None:
        return None
    value = getattr(device, "state", None)
    return str(value).casefold() if value is not None else None


def _record_users(records: Iterable[EmbyDeviceRecord]) -> tuple[str, ...]:
    users: set[str] = set()
    for record in records:
        users.update(name for name in record.user_names if name)
        if record.last_user_name:
            users.add(record.last_user_name)
    return tuple(sorted(users, key=str.casefold))


def _latest_record(records: list[EmbyDeviceRecord]) -> EmbyDeviceRecord | None:
    if not records:
        return None
    return max(
        records,
        key=lambda record: (
            record.last_activity_datetime is not None,
            record.last_activity_datetime or datetime.min,
            record.name.casefold(),
        ),
    )


def classify_client(
    records: Iterable[EmbyDeviceRecord],
    *,
    runtime_state: str | None = None,
    registry_backed: bool = False,
) -> tuple[str, str]:
    """Classify from explicit capability/behavior metadata, never product names alone."""
    items = list(records)
    if runtime_state in ACTIVE_PLAYBACK_STATES:
        return CLIENT_CLASS_PLAYBACK, "observed_active_playback"
    if any(record.playback_observed or record.supports_playback is True for record in items):
        return CLIENT_CLASS_PLAYBACK, "explicit_or_observed_playback"
    if any(record.api_only is True for record in items):
        return CLIENT_CLASS_TECHNICAL, "explicit_api_only"
    if any(
        record.client_type and record.client_type.strip().casefold() in _EXPLICIT_TECHNICAL_TYPES
        for record in items
    ):
        return CLIENT_CLASS_TECHNICAL, "explicit_client_type"
    if registry_backed and items:
        return CLIENT_CLASS_PLAYBACK, "registry_backed_server_player"

    users = _record_users(items)
    repeated_explicit_non_playback = (
        len(items) >= 2
        and not users
        and all(record.supports_playback is False for record in items)
        and all(record.client_type for record in items)
    )
    if repeated_explicit_non_playback:
        return CLIENT_CLASS_TECHNICAL, "repeated_non_playback_api_behavior"
    return CLIENT_CLASS_UNKNOWN, "insufficient_evidence"


def _playback_state(
    *,
    runtime_state: str | None,
    pyemby_state: str | None,
    registry_present: bool,
    registry_enabled: bool,
    emby_present: bool,
) -> str:
    for value in (runtime_state, pyemby_state):
        if value == PLAYBACK_PLAYING:
            return PLAYBACK_PLAYING
        if value == PLAYBACK_PAUSED:
            return PLAYBACK_PAUSED
        if value in {"idle", "off", "standby", "unavailable"}:
            return PLAYBACK_NON_PLAYING
    if registry_present and not registry_enabled and emby_present:
        return PLAYBACK_NON_PLAYING
    if registry_present and not emby_present:
        return PLAYBACK_NON_PLAYING
    return PLAYBACK_UNKNOWN


def _is_visible(
    *,
    player_key: str,
    reported_device_id: str | None,
    users: tuple[str, ...],
    client_class: str,
    options: Mapping[str, Any],
) -> bool:
    hidden_exact = {str(value) for value in options.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
    hidden_devices = {str(value) for value in options.get(CONF_HIDDEN_WHOLE_DEVICES, [])}
    if player_key in hidden_exact:
        return False
    if reported_device_id and reported_device_id in hidden_devices:
        return False
    if len(users) == 1:
        user_visibility = options.get(CONF_USER_MASTER_VISIBILITY, {})
        if isinstance(user_visibility, Mapping) and user_visibility.get(users[0]) is False:
            return False
    return not (
        client_class == CLIENT_CLASS_TECHNICAL
        and not bool(options.get(CONF_TECHNICAL_ACCESS_VISIBILITY, False))
    )


def build_player_catalog(
    records: Iterable[EmbyDeviceRecord],
    *,
    registry_entries: Iterable[Any] = (),
    states: Any = None,
    entry_id: str,
    options: Mapping[str, Any],
    pyemby_devices: Mapping[str, Any] | None = None,
) -> list[PlayerContext]:
    """Build a current user-oriented catalog from fresh server and HA metadata."""
    grouped: dict[str, list[EmbyDeviceRecord]] = {}
    source_records = list(records)
    for record in source_records:
        grouped.setdefault(record.player_key, []).append(record)

    registry_by_key: dict[str, Any] = {}
    for entity in registry_entries:
        if (
            _entry_value(entity, "domain") == "media_player"
            and _entry_value(entity, "platform") == DOMAIN
            and _entry_value(entity, "config_entry_id") == entry_id
        ):
            registry_by_key[str(_entry_value(entity, "unique_id", ""))] = entity

    keys = set(grouped) | set(registry_by_key)
    contexts: list[PlayerContext] = []
    for key in sorted(keys, key=str.casefold):
        player_records = grouped.get(key, [])
        latest = _latest_record(player_records)
        entity = registry_by_key.get(key)
        entity_id = _entry_value(entity, "entity_id") if entity is not None else None
        runtime_state = _state_value(states, entity_id)
        py_state = _pyemby_state(pyemby_devices, key)
        effective_state = runtime_state or py_state
        client_class, class_reason = classify_client(
            player_records,
            runtime_state=effective_state,
            registry_backed=entity is not None,
        )
        users = _record_users(player_records)
        latest_user = latest.last_user_name if latest else None
        app_name = (latest.app_name if latest else None) or "Emby"
        device_name = (latest.name if latest else None) or "Home Assistant player"
        custom_name = _entry_value(entity, "name") if entity is not None else None
        original_name = _entry_value(entity, "original_name") if entity is not None else None
        ha_name = str(custom_name or original_name or device_name or app_name)
        registry_present = entity is not None
        registry_enabled = bool(entity is not None and _entry_value(entity, "disabled_by") is None)
        registry_hidden = bool(entity is not None and _entry_value(entity, "hidden_by") is not None)
        emby_present = bool(player_records)
        playback = _playback_state(
            runtime_state=runtime_state,
            pyemby_state=py_state,
            registry_present=registry_present,
            registry_enabled=registry_enabled,
            emby_present=emby_present,
        )
        visible = _is_visible(
            player_key=key,
            reported_device_id=latest.reported_device_id if latest else None,
            users=users,
            client_class=client_class,
            options=options,
        )
        owned = registry_present
        protected_reason: str | None = None
        if playback == PLAYBACK_PLAYING:
            protected_reason = "playing"
        elif playback == PLAYBACK_PAUSED:
            protected_reason = "paused"
        elif playback == PLAYBACK_UNKNOWN:
            protected_reason = "unknown_playback"
        elif not owned:
            protected_reason = "missing_registry_entity"
        removable = protected_reason is None
        contexts.append(
            PlayerContext(
                player_key=key,
                reported_device_id=latest.reported_device_id if latest else None,
                app_name=str(app_name),
                device_name=str(device_name),
                users=users,
                latest_user=latest_user,
                last_activity=latest.last_activity_datetime if latest else None,
                client_class=client_class,
                classification_reason=class_reason,
                entity_id=str(entity_id) if entity_id else None,
                ha_name=ha_name,
                registry_present=registry_present,
                registry_enabled=registry_enabled,
                registry_hidden=registry_hidden,
                runtime_state=runtime_state,
                playback=playback,
                emby_present=emby_present,
                visible_in_embi=visible,
                orphan=False,
                removable=removable,
                protected_reason=protected_reason,
            )
        )
    return contexts


def group_player_catalog(players: Iterable[PlayerContext]) -> dict[str, list[PlayerContext]]:
    """Group players by known user before shared, unassigned, technical and unknown."""
    grouped: dict[str, list[PlayerContext]] = {}
    for player in players:
        grouped.setdefault(player.group_key, []).append(player)
    for values in grouped.values():
        values.sort(
            key=lambda player: (
                player.playback not in ACTIVE_PLAYBACK_STATES,
                -(player.last_activity.timestamp() if player.last_activity else 0),
                player.selector_label.casefold(),
            )
        )
    return grouped


def filter_player_catalog(
    players: Iterable[PlayerContext], query: str | None
) -> list[PlayerContext]:
    """Search only the user-facing fields required by the contract."""
    normalized = str(query or "").strip().casefold()
    if not normalized:
        return list(players)
    return [player for player in players if normalized in player.search_text]


def catalog_stats(
    players: Iterable[PlayerContext], *, server_history_records: int
) -> PlayerCatalogStats:
    """Return independent server-history, HA, playback and removal counts."""
    items = list(players)
    users = {user for player in items for user in player.users}
    return PlayerCatalogStats(
        server_history_records=int(server_history_records),
        ha_players=sum(player.registry_present for player in items),
        protected_playback=sum(player.playback in ACTIVE_PLAYBACK_STATES for player in items),
        removable_from_ha=sum(player.removable for player in items),
        known_users=len(users),
        technical_accesses=sum(player.client_class == CLIENT_CLASS_TECHNICAL for player in items),
        unknown_clients=sum(player.client_class == CLIENT_CLASS_UNKNOWN for player in items),
        disabled_valid=sum(
            player.registry_present and not player.registry_enabled and player.emby_present
            for player in items
        ),
        server_missing=sum(player.server_missing for player in items),
        orphans=sum(player.orphan for player in items),
    )


def group_label(group_key: str) -> str:
    if group_key.startswith(GROUP_USER_PREFIX):
        return group_key.removeprefix(GROUP_USER_PREFIX)
    return group_key
