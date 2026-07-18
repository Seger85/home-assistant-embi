from __future__ import annotations

DOMAIN = "emby"
NAME = "Emby Integration - EMBi"
VERSION = "0.9.5"
PLATFORMS = ["media_player"]

CONFIG_ENTRY_VERSION = 4
CONFIG_ENTRY_MINOR_VERSION = 0
OPTIONS_SCHEMA_VERSION = 2
CONF_OPTIONS_SCHEMA_VERSION = "options_schema_version"

# Canonical 0.9 player-visibility model.
CONF_GLOBAL_PLAYER_MODE = "global_player_mode"
PLAYER_MODE_PERSISTENT = "persistent"
PLAYER_MODE_ACTIVE_ONLY = "active_only"
PLAYER_MODES = {PLAYER_MODE_PERSISTENT, PLAYER_MODE_ACTIVE_ONLY}
CONF_AUTO_SHOW_NEW_PLAYERS = "auto_show_new_players"
CONF_TECHNICAL_ACCESS_VISIBILITY = "technical_access_visibility"
CONF_HIDDEN_EXACT_PLAYERS = "hidden_exact_players"
CONF_HIDDEN_WHOLE_DEVICES = "hidden_whole_devices"
CONF_USER_MASTER_VISIBILITY = "user_master_visibility"
CONF_UNRESOLVED_LEGACY_RULES = "unresolved_legacy_rules"

# Existing allow-list data remains useful when new players must not appear automatically.
CONF_ALLOWED_DEVICE_IDS = "allowed_device_ids"

# Legacy 0.3 keys are read only by the idempotent migration.
CONF_CLIENT_MODE = "client_mode"
CONF_IGNORED_PLAYER_KEYS = "ignored_player_keys"
CONF_IGNORED_REPORTED_DEVICE_IDS = "ignored_reported_device_ids"
CONF_UNRESOLVED_IGNORED_IDS = "unresolved_ignored_ids"
CLIENT_MODE_ALL = "all"
CLIENT_MODE_ACTIVE_ONLY = "active_only"
CLIENT_MODE_ALLOWLIST = "allowlist"
CLIENT_MODES = [CLIENT_MODE_ALL, CLIENT_MODE_ACTIVE_ONLY, CLIENT_MODE_ALLOWLIST]

# Native Options Flow fields which are intentionally not persisted as duplicate state.

# 0.9.1 compact navigation and pagination fields.
CONF_BACK = "back"  # Legacy input name; never exposed or persisted by 0.9.2 forms.
CONF_FLOW_ACTION = "flow_action"
FLOW_ACTION_SAVE = "save"
FLOW_ACTION_BACK = "back"
FLOW_ACTION_OPEN_AUTOMATIC = "open_automatic_cleanup"
FLOW_ACTION_OPEN_HISTORY = "open_server_history_check"
FLOW_ACTION_OPEN_LAST_RUN = "open_last_cleanup_run"
FLOW_ACTION_APPLY = "apply_changes"
FLOW_ACTION_DISCARD = "discard_changes"
FLOW_ACTION_EXECUTE = "execute"
CONF_PAGE = "page"
CONF_PLAYER_ACTION = "player_action"
PLAYER_ACTION_MANAGE_EXCEPTIONS = "manage_exceptions"
PLAYER_ACTION_DETAILS = "player_details"
PLAYER_ACTION_REMOVE = "remove_ha_players"
PLAYER_ACTION_RESTORE = "restore_ha_players"
CONF_HIDDEN_PAGE_PLAYER_KEYS = "hidden_page_player_keys"
CONF_SELECTED_PLAYER_KEY = "selected_player_key"
CONF_SELECTED_RESTORE_KEYS = "selected_restore_player_keys"
CONF_REVIEW_ACTION = "review_action"
REVIEW_ACTION_APPLY = "apply_changes"
REVIEW_ACTION_DISCARD = "discard_changes"
REVIEW_ACTION_BACK = "back_to_init"
PLAYER_PAGE_SIZE = 12
CONF_ONLY_DURING_PLAYBACK = "only_during_playback"
CONF_SEARCH_QUERY = "search_query"
CONF_SELECTED_GROUP = "selected_group"
CONF_VISIBLE_PLAYER_KEYS = "visible_player_keys"
CONF_ENABLE_ENTITY_IDS = "enable_entity_ids"
CONF_BACK_TO_ROOT = "back_to_root"
CONF_BACK_TO_DEVICES = "back_to_devices"
CONF_BACK_TO_CLEANUP = "back_to_cleanup"
CONF_CLEANUP_ACTION = "cleanup_action"
CLEANUP_ACTION_MANUAL_CHECK = "manual_check"
CLEANUP_ACTION_MANAGE_HA_PLAYERS = "manage_ha_players"
CONF_SELECTED_HA_ENTITY_IDS = "selected_ha_entity_ids"
CONF_CONFIRM_HA_REMOVAL = "confirm_ha_removal"
CONF_CONFIRM_SERVER_DELETION = "confirm_server_deletion"

CONF_MAINTENANCE_STORE_INITIALIZED = "maintenance_store_initialized"
CONF_REGISTRY_RECONCILIATION_VERSION = "registry_reconciliation_version"
REGISTRY_RECONCILIATION_VERSION = 1
CONF_CLEANUP_ENTITY_IDS = "cleanup_entity_ids"
CONF_CONFIRM_CLEANUP = "confirm_cleanup"
CONF_CONFIRM_BULK = "confirm_bulk"
CONF_CONFIRM_APPLY = "confirm_apply"
CONF_CONFIRM_DISCARD = "confirm_discard"

CONF_SERVER_CLEANUP_ENABLED = "server_cleanup_enabled"
CONF_SERVER_CLEANUP_AGE_DAYS = "server_cleanup_age_days"
CONF_MANUAL_CLEANUP_SCOPE = "manual_cleanup_scope"
MANUAL_CLEANUP_SCOPE_AGE = "age_threshold"
MANUAL_CLEANUP_SCOPE_ALL_SAFE = "all_safe_records"
CONF_DELETE_DEVICE_RECORD_IDS = "delete_device_record_ids"
CONF_REMOVE_DELETED_HA_ENTITIES = "remove_deleted_ha_entities"
CONF_CONFIRM_DELETE = "confirm_delete"
CONF_CONFIRMATION_TEXT = "confirmation_text"

CONF_SERVER_AUTO_CLEANUP_ENABLED = "server_auto_cleanup_enabled"
CONF_SERVER_AUTO_CLEANUP_AGE_DAYS = "server_auto_cleanup_age_days"
CONF_SERVER_AUTO_CLEANUP_REMOVE_HA_ENTITIES = "server_auto_cleanup_remove_ha_entities"
CONF_CONFIRM_AUTO_CLEANUP = "confirm_auto_cleanup"

CONF_AGE_PRESET = "age_preset"
CONF_CUSTOM_AGE_DAYS = "custom_age_days"
AGE_PRESET_7 = "preset_7"
AGE_PRESET_30 = "preset_30"
AGE_PRESET_90 = "preset_90"
AGE_PRESET_180 = "preset_180"
AGE_PRESET_365 = "preset_365"
AGE_PRESET_CUSTOM = "custom"
AGE_PRESETS = {
    AGE_PRESET_7: 7,
    AGE_PRESET_30: 30,
    AGE_PRESET_90: 90,
    AGE_PRESET_180: 180,
    AGE_PRESET_365: 365,
}

DEFAULT_PORT = 8096
DEFAULT_SSL_PORT = 8920
DEFAULT_SSL = False
DEFAULT_AUTO_SHOW_NEW_PLAYERS = True
DEFAULT_TECHNICAL_ACCESS_VISIBILITY = False
DEFAULT_SERVER_CLEANUP_AGE_DAYS = 365
DEFAULT_REMOVE_HA_ENTITIES = False
MIN_SERVER_CLEANUP_AGE_DAYS = 1
MAX_SERVER_CLEANUP_AGE_DAYS = 3650
AUTO_CLEANUP_INITIAL_DELAY_SECONDS = 10
AUTO_CLEANUP_INTERVAL_HOURS = 24

RUN_STATUS_IDLE = "idle"
RUN_STATUS_RUNNING = "running"
RUN_STATUS_SERVER_COMPLETED = "server_completed"
RUN_STATUS_REGISTRY_PENDING = "registry_pending"
RUN_STATUS_COMPLETED = "completed"
RUN_STATUS_PARTIAL_FAILURE = "partial_failure"
RUN_STATUS_FAILED = "failed"
RUN_STATUS_INTERRUPTED = "interrupted"

RUN_MODE_MANUAL = "manual"
RUN_MODE_AUTOMATIC = "automatic"
RUN_MODES = {RUN_MODE_MANUAL, RUN_MODE_AUTOMATIC}
RUN_STATUSES = {
    RUN_STATUS_IDLE,
    RUN_STATUS_RUNNING,
    RUN_STATUS_SERVER_COMPLETED,
    RUN_STATUS_REGISTRY_PENDING,
    RUN_STATUS_COMPLETED,
    RUN_STATUS_PARTIAL_FAILURE,
    RUN_STATUS_FAILED,
    RUN_STATUS_INTERRUPTED,
}

FOLLOW_UP_IDLE = "idle"
FOLLOW_UP_PENDING = "pending"
FOLLOW_UP_COMPLETED = "completed"
FOLLOW_UP_INTERRUPTED = "interrupted"
FOLLOW_UP_SKIPPED = "skipped"
FOLLOW_UP_STATUSES = {
    FOLLOW_UP_IDLE,
    FOLLOW_UP_PENDING,
    FOLLOW_UP_COMPLETED,
    FOLLOW_UP_INTERRUPTED,
    FOLLOW_UP_SKIPPED,
}

# Keep the Home Assistant Store envelope version stable and migrate the internal schema.
MAINTENANCE_STORE_STORAGE_VERSION = 1
MAINTENANCE_STORE_VERSION = 2
MAINTENANCE_STORE_KEY_PREFIX = f"{DOMAIN}.maintenance"
MAINTENANCE_NOTIFICATION_ID_PREFIX = f"{DOMAIN}_maintenance"
