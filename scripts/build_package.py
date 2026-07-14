from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"
_FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def source_version() -> str:
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    constants = (COMPONENT / "const.py").read_text(encoding="utf-8")
    match = re.search(r'^VERSION = "([^"]+)"$', constants, re.MULTILINE)
    if match is None:
        raise RuntimeError("const.py does not expose a literal VERSION")
    if manifest.get("version") != match.group(1):
        raise RuntimeError(
            f"Manifest and const.py versions differ: {manifest.get('version')!r} != {match.group(1)!r}"
        )
    return match.group(1)


def component_files() -> list[Path]:
    return [
        path
        for path in sorted(COMPONENT.rglob("*"))
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    ]


def build_archive(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in component_files():
            relative = path.relative_to(COMPONENT).as_posix()
            info = zipfile.ZipInfo(relative, date_time=_FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def verify_archive(archive_path: Path, expected_version: str) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        required = {
            "__init__.py",
            "manifest.json",
            "strings.json",
            "translations/de.json",
            "translations/en.json",
        }
        missing = sorted(required - names)
        if missing:
            raise RuntimeError(f"Archive misses required files: {missing}")
        forbidden = [
            name
            for name in names
            if name.startswith("tests/")
            or name.startswith("docs/")
            or name.startswith(".github/")
            or "__pycache__" in name
            or name.endswith((".pyc", ".pyo"))
        ]
        if forbidden:
            raise RuntimeError(f"Archive contains forbidden files: {forbidden}")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("version") != expected_version:
            raise RuntimeError(
                "Packaged manifest version does not match expected version: "
                f"{manifest.get('version')!r} != {expected_version!r}"
            )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the deterministic EMBi integration archive")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--expected-version")
    parser.add_argument("--commit")
    args = parser.parse_args()

    version = source_version()
    if args.expected_version and version != args.expected_version:
        raise RuntimeError(f"Source version {version!r} does not match {args.expected_version!r}")

    output_dir = args.output_dir.resolve()
    archive_path = output_dir / "embi.zip"
    build_archive(archive_path)
    verify_archive(archive_path, version)
    digest = sha256(archive_path)
    (output_dir / "embi.zip.sha256").write_text(f"{digest}  embi.zip\n", encoding="utf-8")
    if args.commit:
        (output_dir / "BUILD_COMMIT").write_text(f"{args.commit}\n", encoding="utf-8")
    print(f"Built {archive_path} ({version})")
    print(f"SHA-256 {digest}")


if __name__ == "__main__":
    main()
