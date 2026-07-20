from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_temporary_implementation_workflows_remain() -> None:
    temporary = sorted(path.name for path in (ROOT / ".github" / "workflows").glob("embi-09-*.yml"))
    assert temporary == []
