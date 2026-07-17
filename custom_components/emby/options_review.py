from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .const import (
    CONF_AUTO_SHOW_NEW_PLAYERS,
    CONF_GLOBAL_PLAYER_MODE,
    CONF_HIDDEN_EXACT_PLAYERS,
    CONF_HIDDEN_WHOLE_DEVICES,
    CONF_SERVER_AUTO_CLEANUP_AGE_DAYS,
    CONF_SERVER_AUTO_CLEANUP_ENABLED,
    CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES,
    CONF_SERVER_CLEANUP_AGE_DAYS,
    CONF_TECHNICAL_ACCESS_VISIBILITY,
    CONF_USER_MASTER_VISIBILITY,
)


@dataclass(frozen=True, slots=True)
class SemanticChange:
    key: str
    label: str
    before: str
    after: str

    def render(self) -> str:
        return f"{self.label}\n{self.before} → {self.after}"


def _on_off(value: Any, *, german: bool) -> str:
    if german:
        return "Ein" if bool(value) else "Aus"
    return "On" if bool(value) else "Off"


def _mode(value: Any, *, german: bool) -> str:
    active = str(value) == "active_only"
    if german:
        return "Nur während der Wiedergabe" if active else "Immer verfügbar"
    return "Only during playback" if active else "Always available"


def _days(value: Any, *, german: bool) -> str:
    suffix = "Tage" if german else "days"
    return f"{int(value)} {suffix}"


def semantic_changes(
    original: Mapping[str, Any],
    draft: Mapping[str, Any],
    *,
    player_labels: Mapping[str, str] | None = None,
    german: bool = False,
) -> list[SemanticChange]:
    """Return stable, user-facing before/after descriptions for the draft."""
    labels = {
        CONF_GLOBAL_PLAYER_MODE: (
            "Nur während der Wiedergabe anzeigen" if german else "Only show during playback"
        ),
        CONF_AUTO_SHOW_NEW_PLAYERS: (
            "Neue Player automatisch anzeigen" if german else "Automatically show new players"
        ),
        CONF_TECHNICAL_ACCESS_VISIBILITY: (
            "Technische Zugriffe als Player anzeigen"
            if german
            else "Show technical access as players"
        ),
        CONF_SERVER_AUTO_CLEANUP_ENABLED: (
            "Alte Emby-Einträge automatisch bereinigen"
            if german
            else "Automatically clean old Emby records"
        ),
        CONF_SERVER_AUTO_CLEANUP_AGE_DAYS: (
            "Altersgrenze der Automatik" if german else "Automatic cleanup age"
        ),
        CONF_SERVER_CLEANUP_AGE_DAYS: (
            "Altersgrenze der manuellen Prüfung" if german else "Manual cleanup age"
        ),
        CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES: (
            "Passende Home-Assistant-Player ebenfalls entfernen"
            if german
            else "Also remove matching Home Assistant players"
        ),
    }
    formatters = {
        CONF_GLOBAL_PLAYER_MODE: _mode,
        CONF_AUTO_SHOW_NEW_PLAYERS: _on_off,
        CONF_TECHNICAL_ACCESS_VISIBILITY: _on_off,
        CONF_SERVER_AUTO_CLEANUP_ENABLED: _on_off,
        CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES: _on_off,
        CONF_SERVER_AUTO_CLEANUP_AGE_DAYS: _days,
        CONF_SERVER_CLEANUP_AGE_DAYS: _days,
    }
    changes: list[SemanticChange] = []
    for key, label in labels.items():
        before = original.get(key)
        after = draft.get(key)
        if before == after:
            continue
        formatter = formatters[key]
        changes.append(
            SemanticChange(
                key,
                label,
                formatter(before, german=german),
                formatter(after, german=german),
            )
        )

    player_labels = player_labels or {}
    before_hidden = {str(value) for value in original.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
    after_hidden = {str(value) for value in draft.get(CONF_HIDDEN_EXACT_PLAYERS, [])}
    for key in sorted(before_hidden ^ after_hidden, key=str.casefold):
        label = player_labels.get(key, key)
        was_hidden = key in before_hidden
        is_hidden = key in after_hidden
        changes.append(
            SemanticChange(
                f"player:{key}",
                label,
                ("Ausgeblendet" if german else "Hidden")
                if was_hidden
                else ("In Home Assistant anzeigen" if german else "Show in Home Assistant"),
                ("Ausgeblendet" if german else "Hidden")
                if is_hidden
                else ("In Home Assistant anzeigen" if german else "Show in Home Assistant"),
            )
        )

    before_devices = {str(value) for value in original.get(CONF_HIDDEN_WHOLE_DEVICES, [])}
    after_devices = {str(value) for value in draft.get(CONF_HIDDEN_WHOLE_DEVICES, [])}
    if before_devices != after_devices:
        changes.append(
            SemanticChange(
                CONF_HIDDEN_WHOLE_DEVICES,
                "Geräteweite Regeln" if german else "Whole-device rules",
                str(len(before_devices)),
                str(len(after_devices)),
            )
        )

    before_users = original.get(CONF_USER_MASTER_VISIBILITY, {})
    after_users = draft.get(CONF_USER_MASTER_VISIBILITY, {})
    if isinstance(before_users, Mapping) and isinstance(after_users, Mapping):
        for user in sorted(set(before_users) | set(after_users), key=str.casefold):
            before = before_users.get(user, True)
            after = after_users.get(user, True)
            if before != after:
                changes.append(
                    SemanticChange(
                        f"user:{user}",
                        (
                            f"Alle Player von {user} anzeigen"
                            if german
                            else f"Show all players for {user}"
                        ),
                        _on_off(before, german=german),
                        _on_off(after, german=german),
                    )
                )
    return changes
