from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    if text.count(old) != 1:
        raise RuntimeError(f"Expected one match in {path}: {old[:80]!r}; found {text.count(old)}")
    write(path, text.replace(old, new, 1))


def replace_method(path: str, start_name: str, next_name: str, replacement: str) -> None:
    text = read(path)
    pattern = re.compile(
        rf"    async def {re.escape(start_name)}\(.*?(?=    async def {re.escape(next_name)}\()",
        re.S,
    )
    updated, count = pattern.subn(replacement.rstrip() + "\n\n", text, count=1)
    if count != 1:
        raise RuntimeError(f"Could not replace {start_name} in {path}")
    write(path, updated)


# Version and constants.
replace_once("custom_components/emby/const.py", 'VERSION = "0.9.2"', 'VERSION = "0.9.3"')
replace_once(
    "custom_components/emby/const.py",
    'CONF_SERVER_CLEANUP_AGE_DAYS = "server_cleanup_age_days"\n',
    'CONF_SERVER_CLEANUP_AGE_DAYS = "server_cleanup_age_days"\n'
    'CONF_MANUAL_CLEANUP_SCOPE = "manual_cleanup_scope"\n'
    'MANUAL_CLEANUP_SCOPE_AGE = "age_threshold"\n'
    'MANUAL_CLEANUP_SCOPE_ALL_SAFE = "all_safe_records"\n',
)
replace_once(
    "custom_components/emby/const.py",
    "AUTO_CLEANUP_INITIAL_DELAY_SECONDS = 120",
    "AUTO_CLEANUP_INITIAL_DELAY_SECONDS = 10",
)
manifest = json.loads(read("custom_components/emby/manifest.json"))
manifest["version"] = "0.9.3"
write("custom_components/emby/manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

# Manual cleanup may explicitly include recent records while retaining all other safety gates.
replace_once(
    "custom_components/emby/cleanup.py",
    "    active_player_keys: Iterable[str] = (),\n) -> DeviceCleanupPlan:",
    "    active_player_keys: Iterable[str] = (),\n    ignore_age: bool = False,\n) -> DeviceCleanupPlan:",
)
replace_once(
    "custom_components/emby/cleanup.py",
    "        elif activity < cutoff:\n            candidates.append(record)\n        else:\n            skipped_recent.append(record)",
    "        elif ignore_age or activity < cutoff:\n            candidates.append(record)\n        else:\n            skipped_recent.append(record)",
)
replace_once(
    "custom_components/emby/maintenance_cycle.py",
    "    remove_ha_entities: bool,\n) -> tuple[CleanupRunReport, bool]:",
    "    remove_ha_entities: bool,\n    ignore_age: bool = False,\n) -> tuple[CleanupRunReport, bool]:",
)
replace_once(
    "custom_components/emby/maintenance_cycle.py",
    "        selected_record_ids={str(value) for value in selected_record_ids},\n    )",
    "        selected_record_ids={str(value) for value in selected_record_ids},\n        ignore_age=ignore_age,\n    )",
)
replace_once(
    "custom_components/emby/maintenance_cycle_execute.py",
    "    selected_record_ids: set[str] | None = None,\n) -> tuple[CleanupRunReport, bool]:",
    "    selected_record_ids: set[str] | None = None,\n    ignore_age: bool = False,\n) -> tuple[CleanupRunReport, bool]:",
)
replace_once(
    "custom_components/emby/maintenance_cycle_execute.py",
    "            active_player_keys=active,\n        )",
    "            active_player_keys=active,\n            ignore_age=ignore_age if mode != RUN_MODE_AUTOMATIC else False,\n        )",
)

# Stronger technical-client classification: explicit technical identities beat uncertain capability metadata.
replace_once(
    "custom_components/emby/player_context.py",
    "def _technical_app_metadata(records: Iterable[EmbyDeviceRecord]) -> bool:\n    for record in records:\n        app = str(record.app_name or \"\").strip().casefold()\n        if app in _EXPLICIT_TECHNICAL_APPS:\n            return True\n        if any(app.startswith(f\"{name} \") for name in _EXPLICIT_TECHNICAL_APPS):\n            return True\n    return False\n",
    '''def _technical_app_metadata(records: Iterable[EmbyDeviceRecord]) -> bool:\n    \"\"\"Recognize explicit technical app or device identities without using user names.\"\"\"\n    phrases = {\n        *(_EXPLICIT_TECHNICAL_APPS),\n        \"home assistant player\",\n        \"homeassistant player\",\n        \"ha mcp\",\n        \"mcp server\",\n    }\n    for record in records:\n        values = (record.app_name, record.name)\n        for value in values:\n            normalized = str(value or \"\").strip().casefold()\n            if not normalized:\n                continue\n            if normalized in phrases:\n                return True\n            if any(\n                normalized.startswith(f\"{phrase} \")\n                or normalized.endswith(f\" {phrase}\")\n                or f\" {phrase} \" in normalized\n                for phrase in phrases\n            ):\n                return True\n    return False\n''',
)
replace_once(
    "custom_components/emby/player_context.py",
    '''    if any(record.playback_observed or record.supports_playback is True for record in items):\n        return CLIENT_CLASS_PLAYBACK, \"explicit_or_observed_playback\"\n    if any(record.api_only is True for record in items):\n        return CLIENT_CLASS_TECHNICAL, \"explicit_api_only\"\n''',
    '''    if any(record.api_only is True for record in items):\n        return CLIENT_CLASS_TECHNICAL, \"explicit_api_only\"\n''',
)
replace_once(
    "custom_components/emby/player_context.py",
    '''    users = _record_users(items)\n    no_playback_evidence = not any(\n        record.playback_observed or record.supports_playback is True for record in items\n    )\n    if items and not users and no_playback_evidence and _technical_app_metadata(items):\n        return CLIENT_CLASS_TECHNICAL, \"technical_app_without_playback\"\n\n    repeated_explicit_non_playback = (\n''',
    '''    no_observed_playback = not any(record.playback_observed for record in items)\n    if items and no_observed_playback and _technical_app_metadata(items):\n        return CLIENT_CLASS_TECHNICAL, \"explicit_technical_identity\"\n    if any(record.playback_observed or record.supports_playback is True for record in items):\n        return CLIENT_CLASS_PLAYBACK, \"explicit_or_observed_playback\"\n\n    users = _record_users(items)\n    repeated_explicit_non_playback = (\n''',
)

# Apply now returns to the root menu with a visible confirmation and a clean draft.
replace_once(
    "custom_components/emby/options_flow.py",
    '        self._pending_cleanup_age_days: int | None = None\n',
    '        self._pending_cleanup_age_days: int | None = None\n'
    '        self._pending_cleanup_ignore_age = False\n',
)
replace_once(
    "custom_components/emby/options_flow.py",
    '        self._automatic_age_preset: str | None = None\n',
    '        self._automatic_age_preset: str | None = None\n'
    '        self._apply_notice = ""\n',
)
replace_once(
    "custom_components/emby/options_flow.py",
    '                "review_count": str(count),\n',
    '                "review_count": str(count),\n'
    '                "apply_notice": self._apply_notice,\n',
)
replace_once(
    "custom_components/emby/options_flow.py",
    '        self._pending_cleanup_age_days = None\n',
    '        self._pending_cleanup_age_days = None\n'
    '        self._pending_cleanup_ignore_age = False\n',
)
old_abort = '''        return self.async_abort(\n            reason=\"apply_complete\",\n            description_placeholders={\n                \"removed\": \"0\",\n                \"restored\": str(restored),\n                \"enabled\": str(enabled),\n                \"protected\": str(len(protected_keys)),\n                \"failed\": str(failed),\n            },\n        )\n'''
new_root = '''        self._draft = OptionsDraft.from_options(updated)\n        self._original_options = self._draft.original\n        self._draft_options = self._draft.current\n        self._pending_cleanup_records = {}\n        self._pending_cleanup_age_days = None\n        self._pending_cleanup_ignore_age = False\n        self._pending_ha_entity_ids = []\n        self._pending_restore_player_keys = []\n        self._pending_enable_entity_ids.clear()\n        self._selected_group = None\n        self._selected_player_key = None\n        self._search_query = \"\"\n        self._page_by_step.clear()\n        self._review_error = None\n        self._section_error.clear()\n        if self._is_de():\n            self._apply_notice = (\n                \"Änderungen gespeichert und EMBi neu geladen. \"\n                f\"Wiederhergestellt: {restored}, aktiviert: {enabled}, \"\n                f\"geschützt: {len(protected_keys)}, fehlgeschlagen: {failed}.\"\n            )\n        else:\n            self._apply_notice = (\n                \"Changes saved and EMBi reloaded. \"\n                f\"Restored: {restored}, enabled: {enabled}, \"\n                f\"protected: {len(protected_keys)}, failed: {failed}.\"\n            )\n        return await self.async_step_init()\n'''
replace_once("custom_components/emby/options_flow.py", old_abort, new_root)
replace_once(
    "custom_components/emby/options_flow.py",
    '    """EMBi 0.9.2 Options Flow with a preserved in-memory draft."""',
    '    """EMBi 0.9.3 Options Flow with a preserved in-memory draft."""',
)

# Inline per-player switches replace the exception multi-select and its extra page.
replace_once(
    "custom_components/emby/options_devices.py",
    "import logging\n",
    "import logging\nfrom collections import Counter\n",
)
insert_after = '''def _page_selector(total_pages: int) -> selector.SelectSelector:\n    return _single(\n        [\n            {\"value\": str(page), \"label\": f\"{page} / {total_pages}\"}\n            for page in range(1, total_pages + 1)\n        ]\n    )\n\n\n'''
toggle_helper = '''def _player_toggle_fields(players):\n    \"\"\"Return stable, unique user-facing labels for native BooleanSelectors.\"\"\"\n    options = player_options(players)\n    counts = Counter(option[\"label\"] for option in options)\n    seen: Counter[str] = Counter()\n    by_key = {player.player_key: player for player in players}\n    result = []\n    for option in options:\n        base = option[\"label\"]\n        seen[base] += 1\n        label = base if counts[base] == 1 else f\"{base} ({seen[base]})\"\n        player = by_key.get(option[\"value\"])\n        if player is not None:\n            result.append((label, player))\n    return result\n\n\n'''
replace_once("custom_components/emby/options_devices.py", insert_after, insert_after + toggle_helper)
new_group_method = '''    async def async_step_player_group(self, user_input: dict[str, Any] | None = None):\n        if not self._selected_group:\n            return await self.async_step_ha_players()\n        errors: dict[str, str] = {}\n        try:\n            players, _stats = await fresh_catalog(self)\n        except Exception:\n            _LOGGER.exception(\"Failed to load current EMBi player catalog\")\n            players = []\n            errors[\"base\"] = \"cannot_connect\"\n        group_players = list(group_player_catalog(players).get(self._selected_group, []))\n        toggle_fields = _player_toggle_fields(group_players)\n        fields: dict[Any, Any] = {}\n        for label, player in toggle_fields:\n            fields[vol.Required(label, default=player.visible_in_embi)] = selector.BooleanSelector()\n        if group_players:\n            fields[vol.Optional(CONF_SELECTED_PLAYER_KEY)] = _single(player_options(group_players))\n        fields[vol.Required(CONF_FLOW_ACTION, default=\"save\")] = navigation_selector(\n            german=self._is_de(),\n            primary_label=\"Speichern & zurück\" if self._is_de() else \"Save & back\",\n        )\n\n        if user_input is not None:\n            if back_requested(user_input):\n                return await self.async_step_back_to_ha_players()\n            if not errors:\n                requested = {\n                    player.player_key: bool(user_input.get(label, player.visible_in_embi))\n                    for label, player in toggle_fields\n                }\n                if any(\n                    not requested.get(player.player_key, player.visible_in_embi)\n                    and player.playback in ACTIVE_PLAYBACK_STATES\n                    for player in group_players\n                ):\n                    errors[\"base\"] = \"playback_protected\"\n                else:\n                    hidden = {\n                        str(value)\n                        for value in self._draft_options.get(CONF_HIDDEN_EXACT_PLAYERS, [])\n                    }\n                    group_keys = {player.player_key for player in group_players}\n                    user_name = (\n                        self._selected_group.removeprefix(GROUP_USER_PREFIX)\n                        if self._selected_group.startswith(GROUP_USER_PREFIX)\n                        else None\n                    )\n                    any_visible = any(requested.values())\n                    if user_name is not None:\n                        visibility = dict(\n                            self._draft_options.get(CONF_USER_MASTER_VISIBILITY, {})\n                        )\n                        visibility[user_name] = any_visible\n                        self._draft_options[CONF_USER_MASTER_VISIBILITY] = visibility\n                        hidden -= group_keys\n                        if any_visible:\n                            hidden.update(\n                                key for key, visible in requested.items() if not visible\n                            )\n                    elif self._selected_group == GROUP_TECHNICAL:\n                        self._draft_options[CONF_TECHNICAL_ACCESS_VISIBILITY] = any_visible\n                        hidden -= group_keys\n                        if any_visible:\n                            hidden.update(\n                                key for key, visible in requested.items() if not visible\n                            )\n                    else:\n                        hidden -= group_keys\n                        hidden.update(key for key, visible in requested.items() if not visible)\n                    self._draft_options[CONF_HIDDEN_EXACT_PLAYERS] = sorted(hidden)\n                    selected = user_input.get(CONF_SELECTED_PLAYER_KEY)\n                    if selected:\n                        self._selected_player_key = str(selected)\n                        return await self.async_step_player_details()\n                    return await self.async_step_ha_players()\n\n        group_name = next(\n            (\n                option[\"label\"].rsplit(\" · \", 1)[0]\n                for option in group_options(players, german=self._is_de())\n                if option[\"value\"] == self._selected_group\n            ),\n            self._selected_group,\n        )\n        return self.async_show_form(\n            step_id=\"player_group\",\n            data_schema=vol.Schema(fields),\n            errors=errors,\n            description_placeholders={\n                \"group\": str(group_name),\n                \"count\": str(len(group_players)),\n            },\n        )\n'''
replace_method(
    "custom_components/emby/options_devices.py",
    "async_step_player_group",
    "async_step_player_exceptions",
    new_group_method,
)
redirect_exceptions = '''    async def async_step_player_exceptions(self, user_input: dict[str, Any] | None = None):\n        \"\"\"Compatibility redirect; player switches now live directly on the group page.\"\"\"\n        return await self.async_step_player_group(user_input)\n'''
replace_method(
    "custom_components/emby/options_devices.py",
    "async_step_player_exceptions",
    "async_step_player_details",
    redirect_exceptions,
)
write(
    "custom_components/emby/options_devices.py",
    read("custom_components/emby/options_devices.py").replace(
        'primary_label="Übernehmen" if self._is_de() else "Apply"',
        'primary_label="Speichern & zurück" if self._is_de() else "Save & back"',
    ),
)

# Cleanup UI: explicit all-safe manual scope, no saved-threshold prerequisite, quick automatic catch-up.
replace_once(
    "custom_components/emby/options_cleanup.py",
    "    CONF_FLOW_ACTION,\n",
    "    CONF_FLOW_ACTION,\n    CONF_MANUAL_CLEANUP_SCOPE,\n",
)
replace_once(
    "custom_components/emby/options_cleanup.py",
    "    MAX_SERVER_CLEANUP_AGE_DAYS,\n",
    "    MANUAL_CLEANUP_SCOPE_AGE,\n    MANUAL_CLEANUP_SCOPE_ALL_SAFE,\n    MAX_SERVER_CLEANUP_AGE_DAYS,\n",
)
replace_once(
    "custom_components/emby/options_cleanup.py",
    '_AUTO_CUSTOM = "automatic_custom_age_days"\n',
    '_AUTO_CUSTOM = "automatic_custom_age_days"\n_MANUAL_SCOPE = CONF_MANUAL_CLEANUP_SCOPE\n',
)
replace_once(
    "custom_components/emby/options_cleanup.py",
    "        self._pending_cleanup_age_days = None\n        return await self.async_step_server_cleanup()",
    "        self._pending_cleanup_age_days = None\n        self._pending_cleanup_ignore_age = False\n        return await self.async_step_server_cleanup()",
)
# Scope state and plan behavior.
replace_once(
    "custom_components/emby/options_cleanup.py",
    "        errors: dict[str, str] = {}\n        try:\n            devices = await self._devices()",
    "        errors: dict[str, str] = {}\n        scope = MANUAL_CLEANUP_SCOPE_AGE\n        if user_input is not None:\n            scope = str(user_input.get(_MANUAL_SCOPE, MANUAL_CLEANUP_SCOPE_AGE))\n        ignore_age = scope == MANUAL_CLEANUP_SCOPE_ALL_SAFE\n        try:\n            devices = await self._devices()",
)
replace_once(
    "custom_components/emby/options_cleanup.py",
    "            active_player_keys=active_player_keys(self.hass, self._entry),\n        )",
    "            active_player_keys=active_player_keys(self.hass, self._entry),\n            ignore_age=ignore_age,\n        )",
)
old_fields = '''        fields: dict[Any, Any] = {vol.Required(_MANUAL_PRESET, default=preset): _age_preset()}\n        if preset == AGE_PRESET_CUSTOM:\n            fields[vol.Required(_MANUAL_CUSTOM, default=age_days)] = _number()\n'''
new_fields = '''        fields: dict[Any, Any] = {\n            vol.Required(_MANUAL_SCOPE, default=scope): selector.SelectSelector(\n                selector.SelectSelectorConfig(\n                    options=[\n                        {\n                            \"value\": MANUAL_CLEANUP_SCOPE_AGE,\n                            \"label\": (\n                                \"Nur Einträge außerhalb der Altersgrenze\"\n                                if self._is_de()\n                                else \"Only records beyond the age threshold\"\n                            ),\n                        },\n                        {\n                            \"value\": MANUAL_CLEANUP_SCOPE_ALL_SAFE,\n                            \"label\": (\n                                \"Alle sicheren Einträge – unabhängig vom Alter\"\n                                if self._is_de()\n                                else \"All safe records – regardless of age\"\n                            ),\n                        },\n                    ],\n                    mode=selector.SelectSelectorMode.DROPDOWN,\n                )\n            )\n        }\n        if not ignore_age:\n            fields[vol.Required(_MANUAL_PRESET, default=preset)] = _age_preset()\n            if preset == AGE_PRESET_CUSTOM:\n                fields[vol.Required(_MANUAL_CUSTOM, default=age_days)] = _number()\n'''
replace_once("custom_components/emby/options_cleanup.py", old_fields, new_fields)
# Resolution only applies in threshold mode.
replace_once(
    "custom_components/emby/options_cleanup.py",
    '''        if user_input is not None and not back_requested(user_input):\n            try:\n                age_days = _resolve(user_input, _MANUAL_PRESET, _MANUAL_CUSTOM)\n            except (KeyError, TypeError, ValueError):\n                errors[\"base\"] = \"invalid_age\"\n            else:\n                self._draft_options[CONF_SERVER_CLEANUP_AGE_DAYS] = age_days\n                self._manual_age_preset = age_preset_for_days(age_days)\n''',
    '''        if user_input is not None and not back_requested(user_input) and not ignore_age:\n            try:\n                age_days = _resolve(user_input, _MANUAL_PRESET, _MANUAL_CUSTOM)\n            except (KeyError, TypeError, ValueError):\n                errors[\"base\"] = \"invalid_age\"\n            else:\n                self._draft_options[CONF_SERVER_CLEANUP_AGE_DAYS] = age_days\n                self._manual_age_preset = age_preset_for_days(age_days)\n''',
)
# Permit explicit manual deletion even when the selected threshold differs from the saved preference.
old_selection = '''            if selected and not errors:\n                saved_age = int(\n                    self._entry.options.get(\n                        CONF_SERVER_CLEANUP_AGE_DAYS,\n                        DEFAULT_SERVER_CLEANUP_AGE_DAYS,\n                    )\n                )\n                if self._dirty or age_days != saved_age:\n                    errors[\"base\"] = \"unsaved_changes\"\n                elif any(record_id not in candidates for record_id in selected):\n                    errors[\"base\"] = \"invalid_selection\"\n                else:\n                    self._pending_cleanup_records = {\n                        record_id: candidates[record_id] for record_id in selected\n                    }\n                    self._pending_cleanup_age_days = age_days\n                    return await self.async_step_confirm_server_deletion()\n            elif (\n                not selected\n                and not errors\n                and age_days\n                != int(\n                    self._entry.options.get(\n                        CONF_SERVER_CLEANUP_AGE_DAYS,\n                        DEFAULT_SERVER_CLEANUP_AGE_DAYS,\n                    )\n                )\n            ):\n                return await self.async_step_server_cleanup()\n'''
new_selection = '''            if selected and not errors:\n                if any(record_id not in candidates for record_id in selected):\n                    errors[\"base\"] = \"invalid_selection\"\n                else:\n                    self._pending_cleanup_records = {\n                        record_id: candidates[record_id] for record_id in selected\n                    }\n                    self._pending_cleanup_age_days = age_days\n                    self._pending_cleanup_ignore_age = ignore_age\n                    return await self.async_step_confirm_server_deletion()\n'''
replace_once("custom_components/emby/options_cleanup.py", old_selection, new_selection)
replace_once(
    "custom_components/emby/options_cleanup.py",
    '                "without_activity": str(len(plan.skipped_without_activity)),\n',
    '                "without_activity": str(len(plan.skipped_without_activity)),\n'
    '                "scope": (\n'
    '                    "Alle sicheren Einträge" if self._is_de() else "All safe records"\n'
    '                ) if ignore_age else (\n'
    '                    "Altersgrenze" if self._is_de() else "Age threshold"\n'
    '                ),\n',
)
replace_once(
    "custom_components/emby/options_cleanup.py",
    '                "count": str(count),\n                "details": server_device_confirmation_details(',
    '                "count": str(count),\n'
    '                "scope": (\n'
    '                    "Unabhängig vom Alter" if self._is_de() else "Regardless of age"\n'
    '                ) if self._pending_cleanup_ignore_age else (\n'
    '                    f"Älter als {self._pending_cleanup_age_days} Tage"\n'
    '                    if self._is_de()\n'
    '                    else f"Older than {self._pending_cleanup_age_days} days"\n'
    '                ),\n'
    '                "details": server_device_confirmation_details(',
)
replace_once(
    "custom_components/emby/options_cleanup.py",
    "            remove_ha_entities=False,\n        )",
    "            remove_ha_entities=False,\n            ignore_age=self._pending_cleanup_ignore_age,\n        )",
)
# Reset after manual execution.
replace_once(
    "custom_components/emby/options_cleanup.py",
    "        self._pending_cleanup_age_days = None\n        if reload_needed:",
    "        self._pending_cleanup_age_days = None\n        self._pending_cleanup_ignore_age = False\n        if reload_needed:",
)
# Last-run page uses the native OK button instead of a one-option action dropdown.
replace_once(
    "custom_components/emby/options_cleanup.py",
    '''    async def async_step_last_cleanup_run(self, user_input: dict[str, Any] | None = None):\n        if back_requested(user_input):\n            return await self.async_step_server_cleanup()\n''',
    '''    async def async_step_last_cleanup_run(self, user_input: dict[str, Any] | None = None):\n        if user_input is not None:\n            return await self.async_step_server_cleanup()\n''',
)
replace_once(
    "custom_components/emby/options_cleanup.py",
    '''            data_schema=vol.Schema(\n                {\n                    vol.Required(CONF_FLOW_ACTION, default=FLOW_ACTION_BACK): navigation_selector(\n                        german=self._is_de()\n                    )\n                }\n            ),\n''',
    '''            data_schema=vol.Schema({}),\n''',
)
write(
    "custom_components/emby/options_cleanup.py",
    read("custom_components/emby/options_cleanup.py").replace(
        'primary_label="Übernehmen" if self._is_de() else "Apply"',
        'primary_label="Speichern & zurück" if self._is_de() else "Save & back"',
    ),
)

# User-facing copy and release documentation.
def update_flow_json(path: str, german: bool) -> None:
    data = json.loads(read(path))
    options = data.setdefault("options", {})
    steps = options.setdefault("step", {})
    init = steps.get("init", {})
    description = str(init.get("description", ""))
    if "{apply_notice}" not in description:
        init["description"] = description.rstrip() + "\n\n{apply_notice}"
    group = steps.get("player_group", {})
    group["description"] = (
        "{count} Player gehören zu dieser Gruppe. Jeder Player kann direkt ein- oder ausgeschaltet werden. Laufende oder pausierte Wiedergaben bleiben geschützt. Optional kann unten eine Detailansicht geöffnet werden."
        if german
        else "{count} players belong to this group. Each player can be switched on or off directly. Playing or paused sessions remain protected. A detail view can optionally be opened below."
    )
    history = steps.get("server_history_check", {})
    history["description"] = (
        "{total} Einträge geprüft\n{candidates} sind im Modus „{scope}“ sicher auswählbar\n{active} sind durch aktive Wiedergabe geschützt\n{recent} erfüllen die Altersregel nicht\n{without_activity} besitzen keinen gültigen Aktivitätszeitpunkt\n\nIm Modus „Alle sicheren Einträge“ können auch jüngere Einträge manuell gewählt werden. Aktive, pausierte oder nicht eindeutig prüfbare Einträge bleiben immer geschützt."
        if german
        else "{total} records checked\n{candidates} are safely selectable in “{scope}” mode\n{active} are protected by active playback\n{recent} do not meet the age rule\n{without_activity} have no valid activity timestamp\n\n“All safe records” also allows younger records to be selected manually. Active, paused, or ambiguous records always remain protected."
    )
    confirm = steps.get("confirm_server_deletion", {})
    confirm["description"] = (
        "{count} Einträge wurden ausgewählt. Geltungsbereich: {scope}. Vor der Löschung werden Identität, Aktivität und Wiedergabestatus erneut geprüft.\n\n{details}"
        if german
        else "{count} records were selected. Scope: {scope}. Identity, activity, and playback state are revalidated before deletion.\n\n{details}"
    )
    write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

update_flow_json("custom_components/emby/strings.json", False)
update_flow_json("custom_components/emby/translations/en.json", False)
update_flow_json("custom_components/emby/translations/de.json", True)

changelog = read("CHANGELOG.md")
entry = '''## 0.9.3\n\n- Return to the EMBi main menu after applying settings and show a clear saved/reloaded confirmation.\n- Replace group exception multi-selects with direct native on/off switches for every player.\n- Recognize Home Assistant, EMBi, Homarr, Windmill and other explicit API-only identities as technical clients even when an administrator user is attached.\n- Add an explicit manual cleanup scope that can safely select recent server-history records while preserving playback, activity and identity revalidation.\n- Start newly enabled automatic cleanup through the persistent scheduler after a short ten-second grace period.\n- Replace the last-run Back dropdown with the native OK action.\n\n'''
if "## 0.9.3" not in changelog:
    marker = next((m for m in ("## 0.9.2", "# Changelog\n") if m in changelog), None)
    if marker == "## 0.9.2":
        changelog = changelog.replace(marker, entry + marker, 1)
    elif marker:
        changelog = changelog.replace(marker, marker + "\n\n" + entry, 1)
    else:
        changelog = entry + changelog
write("CHANGELOG.md", changelog)

readme = read("README.md").replace("Upgrade auf 0.9.2", "Upgrade auf 0.9.3")
readme = readme.replace("Der in 0.9.0 noch", "Der in 0.9.0 noch")
ux_note = '''\n## Bedienung ab 0.9.3\n\n- **Änderungen übernehmen** speichert, lädt EMBi neu und führt sichtbar zur Hauptseite zurück.\n- Innerhalb einer Benutzer- oder Clientgruppe besitzt jeder Player direkt einen Ein-/Aus-Schalter; die zusätzliche Ausnahmenseite entfällt.\n- **Technische Zugriffe** werden anhand eindeutiger App-, Geräte-, API- und Sitzungsmerkmale klassifiziert.\n- Die manuelle Serverprüfung kann wahlweise nur alte oder alle sicher prüfbaren Einträge anzeigen. Die automatische Bereinigung hält immer an ihrer Altersgrenze fest.\n\n'''
if "## Bedienung ab 0.9.3" not in readme:
    readme = readme.replace("## Änderungen prüfen", ux_note + "## Änderungen prüfen", 1)
write("README.md", readme)

for path in ("docs/PROJECT_STATE.md", "docs/release-checklist.md", "docs/repository-governance.md"):
    text = read(path)
    text = text.replace("0.9.2", "0.9.3")
    write(path, text)

# Update old flow expectations and add focused regressions.
test_flow = read("tests/test_options_flow.py")
test_flow = test_flow.replace('assert result["type"] == "abort"\n    assert result["reason"] == "apply_complete"', 'assert result["type"] == "menu"\n    assert result["step_id"] == "init"\n    assert "gespeichert" in result["description_placeholders"]["apply_notice"]')
test_flow = test_flow.replace('assert result["reason"] == "apply_complete"', 'assert result["type"] == "menu"\n    assert result["step_id"] == "init"')
write("tests/test_options_flow.py", test_flow)

new_tests = r'''from __future__ import annotations

from datetime import UTC, datetime

from custom_components.emby.api import EmbyDeviceRecord
from custom_components.emby.cleanup import plan_device_cleanup
from custom_components.emby.player_context import CLIENT_CLASS_TECHNICAL, classify_client


def _record(*, record_id: str, days_old: int, name: str = "TV", app: str = "Emby TV"):
    day = datetime(2026, 7, 18, tzinfo=UTC).timestamp() - days_old * 86400
    stamp = datetime.fromtimestamp(day, tz=UTC).isoformat()
    return EmbyDeviceRecord(
        record_id=record_id,
        reported_device_id=record_id,
        name=name,
        app_name=app,
        last_user_name="EmbyAdmin_Seger",
        last_activity_date=stamp,
    )


def test_manual_all_safe_scope_includes_recent_but_never_active() -> None:
    now = datetime(2026, 7, 18, tzinfo=UTC)
    recent = _record(record_id="recent", days_old=2)
    active = _record(record_id="active", days_old=1)
    normal = plan_device_cleanup([recent, active], now=now, age_days=180)
    assert normal.candidates == ()
    all_safe = plan_device_cleanup(
        [recent, active],
        now=now,
        age_days=180,
        active_player_keys={active.player_key},
        ignore_age=True,
    )
    assert all_safe.candidates == (recent,)
    assert all_safe.skipped_active == (active,)


def test_explicit_technical_device_with_admin_user_is_technical() -> None:
    record = _record(
        record_id="homarr",
        days_old=1,
        name="Emby Homarr",
        app="Emby",
    )
    client_class, reason = classify_client([record], registry_backed=True)
    assert client_class == CLIENT_CLASS_TECHNICAL
    assert reason == "explicit_technical_identity"


def test_active_technical_identity_remains_playback_protected() -> None:
    record = _record(
        record_id="ha",
        days_old=1,
        name="Home Assistant player",
        app="Emby",
    )
    client_class, reason = classify_client([record], runtime_state="playing")
    assert client_class != CLIENT_CLASS_TECHNICAL
    assert reason == "observed_active_playback"


def test_automatic_path_cannot_bypass_age_contract_source() -> None:
    source = open("custom_components/emby/maintenance_cycle_execute.py", encoding="utf-8").read()
    assert "ignore_age=ignore_age if mode != RUN_MODE_AUTOMATIC else False" in source


def test_apply_returns_root_and_group_uses_boolean_switches_source() -> None:
    flow = open("custom_components/emby/options_flow.py", encoding="utf-8").read()
    devices = open("custom_components/emby/options_devices.py", encoding="utf-8").read()
    assert "return await self.async_step_init()" in flow
    apply_tail = flow.split("async def async_step_apply_changes", 1)[1]
    assert 'reason="apply_complete"' not in apply_tail
    group = devices.split("async def async_step_player_group", 1)[1].split(
        "async def async_step_player_exceptions", 1
    )[0]
    assert "selector.BooleanSelector()" in group
    assert "CONF_HIDDEN_PAGE_PLAYER_KEYS" not in group
'''
write("tests/test_options_flow_093.py", new_tests)

# Version assertions in current-release contract files.
for path in (
    "tests/test_package_contract.py",
    "tests/test_repository_contract.py",
    "tests/test_options_flow_092_contract.py",
):
    text = read(path)
    text = text.replace('"0.9.2"', '"0.9.3"')
    write(path, text)
