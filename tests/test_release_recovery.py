from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import textwrap
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_release_probe_requires_both_public_assets_and_regular_release():
    probe = module("verify_published_release")
    release = {
        "tag_name": "v1.1.0",
        "name": "EMBi 1.1.0",
        "draft": False,
        "prerelease": False,
        "assets": [{"name": "embi.zip", "size": 4}, {"name": "embi.zip.sha256", "size": 4}],
    }
    assert probe.metadata_complete(release, tag="v1.1.0", version="1.1.0")
    for changes in (
        {"assets": []},
        {"assets": release["assets"][:1]},
        {"draft": True},
        {"prerelease": True},
        {"tag_name": "v1.0.0"},
    ):
        assert not probe.metadata_complete({**release, **changes}, tag="v1.1.0", version="1.1.0")


def test_release_probe_detects_wrong_contents_even_with_matching_checksum(tmp_path):
    probe = module("verify_published_release")
    component = tmp_path / "component"
    component.mkdir()
    (component / "manifest.json").write_text("reviewed contents")
    archive = tmp_path / "embi.zip"

    def build(content):
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr("manifest.json", content)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        (tmp_path / "embi.zip.sha256").write_text(f"{digest}  embi.zip\n")

    build("different contents")
    assert not probe.assets_match_source(tmp_path, component)
    build("reviewed contents")
    assert probe.assets_match_source(tmp_path, component)
    (tmp_path / "embi.zip.sha256").write_text("bad checksum")
    assert not probe.assets_match_source(tmp_path, component)


def test_reviewed_release_notes_have_no_unrelated_changelog_sections():
    notes = module("extract_release_notes")
    source = "## [Unreleased]\n\nFuture work\n\n## [1.1.0] - 2026-09-26\n\nVerständlicher Text.\n\n## [1.0.0] - 2026-01-01\n\nOlder work\n"
    assert notes.extract(source, "1.1.0") == "# EMBi 1.1.0\n\nVerständlicher Text.\n"
    with pytest.raises(ValueError):
        notes.extract(source, "9.9.9")


@pytest.mark.parametrize("ruff_failure", [False, True])
def test_autonomous_repair_stdout_is_only_sha_and_errors_never_push(tmp_path, ruff_failure):
    workflow = (ROOT / ".github/workflows/dependabot-automerge.yml").read_text()
    function = textwrap.dedent(
        workflow[
            workflow.index("          apply_deterministic_repair() {") : workflow.index(
                "          process_pr() {"
            )
        ]
    )
    # Execute the actual Bash function with controlled external command boundaries.
    stub = r"""
set -euo pipefail
GITHUB_REPOSITORY=example/example
expected_sha=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
gh() { printf 'clone output\n'; printf 'ruff==0.16.5\n' > "$4/requirements_test.txt"; }
python() { printf 'pip output\n'; }
ruff() { printf 'ruff output\n'; return "$RUFF_EXIT"; }
git() {
  shift 2
  case "$1" in
    rev-parse) printf '%s\n' "$expected_sha" ;;
    diff) return 1 ;;
    push) printf 'push output\n'; touch "$PUSH_MARKER" ;;
    *) printf 'git output\n' ;;
  esac
}
"""
    invocation = r"""
if result="$(apply_deterministic_repair 1 branch "$expected_sha")"; then
  printf '%s\n' "$result"
else
  exit 23
fi
"""
    import os

    env = {
        **os.environ,
        "RUFF_EXIT": "1" if ruff_failure else "0",
        "PUSH_MARKER": str(tmp_path / "pushed"),
    }
    result = subprocess.run(
        ["bash", "-c", stub + function + invocation],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if ruff_failure:
        assert result.returncode == 23
        assert result.stdout == ""
        assert not (tmp_path / "pushed").exists()
    else:
        assert result.returncode == 0, result.stderr
        assert result.stdout == "a" * 40 + "\n"
        assert (tmp_path / "pushed").exists()


def test_release_recovery_never_overwrites_unexpected_published_bytes(tmp_path, monkeypatch):
    probe = module("verify_published_release")
    release = {"tag_name": "v1.1.0", "assets": [{"name": "embi.zip", "size": 100}]}
    monkeypatch.setattr(probe, "get_release", lambda *_: release)

    def download(args, **kwargs):
        directory = Path(args[args.index("--dir") + 1])
        (directory / "embi.zip").write_bytes(b"unreviewed contents")
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(probe.subprocess, "run", download)
    with pytest.raises(RuntimeError, match="differs from the tag"):
        probe.verify("example/example", "v1.1.0", "1.1.0")
    release["assets"].append({"name": "unexpected.txt", "size": 1})
    with pytest.raises(RuntimeError, match="Unexpected published assets"):
        probe.verify("example/example", "v1.1.0", "1.1.0")
