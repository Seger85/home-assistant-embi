from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "emby"

for name in ("strings.json", "translations/en.json", "translations/de.json"):
    path = ROOT / name
    data = json.loads(path.read_text(encoding="utf-8"))
    descriptions = data["options"]["step"]["ha_players"].get("data_description", {})
    descriptions.pop("back", None)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
