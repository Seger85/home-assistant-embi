from pathlib import Path

root = Path(__file__).resolve().parents[1]

path = root / "custom_components/emby/options_cleanup.py"
text = path.read_text(encoding="utf-8").replace(
    "Alle sicheren Einträge – unabhängig vom Alter",
    "Alle sicheren Einträge - unabhängig vom Alter",
).replace(
    "All safe records – regardless of age",
    "All safe records - regardless of age",
)
path.write_text(text, encoding="utf-8")

path = root / "custom_components/emby/options_devices.py"
text = path.read_text(encoding="utf-8")
needle = "    CLIENT_CLASS_TECHNICAL,\n    GROUP_USER_PREFIX,\n"
replacement = "    CLIENT_CLASS_TECHNICAL,\n    GROUP_TECHNICAL,\n    GROUP_USER_PREFIX,\n"
if needle not in text:
    raise RuntimeError("GROUP_TECHNICAL import insertion point not found")
path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")

path = root / "tests/test_options_flow_093.py"
text = path.read_text(encoding="utf-8")
text = text.replace(
    "from datetime import UTC, datetime\n",
    "from datetime import UTC, datetime\nfrom pathlib import Path\n",
    1,
)
text = text.replace(
    'source = open("custom_components/emby/maintenance_cycle_execute.py", encoding="utf-8").read()',
    'source = Path("custom_components/emby/maintenance_cycle_execute.py").read_text(encoding="utf-8")',
)
text = text.replace(
    'flow = open("custom_components/emby/options_flow.py", encoding="utf-8").read()',
    'flow = Path("custom_components/emby/options_flow.py").read_text(encoding="utf-8")',
)
text = text.replace(
    'devices = open("custom_components/emby/options_devices.py", encoding="utf-8").read()',
    'devices = Path("custom_components/emby/options_devices.py").read_text(encoding="utf-8")',
)
path.write_text(text, encoding="utf-8")
