from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "embi_build_package", ROOT / "scripts/build_package.py"
)
assert SPEC is not None and SPEC.loader is not None
BUILD_PACKAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD_PACKAGE)


def test_release_archive_is_deterministic_and_installable(tmp_path: Path) -> None:
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    BUILD_PACKAGE.build_archive(first)
    BUILD_PACKAGE.build_archive(second)
    BUILD_PACKAGE.verify_archive(first, "0.9.2")
    BUILD_PACKAGE.verify_archive(second, "0.9.2")

    assert BUILD_PACKAGE.source_version() == "0.9.2"
    assert first.read_bytes() == second.read_bytes()
    assert BUILD_PACKAGE.sha256(first) == BUILD_PACKAGE.sha256(second)

    with zipfile.ZipFile(first) as archive:
        names = set(archive.namelist())
        manifest = json.loads(archive.read("manifest.json"))

    assert manifest["version"] == "0.9.2"
    assert {
        "__init__.py",
        "manifest.json",
        "strings.json",
        "translations/de.json",
        "translations/en.json",
    } <= names
    assert all(not name.startswith("custom_components/") for name in names)
    assert all(not name.startswith(("tests/", "docs/", ".github/")) for name in names)
    assert all("__pycache__" not in name for name in names)
    assert all(not name.endswith((".pyc", ".pyo")) for name in names)
