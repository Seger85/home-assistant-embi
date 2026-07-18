from __future__ import annotations

from pathlib import Path

path = Path("tests/test_options_flow.py")
text = path.read_text(encoding="utf-8")
old = '    assert result["type"] == "menu"\n    assert result["step_id"] == "review_changes"\n'
new = '    assert result["type"] == "form"\n    assert result["step_id"] == "review_changes"\n'
if text.count(old) != 1:
    raise SystemExit("Unexpected unchanged-apply assertion shape")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
