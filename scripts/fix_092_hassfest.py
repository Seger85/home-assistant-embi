from __future__ import annotations

import json
from pathlib import Path

FILES = (
    Path("custom_components/emby/strings.json"),
    Path("custom_components/emby/translations/en.json"),
    Path("custom_components/emby/translations/de.json"),
)

for path in FILES:
    data = json.loads(path.read_text(encoding="utf-8"))
    descriptions = data["options"]["step"]["ha_players"].get("data_description", {})
    descriptions.pop("back", None)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
