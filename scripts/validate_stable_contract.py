from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "emby"
EXPECTED_VERSION = "0.3.0"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    constants = (COMPONENT / "const.py").read_text(encoding="utf-8")
    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    english = json.loads((COMPONENT / "translations" / "en.json").read_text(encoding="utf-8"))
    german = json.loads((COMPONENT / "translations" / "de.json").read_text(encoding="utf-8"))
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))

    match = re.search(r'^VERSION = "([^"]+)"$', constants, re.MULTILINE)
    require(match is not None, "const.py VERSION must be a literal")
    require(manifest.get("version") == EXPECTED_VERSION, "Manifest is not stable 0.3.0")
    require(match.group(1) == EXPECTED_VERSION, "const.py is not stable 0.3.0")
    require(strings == english, "strings.json and translations/en.json differ")
    require(set(strings) == set(german), "German top-level translation sections differ")
    require(hacs.get("zip_release") is True, "hacs.json must enable zip_release")
    require(hacs.get("filename") == "embi.zip", "hacs.json must select embi.zip")
    require(hacs.get("hide_default_branch") is True, "Default-branch fallback must be hidden")

    component_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in COMPONENT.rglob("*")
        if path.is_file() and path.suffix in {".py", ".json"}
    )
    for forbidden_constant in (
        "CONF_SERVER_CLEANUP_API_KEY",
        "CONF_AUTO_CLEANUP_CONFIRMATION_TEXT",
        "CONF_ADD_DELETED_TO_IGNORED",
    ):
        require(
            forbidden_constant not in component_text,
            f"Obsolete constant remains: {forbidden_constant}",
        )
    for forbidden_ui_text in ("AUTOMATISCH LÖSCHEN", "ENABLE AUTO DELETE"):
        require(
            forbidden_ui_text not in component_text,
            f"Typed activation phrase remains: {forbidden_ui_text}",
        )

    require('PLATFORMS = ["media_player"]' in constants, "Stable must expose only media_player")
    require(
        "Store(" in (COMPONENT / "maintenance_store.py").read_text(), "Persistent Store is missing"
    )
    require(
        "OptionsDraft.from_options" in (COMPONENT / "options_flow.py").read_text(),
        "Options draft is missing",
    )
    print("Stable 0.3.0 repository contract passed")


if __name__ == "__main__":
    main()
