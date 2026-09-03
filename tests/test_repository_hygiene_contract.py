from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def test_validation_push_triggers_are_main_only() -> None:
    for name in ("quality.yml", "hacs.yml", "hassfest.yml"):
        workflow = (WORKFLOWS / name).read_text(encoding="utf-8")
        push_block = workflow.split("  pull_request:", 1)[0]
        assert "      - main" in push_block
        assert "      - develop" not in push_block
