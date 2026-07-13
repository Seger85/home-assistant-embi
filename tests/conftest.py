from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
COMPONENT_ROOT = ROOT / "custom_components"
EMBY_ROOT = COMPONENT_ROOT / "emby"

# Unit tests for the pure EMBi modules run without installing the complete
# Home Assistant test environment. Pre-register the namespace package so
# importing custom_components.emby.api does not execute integration __init__.py.
custom_components = ModuleType("custom_components")
custom_components.__path__ = [str(COMPONENT_ROOT)]
emby_package = ModuleType("custom_components.emby")
emby_package.__path__ = [str(EMBY_ROOT)]

sys.modules.setdefault("custom_components", custom_components)
sys.modules.setdefault("custom_components.emby", emby_package)
