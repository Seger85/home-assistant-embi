"""Publish the reviewed, human-readable changelog section as release notes."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def extract(content: str, version: str) -> str:
    match = re.search(
        rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}\s*\n(.*?)(?=^## |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if match is None or not match.group(1).strip():
        raise ValueError("The reviewed release notes are missing")
    return f"# EMBi {version}\n\n{match.group(1).strip()}\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    notes = extract((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), args.version)
    args.output.write_text(notes, encoding="utf-8")


if __name__ == "__main__":
    main()
