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
    assert MODULE.manifest_version() == "1.0.1"
    assert MODULE.constant_version() == "1.0.1"


def test_every_build_workflow_resolves_version_before_dependencies() -> None:
    for name in ("quality.yml", "test-artifact.yml", "release.yml"):
        workflow = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        setup = workflow.index("actions/setup-python@")
        version = workflow.index("scripts/read_version.py")
        install = workflow.index("pip install")
        assert setup < version < install
        assert "from custom_components.emby" not in workflow
        assert "python -c 'import json" not in workflow
        assert 'python -c "from custom_components.emby' not in workflow
        assert "validate_legacy_migration_contract.py" in workflow


def test_stable_publisher_is_single_sha_bound_regular_latest_release() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "pull_request:" in workflow and "closed" in workflow
    assert "release_sha" in workflow and "MERGE_SHA" in workflow
    assert "git tag -a" in workflow
    assert "prerelease: false" in workflow
    assert "draft: false" in workflow
    assert "make_latest: true" in workflow
    assert "gh release download" in workflow
    assert "cmp dist/embi.zip" in workflow
    assert "cancel-in-progress: false" in workflow
