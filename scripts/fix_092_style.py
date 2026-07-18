from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for path in (ROOT / "custom_components" / "emby").glob("*.py"):
    text = path.read_text(encoding="utf-8")
    updated = text.replace("‹ Zurück", "\\u2039 Zurück").replace("‹ Back", "\\u2039 Back")
    if updated != text:
        path.write_text(updated, encoding="utf-8")
