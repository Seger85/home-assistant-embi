from pathlib import Path

path = Path("custom_components/emby/options_flow.py")
text = path.read_text(encoding="utf-8")
broken = '                "changes": "\n\n".join(lines) or "-",'
fixed = '                "changes": "\\n\\n".join(lines) or "-",'
if broken not in text:
    raise SystemExit("broken options-flow join expression not found")
path.write_text(text.replace(broken, fixed, 1), encoding="utf-8")

print("EMBi 0.9.2 CI syntax correction applied")
