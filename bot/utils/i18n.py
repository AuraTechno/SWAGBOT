import json
from pathlib import Path

_LOCALIZATIONS: dict[str, dict] = {}
_LOCALE_DIR = Path(__file__).resolve().parent.parent / "localization"


def load_localizations():
    for file in _LOCALE_DIR.glob("*.json"):
        lang = file.stem
        with open(file, "r", encoding="utf-8") as f:
            _LOCALIZATIONS[lang] = json.load(f)


def _(key: str, lang: str = "ru", **kwargs) -> str:
    parts = key.split(".")
    value = _LOCALIZATIONS.get(lang, _LOCALIZATIONS.get("ru", {}))
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part, f"{{{key}}}")
        else:
            return f"{{{key}}}"
    if kwargs:
        value = str(value).format(**kwargs)
    return value
