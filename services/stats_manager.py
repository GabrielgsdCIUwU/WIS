"""
services/stats_manager.py
-------------------------
Helper for loading external theme files (.wistheme / .json).
"""

import json
import os
from typing import Dict

from core.config import COLOR_KEYS


def load_themes_from_folder(folder: str) -> Dict[str, Dict[str, str]]:
    """Scan a folder for .wistheme / .json files and return valid theme dicts keyed by name."""
    themes: Dict[str, Dict[str, str]] = {}
    if not folder or not os.path.isdir(folder):
        return themes
    for entry in sorted(os.scandir(folder), key=lambda e: e.name.lower()):
        if not entry.is_file():
            continue
        ext = os.path.splitext(entry.name)[1].lower()
        if ext not in (".wistheme", ".json"):
            continue
        try:
            with open(entry.path) as f:
                data = json.load(f)
            if not data.get("wis_theme"):
                continue
            colors = {
                k: v for k, v in data.get("colors", {}).items()
                if k in COLOR_KEYS and isinstance(v, str)
                and v.startswith("#") and len(v) == 7
            }
            if not colors:
                continue
            name = data.get("name") or os.path.splitext(entry.name)[0]
            themes[name] = colors
        except Exception:
            continue
    return themes
