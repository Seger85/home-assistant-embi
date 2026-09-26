"""Prune completed runs belonging only to retired, disabled workflows.

Active workflows, existing YAML files, dynamic GitHub workflows and unfinished
runs are never removed. Source commits, tags and releases are not modified.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path, PurePosixPath
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def retired(workflow: dict, root: Path = ROOT) -> bool:
    path = workflow.get("path", "")
    parts = PurePosixPath(path).parts
    return bool(
        workflow.get("state") == "disabled_manually"
        and len(parts) == 3
        and parts[:2] == (".github", "workflows")
        and parts[2].endswith((".yml", ".yaml"))
        and not (root / path).exists()
    )


class GitHub:
    def __init__(self, repo: str, token: str):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("Invalid repository")
        self.base = f"https://api.github.com/repos/{repo}"
        self.headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    def request(self, path: str, method: str = "GET"):
        with urlopen(
            Request(self.base + path, headers=self.headers, method=method), timeout=30
        ) as response:
            content = response.read()
            return json.loads(content) if content else None

    def pages(self, path: str, key: str) -> list[dict]:
        result = []
        for page in range(1, 101):
            items = self.request(f"{path}?per_page=100&page={page}")[key]
            result.extend(items)
            if len(items) < 100:
                return result
        raise RuntimeError("Inventory exceeds safe pagination limit")


def prune(api: GitHub, *, apply: bool, root: Path = ROOT) -> dict:
    workflows = [
        item for item in api.pages("/actions/workflows", "workflows") if retired(item, root)
    ]
    deleted = selected = 0
    for workflow in workflows:
        wid = int(workflow["id"])
        # Take a complete page snapshot before deleting: no shifted pagination.
        runs = api.pages(f"/actions/workflows/{wid}/runs", "workflow_runs")
        for run in runs:
            if run.get("workflow_id") != wid or run.get("status") != "completed":
                continue
            selected += 1
            if apply:
                # Recheck current workflow/run state directly before each mutation.
                if not retired(api.request(f"/actions/workflows/{wid}"), root):
                    break
                rid = int(run["id"])
                current = api.request(f"/actions/runs/{rid}")
                if current.get("workflow_id") != wid or current.get("status") != "completed":
                    continue
                api.request(f"/actions/runs/{rid}", "DELETE")
                deleted += 1
                print(f"Removed completed retired-workflow run {rid}", flush=True)
    return {
        "retired_workflows": len(workflows),
        "selected_runs": selected,
        "deleted_runs": deleted,
        "applied": apply,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise SystemExit("Run only from protected main")
    api = GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GH_TOKEN"])
    print(json.dumps(prune(api, apply=args.apply)))


if __name__ == "__main__":
    main()
