from __future__ import annotations

DOMAIN = "emby"
NAME = "Emby Integration - EMBi"
VERSION = "0.2.0"
PLATFORMS = ["media_player"]

CONF_CLIENT_MODE = "client_mode"
CONF_ALLOWED_DEVICE_IDS = "allowed_device_ids"
CONF_IGNORED_DEVICE_IDS = "ignored_device_ids"
CONF_DELETE_DEVICE_IDS = "delete_device_ids"
CONF_CONFIRM_DELETE = "confirm_delete"
CONF_ADD_DELETED_TO_IGNORED = "add_deleted_to_ignored"
CONF_CLEANUP_ENTITY_IDS = "cleanup_entity_ids"
CONF_CONFIRM_CLEANUP = "confirm_cleanup"

CLIENT_MODE_ALL = "all"
CLIENT_MODE_ACTIVE_ONLY = "active_only"
CLIENT_MODE_ALLOWLIST = "allowlist"
CLIENT_MODES = [CLIENT_MODE_ALL, CLIENT_MODE_ACTIVE_ONLY, CLIENT_MODE_ALLOWLIST]

DEFAULT_PORT = 8096
DEFAULT_SSL_PORT = 8920
DEFAULT_SSL = False

DATA_CLIENT = "client"
DATA_DEVICE_CACHE = "device_cache"
DATA_PYEMBY = "pyemby"
