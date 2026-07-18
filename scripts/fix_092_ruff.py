from __future__ import annotations

import subprocess
from pathlib import Path

FILES = (
    Path("custom_components/emby/options_cleanup.py"),
    Path("custom_components/emby/options_flow.py"),
    Path("custom_components/emby/options_ha_cleanup.py"),
    Path("custom_components/emby/options_navigation.py"),
)

for path in FILES:
    text = path.read_text(encoding="utf-8")
    text = text.replace("‹", "\\u2039")
    path.write_text(text, encoding="utf-8")

subprocess.run(
    ["ruff", "check", "--fix", *(str(path) for path in FILES)],
    check=True,
)
subprocess.run(
    ["ruff", "format", *(str(path) for path in FILES)],
    check=True,
)
