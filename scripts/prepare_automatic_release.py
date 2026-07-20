from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"
CHANGELOG = ROOT / "CHANGELOG.md"

VERSION_TEXT_FILES = (
    COMPONENT / "const.py",
    ROOT / "scripts" / "validate_repository_references.py",
    ROOT / "scripts" / "validate_stable_contract.py",
    ROOT / "tests" / "test_release_identity.py",
    ROOT / "tests" / "test_repository_contract.py",
)


def _parse_version(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", value)
    if match is None:
        raise RuntimeError(f"Unsupported semantic version: {value}")
    return tuple(int(part) for part in match.groups())


def _manifest_version() -> str:
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    version = manifest.get("version")
    if not isinstance(version, str):
        raise RuntimeError("manifest.json does not contain a string version")
    return version


def _constant_version() -> str:
    constants = (COMPONENT / "const.py").read_text(encoding="utf-8")
    match = re.search(
        r'^VERSION = "([0-9]+\.[0-9]+\.[0-9]+)"$', constants, re.MULTILINE
    )
    if match is None:
        raise RuntimeError("const.py does not contain the canonical VERSION assignment")
    return match.group(1)


def _replace_exact_version(path: Path, current: str, target: str) -> None:
    content = path.read_text(encoding="utf-8")
    occurrences = content.count(current)
    if occurrences == 0:
        raise RuntimeError(f"{path.relative_to(ROOT)} does not reference {current}")
    path.write_text(content.replace(current, target), encoding="utf-8")


def _update_manifest(current: str, target: str) -> None:
    path = COMPONENT / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("version") != current:
        raise RuntimeError("manifest version changed during release preparation")
    manifest["version"] = target
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _update_changelog(current: str, target: str) -> None:
    content = CHANGELOG.read_text(encoding="utf-8")
    marker = "## [Unreleased]\n\nNo unreleased product changes.\n\n"
    if marker not in content:
        raise RuntimeError("Unreleased changelog marker differs")
    if f"## [{target}]" in content:
        raise RuntimeError(f"Changelog already contains {target}")

    date = datetime.now(UTC).date().isoformat()
    section = (
        f"## [{target}] - {date}\n\n"
        f"- Publish all validated repository changes since v{current} through the autonomous "
        "dependency and stable-release pipeline.\n\n"
    )
    CHANGELOG.write_text(content.replace(marker, marker + section, 1), encoding="utf-8")


def prepare(expected_current: str) -> str:
    manifest_version = _manifest_version()
    constant_version = _constant_version()
    if manifest_version != expected_current or constant_version != expected_current:
        raise RuntimeError(
            "Current version differs: "
            f"manifest={manifest_version}, const={constant_version}, expected={expected_current}"
        )

    major, minor, patch = _parse_version(expected_current)
    target = f"{major}.{minor}.{patch + 1}"

    _update_manifest(expected_current, target)
    for path in VERSION_TEXT_FILES:
        _replace_exact_version(path, expected_current, target)
    _update_changelog(expected_current, target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-current", required=True)
    args = parser.parse_args()
    print(prepare(args.expected_current))


if __name__ == "__main__":
    main()
