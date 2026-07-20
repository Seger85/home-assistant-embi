#!/usr/bin/env python3
"""Validate the frozen historical upgrade contract used by legacy migration."""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "specs" / "0.9.0"
REQ = SPEC / "requirements.yaml"

REQUIRED_FILES = [
    "README.md",
    "00-master-specification.md",
    "01-domain-and-state-model.md",
    "02-devices-and-players.md",
    "03-cleanup.md",
    "04-options-flow-and-navigation.md",
    "05-ui-copy-de.md",
    "06-ui-copy-en.md",
    "07-migration-from-0.3.0.md",
    "08-security-and-safety-contract.md",
    "09-diagnostics-and-logging.md",
    "10-test-and-acceptance-matrix.md",
    "11-release-contract.md",
    "12-data-model-and-persistence.md",
    "13-documentation-and-community.md",
    "requirements.yaml",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


for name in REQUIRED_FILES:
    path = SPEC / name
    if not path.is_file():
        fail(f"missing required legacy fixture: {path.relative_to(ROOT)}")
    if path.stat().st_size == 0:
        fail(f"empty required legacy fixture: {path.relative_to(ROOT)}")

data = yaml.safe_load(REQ.read_text(encoding="utf-8"))
if data.get("version") != "0.9.0":
    fail("historical fixture version must remain 0.9.0")
if data.get("status") != "frozen":
    fail("historical fixture status must remain frozen")
if data.get("release_type") != "stable":
    fail("historical fixture release_type must remain stable")

requirements = data.get("requirements")
if not isinstance(requirements, list) or not requirements:
    fail("requirements list missing or empty")

ids = [item.get("id") for item in requirements]
if any(not requirement_id for requirement_id in ids):
    fail("every requirement needs an id")
if len(ids) != len(set(ids)):
    fail("requirement IDs must be unique")

required_keys = {
    "id",
    "area",
    "priority",
    "summary",
    "automated_test_required",
    "live_verification_required",
    "visual_verification_required",
}
for item in requirements:
    missing = required_keys - set(item)
    if missing:
        fail(f"{item.get('id')} missing keys: {sorted(missing)}")
    if item["priority"] == "blocker" and not item["automated_test_required"]:
        fail(f"blocker {item['id']} must require an automated test")

print(f"Validated frozen legacy migration contract: {len(requirements)} requirements.")
