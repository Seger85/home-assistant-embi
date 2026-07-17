from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, *, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE | re.DOTALL)
    if count != 1:
        raise RuntimeError(f"{label}: expected one regex match, got {count}")
    return updated


# Version and non-persistent navigation constants.
path = "custom_components/emby/const.py"
text = read(path)
text = replace_once(text, 'VERSION = "0.9.1"', 'VERSION = "0.9.2"', label="runtime version")
text = replace_once(
    text,
    'CONF_BACK = "back"\n',
    '''CONF_BACK = "back"  # Legacy input name; never exposed or persisted by 0.9.2 forms.
CONF_FLOW_ACTION = "flow_action"
FLOW_ACTION_SAVE = "save"
FLOW_ACTION_BACK = "back"
FLOW_ACTION_OPEN_AUTOMATIC = "open_automatic_cleanup"
FLOW_ACTION_OPEN_HISTORY = "open_server_history_check"
FLOW_ACTION_OPEN_LAST_RUN = "open_last_cleanup_run"
FLOW_ACTION_APPLY = "apply_changes"
FLOW_ACTION_DISCARD = "discard_changes"
FLOW_ACTION_EXECUTE = "execute"
''',
    label="navigation constants",
)
write(path, text)

path = "custom_components/emby/manifest.json"
manifest = json.loads(read(path))
manifest["version"] = "0.9.2"
write(path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

# Shared native form-action navigation.
write(
    "custom_components/emby/options_navigation.py",
    '''from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from homeassistant.helpers import selector

from .const import CONF_FLOW_ACTION, FLOW_ACTION_BACK, FLOW_ACTION_SAVE


def action_selector(options: Iterable[Mapping[str, str]]) -> selector.SelectSelector:
    """Return a frontend-serializable native list selector for flow actions."""
    normalized = [
        {"value": str(option["value"]), "label": str(option["label"])}
        for option in options
    ]
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=normalized,
            multiple=False,
            mode=selector.SelectSelectorMode.LIST,
        )
    )


def navigation_selector(
    *,
    german: bool,
    primary_label: str | None = None,
    primary_value: str = FLOW_ACTION_SAVE,
) -> selector.SelectSelector:
    """Return a non-persistent form action with a true back choice."""
    options: list[dict[str, str]] = []
    if primary_label is not None:
        options.append({"value": primary_value, "label": primary_label})
    options.append(
        {
            "value": FLOW_ACTION_BACK,
            "label": "‹ Zurück" if german else "‹ Back",
        }
    )
    return action_selector(options)


def back_requested(user_input: Mapping[str, Any] | None) -> bool:
    """Return whether the submitted non-persistent action is Back."""
    return bool(user_input) and user_input.get(CONF_FLOW_ACTION) == FLOW_ACTION_BACK
''',
)

# Player options: fix None translation key, real back action, logging.
path = "custom_components/emby/options_devices.py"
text = read(path)
text = replace_once(
    text,
    "from typing import Any\n\nimport voluptuous as vol\n",
    "import logging\nfrom typing import Any\n\nimport voluptuous as vol\n",
    label="options_devices logging import",
)
text = text.replace("    CONF_BACK,\n", "")
text = replace_once(
    text,
    "    CONF_ENABLE_ENTITY_IDS,\n",
    "    CONF_ENABLE_ENTITY_IDS,\n    CONF_FLOW_ACTION,\n",
    label="options_devices flow action import",
)
text = replace_once(
    text,
    "from .options_runtime import (\n",
    "from .options_navigation import back_requested, navigation_selector\nfrom .options_runtime import (\n",
    label="options_devices navigation import",
)
text = replace_once(
    text,
    "_OLDER_RULES_GROUP = \"older_rules\"\n",
    '_LOGGER = logging.getLogger(__name__)\n\n_OLDER_RULES_GROUP = "older_rules"\n',
    label="options_devices logger",
)
text = regex_once(
    text,
    r"def _single\(\n    options: list\[dict\[str, str\]\], \*, translation_key: str \| None = None\n\) -> selector\.SelectSelector:\n    return selector\.SelectSelector\(\n        selector\.SelectSelectorConfig\(\n            options=options,\n            multiple=False,\n            translation_key=translation_key,\n            mode=selector\.SelectSelectorMode\.DROPDOWN,\n        \)\n    \)\n",
    '''def _single(
    options: list[dict[str, str]], *, translation_key: str | None = None
) -> selector.SelectSelector:
    config: dict[str, Any] = {
        "options": options,
        "multiple": False,
        "mode": selector.SelectSelectorMode.DROPDOWN,
    }
    if translation_key is not None:
        config["translation_key"] = translation_key
    return selector.SelectSelector(selector.SelectSelectorConfig(**config))
''',
    label="frontend-safe single selector",
)
text = text.replace(
    "        except Exception:\n            players = []\n",
    '        except Exception:\n            _LOGGER.exception("Failed to load current EMBi player catalog")\n            players = []\n',
)
back_field = (
    '        fields[vol.Required(CONF_FLOW_ACTION, default="save")] = navigation_selector(\n'
    "            german=self._is_de(),\n"
    '            primary_label="Übernehmen" if self._is_de() else "Apply",\n'
    "        )"
)
text = text.replace(
    "        fields[vol.Optional(CONF_BACK, default=False)] = selector.BooleanSelector()",
    back_field,
)
text = text.replace("if user_input.get(CONF_BACK):", "if back_requested(user_input):")
write(path, text)

# Home Assistant player removal/restoration navigation and logging.
path = "custom_components/emby/options_ha_cleanup.py"
text = read(path)
text = replace_once(
    text,
    "from typing import Any\n\nimport voluptuous as vol\n",
    "import logging\nfrom typing import Any\n\nimport voluptuous as vol\n",
    label="ha cleanup logging import",
)
text = text.replace("    CONF_BACK,\n", "")
text = replace_once(
    text,
    "    CONF_HIDDEN_EXACT_PLAYERS,\n",
    "    CONF_FLOW_ACTION,\n    CONF_HIDDEN_EXACT_PLAYERS,\n    FLOW_ACTION_BACK,\n    FLOW_ACTION_EXECUTE,\n",
    label="ha cleanup action imports",
)
text = replace_once(
    text,
    "from .options_runtime import entity_options, fresh_catalog, page_slice, player_options\n",
    "from .options_navigation import action_selector, back_requested, navigation_selector\nfrom .options_runtime import entity_options, fresh_catalog, page_slice, player_options\n",
    label="ha cleanup navigation import",
)
text = replace_once(
    text,
    "from .player_actions import async_remove_ha_players, async_restore_players\n\n\n",
    'from .player_actions import async_remove_ha_players, async_restore_players\n\n\n_LOGGER = logging.getLogger(__name__)\n\n\n',
    label="ha cleanup logger",
)
text = text.replace(
    "        except Exception:\n            players = []\n",
    '        except Exception:\n            _LOGGER.exception("Failed to load current EMBi player catalog")\n            players = []\n',
)
text = text.replace(
    "        fields[vol.Optional(CONF_BACK, default=False)] = selector.BooleanSelector()",
    '''        fields[vol.Required(CONF_FLOW_ACTION, default="save")] = navigation_selector(
            german=self._is_de(),
            primary_label="Weiter" if self._is_de() else "Continue",
        )''',
)
text = text.replace("if user_input.get(CONF_BACK):", "if back_requested(user_input):")
text = regex_once(
    text,
    r"    async def async_step_confirm_ha_removal\(self, user_input: dict\[str, Any\] \| None = None\):\n.*?\n    async def async_step_back_to_manage_ha_players",
    '''    async def async_step_confirm_ha_removal(self, user_input: dict[str, Any] | None = None):
        if not self._pending_ha_entity_ids:
            return await self.async_step_manage_ha_players()
        if user_input is not None:
            action = user_input.get(CONF_FLOW_ACTION)
            if action == FLOW_ACTION_BACK:
                return await self.async_step_back_to_manage_ha_players()
            if action == FLOW_ACTION_EXECUTE:
                return await self.async_step_execute_ha_removal()
        return self.async_show_form(
            step_id="confirm_ha_removal",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FLOW_ACTION): action_selector(
                        [
                            {
                                "value": FLOW_ACTION_EXECUTE,
                                "label": (
                                    f"{len(self._pending_ha_entity_ids)} HA-Player entfernen"
                                    if self._is_de()
                                    else f"Remove {len(self._pending_ha_entity_ids)} HA players"
                                ),
                            },
                            {
                                "value": FLOW_ACTION_BACK,
                                "label": "‹ Zurück" if self._is_de() else "‹ Back",
                            },
                        ]
                    )
                }
            ),
            description_placeholders={"count": str(len(self._pending_ha_entity_ids))},
        )

    async def async_step_back_to_manage_ha_players''',
    label="HA removal confirmation form",
)
write(path, text)

# Mobile-safe server labels, localized confirmation detail.
path = "custom_components/emby/helpers.py"
text = read(path)
text = replace_once(
    text,
    "from collections.abc import Iterable\n",
    "from collections import Counter\nfrom collections.abc import Iterable\nfrom zoneinfo import ZoneInfo, ZoneInfoNotFoundError\n",
    label="helper display imports",
)
text = regex_once(
    text,
    r"def server_device_selector_options\(\n    devices: Iterable\[EmbyDeviceRecord\],\n\) -> dict\[str, str\]:\n    \"\"\"Return destructive-cleanup options keyed by server record ID\.\"\"\"\n    return \{device\.record_id: device\.server_cleanup_label for device in devices\}\n",
    '''def _display_zone(time_zone: str) -> ZoneInfo:
    try:
        return ZoneInfo(time_zone)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _server_record_base_label(
    device: EmbyDeviceRecord,
    *,
    time_zone: str,
    german: bool,
) -> str:
    app = device.app_name or ("Unbekannte App" if german else "Unknown app")
    user = device.last_user_name or ("Ohne Benutzer" if german else "No user")
    activity = device.last_activity_datetime
    if activity is None:
        date_label = "unbekannt" if german else "unknown"
    else:
        local = activity.astimezone(_display_zone(time_zone))
        date_label = local.strftime("%d.%m.%Y" if german else "%Y-%m-%d")
    last_label = f"zuletzt {date_label}" if german else f"last active {date_label}"
    return f"{device.name} · {app} · {user} · {last_label}"


def server_device_selector_options(
    devices: Iterable[EmbyDeviceRecord],
    *,
    time_zone: str,
    german: bool,
) -> dict[str, str]:
    """Return stable mobile-safe options without versions, UTC or internal IDs."""
    records = list(devices)
    base_by_id = {
        device.record_id: _server_record_base_label(
            device,
            time_zone=time_zone,
            german=german,
        )
        for device in records
    }
    counts = Counter(base_by_id.values())
    ordinals: Counter[str] = Counter()
    options: dict[str, str] = {}
    for device in sorted(
        records,
        key=lambda item: (base_by_id[item.record_id].casefold(), item.record_id),
    ):
        base = base_by_id[device.record_id]
        ordinals[base] += 1
        label = base
        if counts[base] > 1:
            suffix = (
                f"Eintrag {ordinals[base]}/{counts[base]}"
                if german
                else f"record {ordinals[base]}/{counts[base]}"
            )
            label = f"{base} · {suffix}"
        options[device.record_id] = label
    return options


def server_device_confirmation_details(
    devices: Iterable[EmbyDeviceRecord],
    *,
    time_zone: str,
    german: bool,
) -> str:
    """Render full selected-record details only on the confirmation page."""
    zone = _display_zone(time_zone)
    lines: list[str] = []
    for device in sorted(devices, key=lambda item: (item.name.casefold(), item.record_id)):
        app = device.app_name or ("Unbekannte App" if german else "Unknown app")
        if device.app_version:
            app = f"{app} {device.app_version}"
        user = device.last_user_name or ("Ohne Benutzer" if german else "No user")
        activity = device.last_activity_datetime
        timestamp = (
            activity.astimezone(zone).strftime("%d.%m.%Y %H:%M:%S %Z")
            if activity is not None
            else ("Unbekannt" if german else "Unknown")
        )
        lines.append(
            " · ".join(
                (
                    device.name,
                    app,
                    user,
                    timestamp,
                    f"Record {device.short_record_id}",
                )
            )
        )
    return "\n".join(lines) or "-"
''',
    label="mobile cleanup labels",
)
write(path, text)

# Server cleanup forms/report and localized time handling.
path = "custom_components/emby/options_cleanup.py"
text = read(path)
text = replace_once(
    text,
    "from typing import Any\n\nimport voluptuous as vol\n",
    "import logging\nfrom datetime import datetime\nfrom typing import Any\nfrom zoneinfo import ZoneInfo, ZoneInfoNotFoundError\n\nimport voluptuous as vol\n",
    label="cleanup imports",
)
text = text.replace("    CONF_BACK,\n", "")
text = replace_once(
    text,
    "    CONF_DELETE_DEVICE_RECORD_IDS,\n",
    '''    CONF_DELETE_DEVICE_RECORD_IDS,
    CONF_FLOW_ACTION,
    FLOW_ACTION_BACK,
    FLOW_ACTION_EXECUTE,
    FLOW_ACTION_OPEN_AUTOMATIC,
    FLOW_ACTION_OPEN_HISTORY,
    FLOW_ACTION_OPEN_LAST_RUN,
''',
    label="cleanup action constants",
)
text = replace_once(
    text,
    "from .helpers import age_days_from_input, age_preset_for_days, server_device_selector_options\n",
    '''from .helpers import (
    age_days_from_input,
    age_preset_for_days,
    server_device_confirmation_details,
    server_device_selector_options,
)
''',
    label="cleanup helper imports",
)
text = replace_once(
    text,
    "from .options_runtime import status_label\n\n",
    "from .options_navigation import action_selector, back_requested, navigation_selector\n\n",
    label="cleanup navigation import",
)
text = replace_once(
    text,
    '_AUTO_CUSTOM = "automatic_custom_age_days"\n\n\n',
    '_AUTO_CUSTOM = "automatic_custom_age_days"\n\n_LOGGER = logging.getLogger(__name__)\n\n\n',
    label="cleanup logger",
)
text = regex_once(
    text,
    r"class CleanupOptionsMixin:\n    \"\"\"Separated Emby-server cleanup settings, preview and status pages\.\"\"\"\n\n    async def async_step_server_cleanup\(self, user_input: dict\[str, Any\] \| None = None\):\n.*?\n    async def async_step_back_to_server_cleanup",
    '''class CleanupOptionsMixin:
    """Separated Emby-server cleanup settings, preview and status pages."""

    async def async_step_server_cleanup(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            action = user_input.get(CONF_FLOW_ACTION)
            if action == FLOW_ACTION_OPEN_AUTOMATIC:
                return await self.async_step_automatic_cleanup()
            if action == FLOW_ACTION_OPEN_HISTORY:
                return await self.async_step_server_history_check()
            if action == FLOW_ACTION_OPEN_LAST_RUN:
                return await self.async_step_last_cleanup_run()
            if action == FLOW_ACTION_BACK:
                return await self.async_step_init()
        return self.async_show_form(
            step_id="server_cleanup",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FLOW_ACTION): action_selector(
                        [
                            {
                                "value": FLOW_ACTION_OPEN_AUTOMATIC,
                                "label": (
                                    "Automatische Bereinigung"
                                    if self._is_de()
                                    else "Automatic cleanup"
                                ),
                            },
                            {
                                "value": FLOW_ACTION_OPEN_HISTORY,
                                "label": (
                                    "Jetzt auf alte Einträge prüfen"
                                    if self._is_de()
                                    else "Check for old records now"
                                ),
                            },
                            {
                                "value": FLOW_ACTION_OPEN_LAST_RUN,
                                "label": (
                                    "Letzter Bereinigungslauf"
                                    if self._is_de()
                                    else "Last cleanup run"
                                ),
                            },
                            {
                                "value": FLOW_ACTION_BACK,
                                "label": "‹ Zurück" if self._is_de() else "‹ Back",
                            },
                        ]
                    )
                }
            ),
        )

    async def async_step_back_to_server_cleanup''',
    label="server cleanup form navigation",
)
text = text.replace(
    "        fields[vol.Optional(CONF_BACK, default=False)] = selector.BooleanSelector()",
    '''        fields[vol.Required(CONF_FLOW_ACTION, default="save")] = navigation_selector(
            german=self._is_de(),
            primary_label="Übernehmen" if self._is_de() else "Apply",
        )''',
)
text = text.replace("user_input.get(CONF_BACK)", "back_requested(user_input)")
text = text.replace(
    "            devices = []\n            errors[\"base\"] = \"cannot_connect\"\n",
    '            _LOGGER.exception("Failed to load Emby server-history records")\n            devices = []\n            errors["base"] = "cannot_connect"\n',
)
text = replace_once(
    text,
    "                    for key, label in server_device_selector_options(plan.candidates).items()\n",
    '''                    for key, label in server_device_selector_options(
                        plan.candidates,
                        time_zone=self.hass.config.time_zone,
                        german=self._is_de(),
                    ).items()
''',
    label="localized cleanup selector",
)
text = regex_once(
    text,
    r"    async def async_step_confirm_server_deletion\(self, user_input: dict\[str, Any\] \| None = None\):\n.*?\n    async def async_step_back_to_server_history_check",
    '''    async def async_step_confirm_server_deletion(
        self, user_input: dict[str, Any] | None = None
    ):
        if not self._pending_cleanup_records:
            return await self.async_step_server_history_check()
        if user_input is not None:
            action = user_input.get(CONF_FLOW_ACTION)
            if action == FLOW_ACTION_BACK:
                return await self.async_step_back_to_server_history_check()
            if action == FLOW_ACTION_EXECUTE:
                return await self.async_step_execute_server_deletion()
        count = len(self._pending_cleanup_records)
        return self.async_show_form(
            step_id="confirm_server_deletion",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FLOW_ACTION): action_selector(
                        [
                            {
                                "value": FLOW_ACTION_EXECUTE,
                                "label": (
                                    f"{count} Emby-Einträge löschen"
                                    if self._is_de()
                                    else f"Delete {count} Emby records"
                                ),
                            },
                            {
                                "value": FLOW_ACTION_BACK,
                                "label": "‹ Zurück" if self._is_de() else "‹ Back",
                            },
                        ]
                    )
                }
            ),
            description_placeholders={
                "count": str(count),
                "details": server_device_confirmation_details(
                    self._pending_cleanup_records.values(),
                    time_zone=self.hass.config.time_zone,
                    german=self._is_de(),
                ),
            },
        )

    async def async_step_back_to_server_history_check''',
    label="server delete confirmation form",
)
text = regex_once(
    text,
    r"    async def async_step_last_cleanup_run\(self, user_input: dict\[str, Any\] \| None = None\):\n.*\Z",
    '''    def _format_report_time(self, value: str | None, *, empty: str) -> str:
        if not value:
            return empty
        try:
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            try:
                zone = ZoneInfo(self.hass.config.time_zone)
            except ZoneInfoNotFoundError:
                zone = ZoneInfo("UTC")
            local = parsed.astimezone(zone)
        except (TypeError, ValueError):
            _LOGGER.warning("Invalid persisted EMBi maintenance timestamp: %r", value)
            return "Unbekannt" if self._is_de() else "Unknown"
        return local.strftime("%d.%m.%Y %H:%M" if self._is_de() else "%Y-%m-%d %H:%M")

    async def async_step_last_cleanup_run(self, user_input: dict[str, Any] | None = None):
        if back_requested(user_input):
            return await self.async_step_server_cleanup()
        report = self._runtime.maintenance_state.report
        never = "Noch nicht ausgeführt" if self._is_de() else "Not run yet"
        no_schedule = "Kein Lauf geplant" if self._is_de() else "No run scheduled"
        mode = {
            "manual": "Manuell" if self._is_de() else "Manual",
            "automatic": "Automatisch" if self._is_de() else "Automatic",
        }.get(report.mode, never)
        age = (
            f"{report.age_threshold_days} Tage"
            if self._is_de() and report.age_threshold_days is not None
            else (
                f"{report.age_threshold_days} days"
                if report.age_threshold_days is not None
                else "-"
            )
        )
        return self.async_show_form(
            step_id="last_cleanup_run",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FLOW_ACTION, default=FLOW_ACTION_BACK): navigation_selector(
                        german=self._is_de()
                    )
                }
            ),
            description_placeholders={
                "run_at": self._format_report_time(
                    report.completed_at or report.started_at,
                    empty=never,
                ),
                "mode": mode,
                "age": age,
                "deleted": str(report.server_deleted),
                "protected": str(
                    report.skipped_active + report.registry_entities_protected
                ),
                "failed": str(report.server_failed),
                "next_run": self._format_report_time(
                    report.next_run_at,
                    empty=no_schedule,
                ),
            },
        )
''',
    label="last cleanup report form",
)
write(path, text)

# Options root/review: no back menu row, logged failures.
path = "custom_components/emby/options_flow.py"
text = read(path)
text = replace_once(
    text,
    "from copy import deepcopy\nfrom typing import Any\n\nfrom homeassistant import config_entries\n",
    "from copy import deepcopy\nimport logging\nfrom typing import Any\n\nimport voluptuous as vol\nfrom homeassistant import config_entries\n",
    label="options flow imports",
)
text = replace_once(
    text,
    "    CONF_HIDDEN_EXACT_PLAYERS,\n",
    '''    CONF_FLOW_ACTION,
    CONF_HIDDEN_EXACT_PLAYERS,
    FLOW_ACTION_APPLY,
    FLOW_ACTION_BACK,
    FLOW_ACTION_DISCARD,
''',
    label="options flow action constants",
)
text = replace_once(
    text,
    "from .options_model import migrate_options_090\n",
    "from .options_model import migrate_options_090\nfrom .options_navigation import action_selector\n",
    label="options flow navigation import",
)
text = replace_once(
    text,
    "_ERROR_TEXT_DE = {\n",
    "_LOGGER = logging.getLogger(__name__)\n\n_ERROR_TEXT_DE = {\n",
    label="options flow logger",
)
text = text.replace("EMBi 0.9.1 Options Flow", "EMBi 0.9.2 Options Flow")
text = text.replace(
    "        except Exception:\n            labels = {}\n",
    '        except Exception:\n            _LOGGER.exception("Failed to build EMBi option-review labels")\n            labels = {}\n',
)
text = text.replace(
    "        except Exception:\n            stats = None\n",
    '        except Exception:\n            _LOGGER.exception("Failed to build EMBi root-menu statistics")\n            stats = None\n',
)
text = text.replace(
    "        except Exception:\n            self._review_error = \"cannot_connect\"\n",
    '        except Exception:\n            _LOGGER.exception("Failed to refresh EMBi players before applying options")\n            self._review_error = "cannot_connect"\n',
)
text = text.replace(
    "        except Exception:\n            self._review_error = \"save_failed\"\n",
    '        except Exception:\n            _LOGGER.exception("Failed to store EMBi options")\n            self._review_error = "save_failed"\n',
)
text = regex_once(
    text,
    r"    async def async_step_review_changes\(self, user_input: dict\[str, Any\] \| None = None\):\n.*?\n    async def async_step_discard_changes",
    '''    async def async_step_review_changes(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            action = user_input.get(CONF_FLOW_ACTION)
            if action == FLOW_ACTION_APPLY:
                return await self.async_step_apply_changes()
            if action == FLOW_ACTION_DISCARD:
                return await self.async_step_discard_changes()
            if action == FLOW_ACTION_BACK:
                return await self.async_step_init()
        if not self._dirty:
            self._review_error = "no_changes"
        lines, count = await self._review_lines()
        return self.async_show_form(
            step_id="review_changes",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FLOW_ACTION): action_selector(
                        [
                            {
                                "value": FLOW_ACTION_APPLY,
                                "label": (
                                    "Änderungen übernehmen"
                                    if self._is_de()
                                    else "Apply changes"
                                ),
                            },
                            {
                                "value": FLOW_ACTION_DISCARD,
                                "label": (
                                    "Änderungen verwerfen"
                                    if self._is_de()
                                    else "Discard changes"
                                ),
                            },
                            {
                                "value": FLOW_ACTION_BACK,
                                "label": "‹ Zurück" if self._is_de() else "‹ Back",
                            },
                        ]
                    )
                }
            ),
            description_placeholders={
                "count": str(count),
                "count_text": self._change_count_text(count),
                "changes": "\n\n".join(lines) or "-",
                "error": self._error_text(self._review_error),
            },
        )

    async def async_step_discard_changes''',
    label="review changes form",
)
write(path, text)

# Technical client classification and playback-state resolution.
path = "custom_components/emby/player_context.py"
text = read(path)
text = replace_once(
    text,
    "_EXPLICIT_TECHNICAL_TYPES = {\n",
    '''_EXPLICIT_TECHNICAL_APPS = {
    "embi",
    "home assistant",
    "home-assistant",
    "homarr",
    "homarr dashboard",
    "windmill",
}
_EXPLICIT_TECHNICAL_CAPABILITIES = {
    "api",
    "api_only",
    "automation",
    "dashboard",
    "integration",
    "service",
    "webhook",
}
_EXPLICIT_TECHNICAL_TYPES = {
''',
    label="technical classification metadata",
)
text = regex_once(
    text,
    r"def classify_client\(\n    records: Iterable\[EmbyDeviceRecord\],\n    \*,\n    runtime_state: str \| None = None,\n    registry_backed: bool = False,\n\) -> tuple\[str, str\]:\n.*?\n\ndef _playback_state",
    '''def _technical_app_metadata(records: Iterable[EmbyDeviceRecord]) -> bool:
    for record in records:
        app = str(record.app_name or "").strip().casefold()
        if app in _EXPLICIT_TECHNICAL_APPS:
            return True
        if any(app.startswith(f"{name} ") for name in _EXPLICIT_TECHNICAL_APPS):
            return True
    return False


def classify_client(
    records: Iterable[EmbyDeviceRecord],
    *,
    runtime_state: str | None = None,
    registry_backed: bool = False,
) -> tuple[str, str]:
    """Classify from capability, behavior, app and registry/session evidence."""
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
    if any(_EXPLICIT_TECHNICAL_CAPABILITIES & set(record.capabilities) for record in items):
        return CLIENT_CLASS_TECHNICAL, "explicit_technical_capability"

    users = _record_users(items)
    no_playback_evidence = not any(
        record.playback_observed or record.supports_playback is True for record in items
    )
    if items and not users and no_playback_evidence and _technical_app_metadata(items):
        return CLIENT_CLASS_TECHNICAL, "technical_app_without_playback"

    repeated_explicit_non_playback = (
        len(items) >= 2
        and not users
        and all(record.supports_playback is False for record in items)
        and all(record.client_type for record in items)
    )
    if repeated_explicit_non_playback:
        return CLIENT_CLASS_TECHNICAL, "repeated_non_playback_api_behavior"
    if registry_backed and items:
        return CLIENT_CLASS_PLAYBACK, "registry_backed_server_player"
    return CLIENT_CLASS_UNKNOWN, "insufficient_evidence"


def _playback_state''',
    label="technical client classifier",
)
text = replace_once(
    text,
    "    emby_present: bool,\n) -> str:\n",
    "    emby_present: bool,\n    client_class: str,\n) -> str:\n",
    label="playback state signature",
)
text = replace_once(
    text,
    '        if value in {"idle", "off", "standby", "unavailable"}:\n            return PLAYBACK_NON_PLAYING\n',
    '''        if value in {"idle", "off", "standby", "unavailable"}:
            return PLAYBACK_NON_PLAYING
    if client_class == CLIENT_CLASS_TECHNICAL:
        return PLAYBACK_NON_PLAYING
''',
    label="technical non-playing state",
)
text = replace_once(
    text,
    "            emby_present=emby_present,\n        )\n",
    "            emby_present=emby_present,\n            client_class=client_class,\n        )\n",
    label="playback state call",
)
write(path, text)

# Translations: form actions, compact labels, report fields.
def update_translation(path: str, *, german: bool) -> None:
    data = json.loads(read(path))
    steps = data["options"]["step"]
    action_label = "Aktion" if german else "Action"

    for name in (
        "ha_players",
        "player_group",
        "player_exceptions",
        "player_details",
        "older_rules",
        "automatic_cleanup",
        "server_history_check",
        "manage_ha_players",
        "restore_ha_players",
    ):
        step_data = steps[name].setdefault("data", {})
        step_data.pop("back", None)
        step_data["flow_action"] = action_label

    for name in (
        "server_cleanup",
        "confirm_server_deletion",
        "last_cleanup_run",
        "confirm_ha_removal",
        "review_changes",
    ):
        steps[name].pop("menu_options", None)
        steps[name]["data"] = {"flow_action": action_label}

    steps["automatic_cleanup"]["data"][
        "server_auto_cleanup_remove_ha_entities"
    ] = (
        "Passende Home-Assistant-Player ebenfalls entfernen"
        if german
        else "Also remove matching Home Assistant players"
    )
    steps["automatic_cleanup"].setdefault("data_description", {})[
        "server_auto_cleanup_remove_ha_entities"
    ] = (
        "Nur nach erfolgreicher Serverlöschung und erneuter Prüfung von Identität, "
        "Config Entry, Plattform, Unique-ID, verbleibender Historie und Wiedergabestatus "
        "wird ein exakt passender Home-Assistant-Player entfernt."
        if german
        else "A matching Home Assistant player is removed only after successful server "
        "deletion and fresh identity, config-entry, platform, unique-ID, remaining-history "
        "and playback validation."
    )
    steps["server_history_check"]["data"]["delete_device_record_ids"] = (
        "Auswählbare Emby-Einträge" if german else "Selectable Emby records"
    )
    steps["confirm_server_deletion"]["description"] = (
        "Unmittelbar vor der Ausführung werden die Kandidaten erneut geladen und validiert. "
        "Benutzer, Medien, Bibliotheken und Wiedergabeverlauf werden nicht gelöscht.\n\n{details}"
        if german
        else "Candidates are refreshed and validated again immediately before execution. "
        "Users, media, libraries and playback history are not deleted.\n\n{details}"
    )
    steps["last_cleanup_run"]["description"] = (
        "Zeitpunkt: {run_at}\nModus: {mode}\nAltersgrenze: {age}\n"
        "Gelöscht: {deleted}\nGeschützt: {protected}\nFehlgeschlagen: {failed}\n"
        "Nächster Lauf: {next_run}"
        if german
        else "Time: {run_at}\nMode: {mode}\nAge limit: {age}\n"
        "Deleted: {deleted}\nProtected: {protected}\nFailed: {failed}\n"
        "Next run: {next_run}"
    )

    write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


update_translation("custom_components/emby/translations/de.json", german=True)
update_translation("custom_components/emby/translations/en.json", german=False)
write("custom_components/emby/strings.json", read("custom_components/emby/translations/en.json"))

# Tests: realistic flow serialization, navigation, labels and classification.
path = "tests/test_options_flow.py"
text = read(path)
text = replace_once(
    text,
    'self.config = SimpleNamespace(language="de")',
    'self.config = SimpleNamespace(language="de", time_zone="Europe/Berlin")',
    label="fake HA timezone",
)
append = r'''


def _realistic_player_fixture():
    from custom_components.emby.player_context import build_player_catalog, catalog_stats

    records: list[EmbyDeviceRecord] = []
    registry_entries = []
    apps = ["Emby TV", "Emby for iOS", "Emby Web", "Emby for Android"]
    for index in range(69):
        player_index = index % 31
        app = apps[player_index % len(apps)]
        data = {
            "Id": f"history-{index:02d}",
            "ReportedDeviceId": f"device-{player_index:02d}",
            "Name": f"Room {player_index:02d}",
            "AppName": app,
            "LastUserName": f"User {player_index % 8}",
            "DateLastActivity": f"2026-07-{(index % 15) + 1:02d}T12:00:00Z",
            "SupportsPlayback": True,
        }
        records.append(EmbyDeviceRecord.from_api(data))
    for player_index in range(31):
        app = apps[player_index % len(apps)]
        key = f"device-{player_index:02d}.{app}"
        registry_entries.append(
            SimpleNamespace(
                domain="media_player",
                platform="emby",
                config_entry_id="entry",
                unique_id=key,
                entity_id=f"media_player.emby_{player_index:02d}",
                name=f"HA Player {player_index:02d}",
                original_name=f"Emby {player_index:02d}",
                disabled_by=None,
                hidden_by=None,
            )
        )

    class FixtureStates:
        def get(self, entity_id):
            return SimpleNamespace(state="idle") if entity_id else None

    players = build_player_catalog(
        records,
        registry_entries=registry_entries,
        states=FixtureStates(),
        entry_id="entry",
        options=default_options_090(),
    )
    return records, players, catalog_stats(players, server_history_records=len(records))


def _assert_form_serializable(result) -> None:
    import json

    assert result["type"] == "form"
    serialized = []
    for validator in result["data_schema"].schema.values():
        serializer = getattr(validator, "serialize", None)
        if serializer is not None:
            serialized.append(serializer())
    json.dumps(serialized)


@pytest.mark.asyncio
async def test_realistic_root_player_form_is_frontend_serializable(monkeypatch) -> None:
    records, players, fixture_stats = _realistic_player_fixture()

    async def catalog(_flow):
        return players, fixture_stats

    monkeypatch.setattr("custom_components.emby.options_flow.fresh_catalog", catalog)
    monkeypatch.setattr("custom_components.emby.options_devices.fresh_catalog", catalog)
    monkeypatch.setattr("custom_components.emby.options_ha_cleanup.fresh_catalog", catalog)
    flow, _entry, _store, _hass = setup_flow()
    flow._runtime.api_client = FakeApi(records)

    result = await flow.async_step_ha_players()
    assert result["step_id"] == "ha_players"
    assert result["errors"] == {}
    _assert_form_serializable(result)


@pytest.mark.asyncio
async def test_reachable_forms_serialize_and_never_expose_legacy_back_toggle(monkeypatch) -> None:
    from custom_components.emby.const import CONF_BACK
    from custom_components.emby.player_context import group_player_catalog

    records, players, fixture_stats = _realistic_player_fixture()

    async def catalog(_flow):
        return players, fixture_stats

    monkeypatch.setattr("custom_components.emby.options_flow.fresh_catalog", catalog)
    monkeypatch.setattr("custom_components.emby.options_devices.fresh_catalog", catalog)
    monkeypatch.setattr("custom_components.emby.options_ha_cleanup.fresh_catalog", catalog)
    flow, _entry, _store, _hass = setup_flow()
    flow._runtime.api_client = FakeApi(records)
    flow._selected_group = next(iter(group_player_catalog(players)))

    results = [
        await flow.async_step_ha_players(),
        await flow.async_step_player_group(),
        await flow.async_step_player_exceptions(),
        await flow.async_step_player_details(),
        await flow.async_step_server_cleanup(),
        await flow.async_step_automatic_cleanup(),
        await flow.async_step_server_history_check(),
        await flow.async_step_last_cleanup_run(),
        await flow.async_step_manage_ha_players(),
        await flow.async_step_restore_ha_players(),
        await flow.async_step_review_changes(),
    ]
    for result in results:
        _assert_form_serializable(result)
        keys = {str(getattr(marker, "schema", marker)) for marker in result["data_schema"].schema}
        assert CONF_BACK not in keys


@pytest.mark.asyncio
async def test_form_back_action_preserves_complete_draft(monkeypatch) -> None:
    from custom_components.emby.const import CONF_FLOW_ACTION, FLOW_ACTION_BACK

    patch_catalog(monkeypatch)
    flow, entry, store, hass = setup_flow()
    flow._draft_options[CONF_GLOBAL_PLAYER_MODE] = PLAYER_MODE_ACTIVE_ONLY
    result = await flow.async_step_ha_players({CONF_FLOW_ACTION: FLOW_ACTION_BACK})

    assert result["type"] == "menu"
    assert flow._draft_options[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_ACTIVE_ONLY
    assert entry.options[CONF_GLOBAL_PLAYER_MODE] == PLAYER_MODE_PERSISTENT
    assert hass.config_entries.updates == []
    assert hass.config_entries.reloads == []
    assert store.saved == []


@pytest.mark.asyncio
async def test_last_cleanup_run_uses_local_readable_values(monkeypatch) -> None:
    from custom_components.emby.models import CleanupRunReport

    patch_catalog(monkeypatch)
    flow, _entry, _store, _hass = setup_flow()
    flow._runtime.maintenance_state.report = CleanupRunReport(
        mode="manual",
        completed_at="2026-07-17T18:00:00+00:00",
        age_threshold_days=180,
        server_deleted=4,
        server_failed=1,
        skipped_active=2,
        next_run_at=None,
    )
    result = await flow.async_step_last_cleanup_run()
    placeholders = result["description_placeholders"]
    assert placeholders["run_at"] == "17.07.2026 20:00"
    assert placeholders["mode"] == "Manuell"
    assert placeholders["age"] == "180 Tage"
    assert placeholders["next_run"] == "Kein Lauf geplant"
    _assert_form_serializable(result)
'''
if "test_realistic_root_player_form_is_frontend_serializable" not in text:
    text += append
write(path, text)

write(
    "tests/test_options_flow_092_contract.py",
    r'''from __future__ import annotations

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
    strings = json.loads(
        (ROOT / "custom_components/emby/strings.json").read_text(encoding="utf-8")
    )
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
''',
)

path = "tests/test_player_context_090.py"
text = read(path)
append = r'''


def test_known_technical_apps_use_combined_non_playback_evidence() -> None:
    for app in ("Home Assistant", "EMBi", "Windmill", "Homarr Dashboard"):
        item = record(
            record_id=f"record-{app}",
            reported_id=f"reported-{app}",
            app=app,
            name="Service endpoint",
            supports_playback=False,
        )
        classification, reason = classify_client([item])
        assert classification == CLIENT_CLASS_TECHNICAL
        assert reason == "technical_app_without_playback"


def test_normal_playback_clients_are_not_misclassified_as_technical() -> None:
    for app in ("Emby TV", "Emby for iOS", "Emby Web", "Emby for Android"):
        item = record(
            record_id=f"record-{app}",
            reported_id=f"reported-{app}",
            app=app,
            supports_playback=True,
        )
        classification, _reason = classify_client([item])
        assert classification == CLIENT_CLASS_PLAYBACK


def test_active_technical_app_is_always_playback_protected() -> None:
    item = record(
        record_id="technical-active",
        reported_id="technical-active",
        app="Home Assistant",
        supports_playback=False,
    )
    classification, reason = classify_client([item], runtime_state="paused")
    assert classification == CLIENT_CLASS_PLAYBACK
    assert reason == "observed_active_playback"


def test_technical_catalog_resolves_non_playing_but_ambiguous_remains_protected() -> None:
    technical = record(
        record_id="technical",
        reported_id="technical",
        app="Windmill",
        supports_playback=False,
    )
    ambiguous = record(
        record_id="ambiguous",
        reported_id="ambiguous",
        app="Unknown custom client",
    )
    technical_entity = entity(technical.player_key, entity_id="media_player.technical")
    ambiguous_entity = entity(ambiguous.player_key, entity_id="media_player.ambiguous")
    players = build_player_catalog(
        [technical, ambiguous],
        registry_entries=[technical_entity, ambiguous_entity],
        states=States(),
        entry_id="entry",
        options=default_options_090(),
    )
    by_id = {player.entity_id: player for player in players}
    assert by_id["media_player.technical"].client_class == CLIENT_CLASS_TECHNICAL
    assert by_id["media_player.technical"].playback == "non_playing"
    assert by_id["media_player.technical"].protected_reason is None
    assert by_id["media_player.ambiguous"].protected_reason == "unknown_playback"
'''
if "test_known_technical_apps_use_combined_non_playback_evidence" not in text:
    text += append
write(path, text)

# Stable contracts, CI package version, docs and changelog.
for path in (
    "scripts/validate_stable_contract.py",
    ".github/workflows/quality.yml",
    ".github/workflows/test-artifact.yml",
    "tests/test_package_contract.py",
    "tests/test_repository_contract.py",
):
    text = read(path).replace("0.9.1", "0.9.2")
    write(path, text)

for path in (
    "README.md",
    "docs/PROJECT_STATE.md",
    "docs/release-checklist.md",
    "docs/repository-governance.md",
):
    text = read(path).replace("0.9.1", "0.9.2")
    write(path, text)

path = "CHANGELOG.md"
text = read(path)
entry = '''## [0.9.2] - 2026-07-17

### Fixed

- Repaired the Home Assistant player Options Flow for Home Assistant 2026.7.2 by emitting only frontend-serializable selector configuration.
- Replaced toggle and chevron-based Back entries with non-persistent native form actions that preserve the complete draft.
- Added a compact localized cleanup-run report and mobile-safe old-record labels without versions, UTC or internal identifiers.
- Shortened the matching Home Assistant player cleanup label while retaining the full safety contract in its description.
- Improved technical-client classification using capability, playback, app, registry and session evidence while keeping ambiguous clients protected.

### Validation

- Added realistic 69-record, 31-entity Options Flow fixtures, complete form serialization checks, navigation and translation contracts, mobile-label tests and technical-client classification coverage.
- Kept all destructive operations behind fresh identity and playback revalidation; no migration or test deletes server history or Home Assistant entities.

'''
if "## [0.9.2]" not in text:
    marker = text.find("## [")
    text = entry + text if marker == -1 else text[:marker] + entry + text[marker:]
write(path, text)

# Make release-request validation generic for future stable releases.
path = ".github/workflows/publish-stable-request.yml"
text = read(path)
text = replace_once(
    text,
    '          request = Path(".github/release-requests/v0.9.1.yml")\n',
    '''          import subprocess

          changed = [
              Path(line)
              for line in subprocess.check_output(
                  ["git", "diff", "--name-only", "origin/main...HEAD"],
                  text=True,
              ).splitlines()
              if line.startswith(".github/release-requests/") and line.endswith(".yml")
          ]
          if len(changed) != 1:
              raise SystemExit("Exactly one stable release request must change")
          request = changed[0]
''',
    label="generic release request validation",
)
write(path, text)

print("EMBi 0.9.2 patch applied")
