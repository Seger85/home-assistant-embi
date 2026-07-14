from __future__ import annotations

DOMAIN = "emby"
NAME = "Emby Integration - EMBi"
VERSION = "0.3.0-rc2"
PLATFORMS = ["media_player"]

CONF_CLIENT_MODE = "client_mode"
CONF_ALLOWED_DEVICE_IDS = "allowed_device_ids"
CONF_IGNORED_DEVICE_IDS = "ignored_device_ids"

CONF_CLEANUP_ENTITY_IDS = "cleanup_entity_ids"
CONF_CONFIRM_CLEANUP = "confirm_cleanup"
CONF_CONFIRM_BULK = "confirm_bulk"

CONF_SERVER_CLEANUP_ENABLED = "server_cleanup_enabled"
CONF_SERVER_CLEANUP_API_KEY = "server_cleanup_api_key"
CONF_DELETE_DEVICE_RECORD_IDS = "delete_device_record_ids"
CONF_ADD_DELETED_TO_IGNORED = "add_deleted_to_ignored"
CONF_CONFIRM_DELETE = "confirm_delete"
CONF_CONFIRMATION_TEXT = "confirmation_text"

CLIENT_MODE_ALL = "all"
CLIENT_MODE_ACTIVE_ONLY = "active_only"
CLIENT_MODE_ALLOWLIST = "allowlist"
CLIENT_MODES = [CLIENT_MODE_ALL, CLIENT_MODE_ACTIVE_ONLY, CLIENT_MODE_ALLOWLIST]

DEFAULT_PORT = 8096
DEFAULT_SSL_PORT = 8920
DEFAULT_SSL = False
