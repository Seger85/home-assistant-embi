from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
COMPONENT_ROOT = ROOT / "custom_components"
EMBY_ROOT = COMPONENT_ROOT / "emby"

# Pure-unit tests run without installing the complete Home Assistant test
# environment. Register only the namespace and type-only modules imported by
# the pure registry evaluator.
custom_components = ModuleType("custom_components")
custom_components.__path__ = [str(COMPONENT_ROOT)]
emby_package = ModuleType("custom_components.emby")
emby_package.__path__ = [str(EMBY_ROOT)]
sys.modules.setdefault("custom_components", custom_components)
sys.modules.setdefault("custom_components.emby", emby_package)

homeassistant = ModuleType("homeassistant")
config_entries = ModuleType("homeassistant.config_entries")
core = ModuleType("homeassistant.core")
helpers = ModuleType("homeassistant.helpers")
entity_registry = ModuleType("homeassistant.helpers.entity_registry")
config_entries.ConfigEntry = object
core.HomeAssistant = object
entity_registry.EntityRegistry = object
helpers.entity_registry = entity_registry
homeassistant.config_entries = config_entries
homeassistant.core = core
homeassistant.helpers = helpers
sys.modules.setdefault("homeassistant", homeassistant)
sys.modules.setdefault("homeassistant.config_entries", config_entries)
sys.modules.setdefault("homeassistant.core", core)
sys.modules.setdefault("homeassistant.helpers", helpers)
sys.modules.setdefault("homeassistant.helpers.entity_registry", entity_registry)
