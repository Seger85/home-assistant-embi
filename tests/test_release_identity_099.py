from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "read_version.py"
SPEC = importlib.util.spec_from_file_location("embi_read_version", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_dependency_free_version_reader_matches_repository() -> None:
    assert MODULE.manifest_version() == "0.9.9"
    assert MODULE.constant_version() == "0.9.9"


def test_stable_workflow_avoids_known_release_failures() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "from custom_components.emby.const import VERSION" not in workflow
    assert "python scripts/read_version.py" in workflow
    assert "FETCH_HEAD" in workflow
    assert "origin/main" not in workflow
    assert "pull_request:" in workflow and "closed" in workflow
    assert "workflow_dispatch:" in workflow
