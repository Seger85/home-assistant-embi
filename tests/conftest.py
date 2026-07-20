from __future__ import annotations

import sys
from datetime import UTC, datetime
from enum import Enum, IntFlag
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
COMPONENT_ROOT = ROOT / "custom_components"
EMBY_ROOT = COMPONENT_ROOT / "emby"

custom_components = ModuleType("custom_components")
custom_components.__path__ = [str(COMPONENT_ROOT)]
emby_package = ModuleType("custom_components.emby")
emby_package.__path__ = [str(EMBY_ROOT)]
sys.modules.setdefault("custom_components", custom_components)
sys.modules.setdefault("custom_components.emby", emby_package)
custom_components.emby = emby_package

homeassistant = ModuleType("homeassistant")
components = ModuleType("homeassistant.components")
components.__path__ = []
persistent_notification = ModuleType("homeassistant.components.persistent_notification")
media_player = ModuleType("homeassistant.components.media_player")
config_entries = ModuleType("homeassistant.config_entries")
const = ModuleType("homeassistant.const")
core = ModuleType("homeassistant.core")
exceptions = ModuleType("homeassistant.exceptions")
helpers = ModuleType("homeassistant.helpers")
helpers.__path__ = []
entity_platform = ModuleType("homeassistant.helpers.entity_platform")
entity_registry = ModuleType("homeassistant.helpers.entity_registry")
event = ModuleType("homeassistant.helpers.event")
selector = ModuleType("homeassistant.helpers.selector")
aiohttp_client = ModuleType("homeassistant.helpers.aiohttp_client")
util = ModuleType("homeassistant.util")
dt = ModuleType("homeassistant.util.dt")


def callback(func):
    return func


class ConfigEntryState(Enum):
    LOADED = "loaded"
    NOT_LOADED = "not_loaded"


class OptionsFlow:
    hass = None

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    def async_show_menu(self, **kwargs):
        return {"type": "menu", **kwargs}

    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}

    def async_abort(self, **kwargs):
        return {"type": "abort", **kwargs}


class ConfigFlow:
    def __init_subclass__(cls, **kwargs):
        return super().__init_subclass__()


class _Config:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TextSelectorType:
    PASSWORD = "password"


class NumberSelectorMode:
    BOX = "box"


class SelectSelectorMode:
    DROPDOWN = "dropdown"


class _Selector:
    def __init__(self, config=None):
        self.config = config

    def __call__(self, value):
        return value


class MediaPlayerEntityFeature(IntFlag):
    PAUSE = 1
    PREVIOUS_TRACK = 2
    NEXT_TRACK = 4
    STOP = 8
    SEEK = 16
    PLAY = 32


class MediaPlayerState(Enum):
    PAUSED = "paused"
    PLAYING = "playing"
    IDLE = "idle"
    OFF = "off"


class MediaType(Enum):
    TVSHOW = "tvshow"
    MOVIE = "movie"
    MUSIC = "music"
    VIDEO = "video"
    CHANNEL = "channel"


class MediaPlayerEntity:
    hass = None

    @property
    def unique_id(self):
        return getattr(self, "_attr_unique_id", None)

    async def async_added_to_hass(self) -> None:
        return None

    async def async_remove(self, *, force_remove: bool = False) -> None:
        return None


selector.TextSelector = _Selector
selector.NumberSelector = _Selector
selector.BooleanSelector = _Selector
selector.SelectSelector = _Selector
selector.TextSelectorConfig = _Config
selector.NumberSelectorConfig = _Config
selector.SelectSelectorConfig = _Config
selector.TextSelectorType = TextSelectorType
selector.NumberSelectorMode = NumberSelectorMode
selector.SelectSelectorMode = SelectSelectorMode

media_player.MediaPlayerEntity = MediaPlayerEntity
media_player.MediaPlayerEntityFeature = MediaPlayerEntityFeature
media_player.MediaPlayerState = MediaPlayerState
media_player.MediaType = MediaType
entity_platform.AddEntitiesCallback = object

config_entries.ConfigEntry = object
config_entries.ConfigEntryState = ConfigEntryState
config_entries.OptionsFlow = OptionsFlow
config_entries.ConfigFlow = ConfigFlow
core.HomeAssistant = object
core.callback = callback
exceptions.ConfigEntryAuthFailed = RuntimeError
exceptions.ConfigEntryNotReady = RuntimeError
entity_registry.EntityRegistry = object
entity_registry.async_get = lambda hass: hass.registry
helpers.entity_platform = entity_platform
helpers.entity_registry = entity_registry
helpers.selector = selector
event.async_track_point_in_utc_time = lambda hass, action, point: lambda: None
aiohttp_client.async_get_clientsession = lambda hass: None

persistent_notification.async_create = lambda hass, message, **kwargs: hass.notifications.append(
    ("create", message, kwargs)
)
persistent_notification.async_dismiss = lambda hass, notification_id: hass.notifications.append(
    ("dismiss", notification_id, {})
)
components.media_player = media_player
components.persistent_notification = persistent_notification

for name in (
    "CONF_API_KEY",
    "CONF_HOST",
    "CONF_NAME",
    "CONF_PORT",
    "CONF_SSL",
    "DEVICE_DEFAULT_NAME",
):
    setattr(const, name, name.lower())

dt.utcnow = lambda: datetime.now(UTC)
dt.as_local = lambda value: value
util.dt = dt

homeassistant.components = components
homeassistant.config_entries = config_entries
homeassistant.const = const
homeassistant.core = core
homeassistant.exceptions = exceptions
homeassistant.helpers = helpers
homeassistant.util = util

modules = {
    "homeassistant": homeassistant,
    "homeassistant.components": components,
    "homeassistant.components.media_player": media_player,
    "homeassistant.components.persistent_notification": persistent_notification,
    "homeassistant.config_entries": config_entries,
    "homeassistant.const": const,
    "homeassistant.core": core,
    "homeassistant.exceptions": exceptions,
    "homeassistant.helpers": helpers,
    "homeassistant.helpers.entity_platform": entity_platform,
    "homeassistant.helpers.entity_registry": entity_registry,
    "homeassistant.helpers.event": event,
    "homeassistant.helpers.selector": selector,
    "homeassistant.helpers.aiohttp_client": aiohttp_client,
    "homeassistant.util": util,
    "homeassistant.util.dt": dt,
}
for name, module in modules.items():
    sys.modules.setdefault(name, module)


def pytest_configure(config):
    config.addinivalue_line("markers", "runtime: isolated EMBi runtime contract test")
