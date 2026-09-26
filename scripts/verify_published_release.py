"""Read-only release probe: 0 complete, 1 repair needed, 2 unable to verify safely."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"


def metadata_complete(data: dict, *, tag: str, version: str) -> bool:
    return bool(
        data.get("tag_name") == tag
        and data.get("name") == f"EMBi {version}"
        and data.get("draft") is False
        and data.get("prerelease") is False
        and len(data.get("assets", [])) == 2
        and {item.get("name") for item in data.get("assets", [])} == {"embi.zip", "embi.zip.sha256"}
        and all(item.get("size", 0) > 0 for item in data["assets"])
    )


def archive_matches_source(archive: Path, component: Path = COMPONENT) -> bool:
    """Check exact files without relying on a compression implementation."""
    expected = {
        path.relative_to(component).as_posix(): path.read_bytes()
        for path in component.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    }
    try:
        with zipfile.ZipFile(archive) as package:
            if (
                len(package.namelist()) != len(expected)
                or set(package.namelist()) != expected.keys()
            ):
                return False
            return all(package.read(name) == content for name, content in expected.items())
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError):
        return False


def assets_match_source(directory: Path, component: Path = COMPONENT) -> bool:
    """Verify checksum and exact file contents, independently of ZIP compression."""
    archive = directory / "embi.zip"
    try:
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        return (
            directory / "embi.zip.sha256"
        ).read_text().strip() == f"{digest}  embi.zip" and archive_matches_source(
            archive, component
        )
    except OSError:
        return False


def get_release(repo: str, path: str) -> dict | None:
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/releases/{path}"], capture_output=True, text=True, check=False
    )
    if result.returncode:
        if "HTTP 404" in result.stderr:
            return None
        raise RuntimeError("GitHub release metadata could not be read")
    return json.loads(result.stdout)


def verify(repo: str, tag: str, version: str) -> bool:
    release = get_release(repo, f"tags/{tag}")
    if release is None:
        return False
    names = [item.get("name") for item in release.get("assets", [])]
    if len(names) != len(set(names)) or set(names) - {"embi.zip", "embi.zip.sha256"}:
        raise RuntimeError("Unexpected published assets; refusing automatic replacement")
    if not names:
        return False
    with tempfile.TemporaryDirectory(prefix="embi-release-check-") as directory:
        result = subprocess.run(
            [
                "gh",
                "release",
                "download",
                tag,
                "--repo",
                repo,
                "--dir",
                directory,
                *[argument for name in names for argument in ("--pattern", name)],
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError("Published release assets could not be downloaded")
        downloaded = Path(directory)
        archive = downloaded / "embi.zip"
        if "embi.zip" in names and not archive_matches_source(archive):
            raise RuntimeError("Published package differs from the tag; refusing replacement")
        if "embi.zip.sha256" in names:
            if "embi.zip" not in names:
                # A checksum-only partial upload can be compared to our deterministic
                # package without modifying either the tag or the existing asset.
                expected = downloaded / "expected"
                commit = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip()
                subprocess.run(
                    [
                        sys.executable,
                        "-I",
                        str(ROOT / "scripts/build_package.py"),
                        "--output-dir",
                        str(expected),
                        "--expected-version",
                        version,
                        "--commit",
                        commit,
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    check=True,
                )
                archive = expected / "embi.zip"
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            if (downloaded / "embi.zip.sha256").read_text().strip() != f"{digest}  embi.zip":
                raise RuntimeError("Published checksum differs; refusing automatic replacement")
    latest = get_release(repo, "latest")
    return bool(
        metadata_complete(release, tag=tag, version=version)
        and latest
        and latest.get("tag_name") == tag
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY"),
        required=not os.environ.get("GITHUB_REPOSITORY"),
    )
    parser.add_argument("--tag", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    try:
        complete = verify(args.repo, args.tag, args.version)
    except (RuntimeError, ValueError, OSError, subprocess.CalledProcessError):
        print("Release verification could not finish; publication remains unchanged.")
        raise SystemExit(2) from None
    raise SystemExit(0 if complete else 1)


if __name__ == "__main__":
    main()
