from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {".git", ".pytest_cache", ".ruff_cache", "dist", "__pycache__"}
TEXT_SUFFIXES = {".py", ".json", ".md", ".yml", ".yaml", ".toml", ".txt"}

PATTERNS = {
    "Home Assistant long-lived token": re.compile(r"eyJ[A-Za-z0-9_-]{30,}\.[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "private IPv4 address": re.compile(
        r"(?<![0-9])(?:10\.(?:\d{1,3}\.){2}\d{1,3}|192\.168\.(?:\d{1,3}\.)\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3})(?![0-9])"
    ),
    "live config-entry identifier": re.compile(r"\b01[A-HJKMNP-TV-Z0-9]{24}\b"),
}


def files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower() in TEXT_SUFFIXES
        and not EXCLUDED_DIRS.intersection(path.parts)
    ]


def main() -> None:
    failures: list[str] = []
    for path in files():
        text = path.read_text(encoding="utf-8")
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                failures.append(f"{path.relative_to(ROOT)}:{line}: {label}")
    if failures:
        raise SystemExit("Potential private data detected:\n" + "\n".join(failures))
    print(f"Secret/privacy scan passed for {len(files())} text files")


if __name__ == "__main__":
    main()
