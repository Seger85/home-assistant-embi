"""Protect live workflows and unfinished runs during retired-history pruning."""

import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "hygiene", Path(__file__).parents[1] / "scripts/maintain_workflow_history.py"
)
hygiene = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hygiene)


def test_only_disabled_missing_workflows_are_retired(tmp_path):
    old = {"path": ".github/workflows/old.yml", "state": "disabled_manually"}
    assert hygiene.retired(old, tmp_path)
    assert not hygiene.retired({**old, "state": "active"}, tmp_path)
    assert not hygiene.retired({**old, "path": "dynamic/dependabot/update-graph"}, tmp_path)
    assert not hygiene.retired({**old, "path": ".github/workflows/../../secret.yml"}, tmp_path)
    file = tmp_path / old["path"]
    file.parent.mkdir(parents=True)
    file.touch()
    assert not hygiene.retired(old, tmp_path)


def test_dry_run_revalidation_and_unfinished_run_protection(tmp_path):
    old = {"id": 1, "path": ".github/workflows/old.yml", "state": "disabled_manually"}

    class Api:
        def __init__(self):
            self.requests = []
            self.active = False

        def pages(self, path, key):
            if key == "workflows":
                return [old, {**old, "id": 2, "state": "active"}]
            return [
                {"id": 3, "workflow_id": 1, "status": "completed"},
                {"id": 4, "workflow_id": 1, "status": "in_progress"},
                {"id": 5, "workflow_id": 2, "status": "completed"},
            ]

        def request(self, path, method="GET"):
            self.requests.append((path, method))
            if "workflows" in path:
                return {**old, "state": "active"} if self.active else old
            return {"workflow_id": 1, "status": "completed"}

    api = Api()
    assert hygiene.prune(api, apply=False, root=tmp_path)["selected_runs"] == 1
    assert not api.requests
    api.active = True
    assert hygiene.prune(api, apply=True, root=tmp_path)["deleted_runs"] == 0
    api.active = False
    assert hygiene.prune(api, apply=True, root=tmp_path)["deleted_runs"] == 1
    assert [p for p, m in api.requests if m == "DELETE"] == ["/actions/runs/3"]
