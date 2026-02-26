"""
core/config.py
--------------
Global constants, theme definitions, SettingsStore and StatisticsStore.
"""

import os
import time
import json
from collections import defaultdict, Counter
from datetime import datetime
from threading import Thread
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

# ── Optional audio ────────────────────────────────────────────────────────────
try:
    import pygame
    pygame.mixer.init()
    _PYGAME_OK = True
except Exception:
    _PYGAME_OK = False

def get_app_data_dir():
    """Get writable app data directory (works with .exe and frozen apps)"""
    if os.name == 'nt':  # Windows
        app_data = Path(os.getenv('APPDATA')) / 'WIS'
    else:  # Linux/macOS
        app_data = Path.home() / '.wis'
    
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data

# Set up paths for JSON files
APP_DATA_DIR = get_app_data_dir()
SETTINGS_FILE = APP_DATA_DIR / 'wis_settings.json'
STATS_FILE = APP_DATA_DIR / 'wis_stats.json'

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Module-level log icon map ─────────────────────────────────────────────────
_LOG_ICONS: Dict[str, str] = {
    "ok": "✓", "err": "✗", "warn": "!", "info": "·", "debug": ">",
}

# ─────────────────────────────────────────────────────────────────────────────
#  DEFAULTS & THEMES
# ─────────────────────────────────────────────────────────────────────────────

DEFAULTS: Dict[str, Any] = {
    "bg": "#0f1117", "bg2": "#181c26", "bg3": "#1f2433",
    "accent": "#4f8ef7", "accent2": "#2ecc8f", "danger": "#e05252",
    "warning": "#f0a500", "fg": "#d6dce8", "fg2": "#7a8499", "border": "#2a3045",
    "scan_rate": 15.0, "send_timeout": 15, "file_delay": 0.8,
    "formats": ".jpg,.jpeg,.png,.gif,.bmp,.webp",
    "sound_enabled": True, "sound_volume": 0.8,
    "theme_folder": "",
}

COLOR_KEYS: List[str] = [
    "bg", "bg2", "bg3", "accent", "accent2", "danger", "warning", "fg", "fg2", "border",
]

THEME_PRESETS: Dict[str, Dict[str, str]] = {
    "Dark Blue (default)": {
        "bg": "#0f1117", "bg2": "#181c26", "bg3": "#1f2433",
        "accent": "#4f8ef7", "accent2": "#2ecc8f", "danger": "#e05252",
        "warning": "#f0a500", "fg": "#d6dce8", "fg2": "#7a8499", "border": "#2a3045",
    },
    "Nord": {
        "bg": "#2e3440", "bg2": "#3b4252", "bg3": "#434c5e",
        "accent": "#81a1c1", "accent2": "#a3be8c", "danger": "#bf616a",
        "warning": "#ebcb8b", "fg": "#eceff4", "fg2": "#9099a6", "border": "#4c566a",
    },
    "Dracula": {
        "bg": "#282a36", "bg2": "#313341", "bg3": "#383a4a",
        "accent": "#bd93f9", "accent2": "#50fa7b", "danger": "#ff5555",
        "warning": "#f1fa8c", "fg": "#f8f8f2", "fg2": "#9099a6", "border": "#44475a",
    },
    "Light": {
        "bg": "#f0f2f7", "bg2": "#ffffff", "bg3": "#e4e7ef",
        "accent": "#2563eb", "accent2": "#16a34a", "danger": "#dc2626",
        "warning": "#d97706", "fg": "#1e293b", "fg2": "#64748b", "border": "#cbd5e1",
    },
}

# Live color dict — mutated when settings change
C: Dict[str, Any] = dict(DEFAULTS)


# ─────────────────────────────────────────────────────────────────────────────
#  SETTINGS STORE
# ─────────────────────────────────────────────────────────────────────────────

class SettingsStore:
    def __init__(self, path: str):
        self._path = path
        self.webhooks:        List[dict]    = []
        self.folders:         List[dict]    = []
        self.auto_start:      bool          = False
        self.debug_mode:      bool          = False
        self.custom_themes:   Dict          = {}
        self.shared_profiles: List[dict]    = []
        self.values:          Dict[str, Any] = dict(DEFAULTS)
        self.stats_config:    Dict = {
            "max_sends": 10000, "max_errors": 2000,
            "months": 12, "autosave_every": 10,
        }

    def load(self) -> None:
        try:
            if not os.path.exists(self._path):
                return
            with open(self._path) as f:
                s = json.load(f)
            self.webhooks        = s.get("webhooks",         [])
            self.folders         = s.get("folders",          [])
            self.auto_start      = s.get("auto_start",       False)
            self.debug_mode      = s.get("debug_mode",       False)
            self.custom_themes   = s.get("custom_themes",    {})
            self.shared_profiles = s.get("shared_profiles",  [])
            self.values.update({k: s[k] for k in DEFAULTS if k in s})
            sc = s.get("stats_config", {})
            self.stats_config.update({k: sc[k] for k in self.stats_config if k in sc})
            if not self.webhooks and s.get("webhook_url"):
                self.webhooks = [{"name": "Default", "url": s["webhook_url"], "enabled": True}]
            if not self.folders and s.get("folder_path"):
                self.folders = [{"path": s["folder_path"], "enabled": True, "recursive": False}]
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save(self) -> None:
        try:
            data = {
                "webhooks": self.webhooks, "folders": self.folders,
                "auto_start": self.auto_start, "debug_mode": self.debug_mode,
                "stats_config": self.stats_config, "custom_themes": self.custom_themes,
                "shared_profiles": self.shared_profiles,
            }
            data.update(self.values)
            with open(self._path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")


# ─────────────────────────────────────────────────────────────────────────────
#  STATISTICS STORE
# ─────────────────────────────────────────────────────────────────────────────

class StatisticsStore:
    def __init__(self, path: str, config: Dict):
        self._path   = path
        self._config = config
        self.sends:  List[dict] = []
        self.errors: List[dict] = []

    def load(self) -> None:
        try:
            if os.path.exists(self._path):
                with open(self._path) as f:
                    data = json.load(f)
                self.sends  = data.get("sends",  [])
                self.errors = data.get("errors", [])
        except Exception as e:
            print(f"Error loading stats: {e}")

    def save(self) -> None:
        try:
            max_s = self._config.get("max_sends",  10000)
            max_e = self._config.get("max_errors",  2000)
            self.sends  = self.sends [-max(1, max_s):]
            self.errors = self.errors[-max(1, max_e):]
            with open(self._path, "w") as f:
                json.dump({"sends": self.sends, "errors": self.errors}, f)
        except Exception as e:
            print(f"Error saving stats: {e}")

    def record_send(self, *, ok: bool, file: str, webhook: str, folder: str,
                    ext: str, err_type: str = "", detail: str = "") -> None:
        ts    = time.strftime("%H:%M:%S")
        month = time.strftime("%Y-%m")
        self.sends.append({"time": ts, "month": month, "file": file,
                           "webhook": webhook, "folder": folder, "ext": ext, "ok": ok})
        if not ok:
            self.errors.append({"time": ts, "type": err_type, "file": file,
                                "webhook": webhook, "detail": detail})
        every = max(1, self._config.get("autosave_every", 10))
        if len(self.sends) % every == 0:
            Thread(target=self.save, daemon=True).start()

    def clear(self) -> None:
        self.sends  = []
        self.errors = []

    def months_data(self, n: int) -> List[Tuple[str, int]]:
        now = datetime.now()
        slots: List[Tuple[str, str]] = []
        for offset in range(n - 1, -1, -1):
            m = now.month - offset
            y = now.year
            while m <= 0:
                m += 12
                y -= 1
            slots.append((f"{y}-{m:02d}", datetime(y, m, 1).strftime("%b %y")))
        month_counts: Counter = Counter(s.get("month") for s in self.sends)
        return [(label, month_counts.get(key, 0)) for key, label in slots]

    def _count_by(self, field: str, source: Optional[List[dict]] = None,
                  ok_only: bool = True) -> List[Tuple[str, int]]:
        data = source if source is not None else self.sends
        counts: Dict[str, int] = defaultdict(int)
        for item in data:
            if ok_only and not item.get("ok"):
                continue
            counts[item.get(field, "Unknown")] += 1
        return sorted(counts.items(), key=lambda x: -x[1])

    def webhook_data(self)    -> List[Tuple[str, int]]: return self._count_by("webhook")
    def folder_data(self)     -> List[Tuple[str, int]]: return self._count_by("folder")
    def ext_data(self)        -> List[Tuple[str, int]]: return self._count_by("ext")
    def error_type_data(self) -> List[Tuple[str, int]]:
        return self._count_by("type", source=self.errors, ok_only=False)

    def webhook_table(self) -> List[Tuple]:
        wh: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
        for s in self.sends:
            rec = wh[s.get("webhook", "Unknown")]
            if s.get("ok"):
                rec[0] += 1
            else:
                rec[1] += 1
        rows = []
        for name, (ok, fail) in sorted(wh.items(), key=lambda x: -x[1][0]):
            tot  = ok + fail
            rate = f"{100 * ok / tot:.1f}%" if tot else "—"
            rows.append((name, ok, fail, rate))
        return rows
