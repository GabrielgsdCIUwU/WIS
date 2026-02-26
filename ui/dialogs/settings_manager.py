"""
ui/dialogs/settings_manager.py
--------------------------------
SettingsManager dialog.
"""

import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable, Dict, List, Optional, Tuple

from core.config import (C, COLOR_KEYS, DEFAULTS, THEME_PRESETS,
                          SettingsStore)
from services.stats_manager import load_themes_from_folder
from ui.components.factory import BasePopup
from ui.dialogs.profile_manager import SharedProfileManager
from ui.styles.theme_manager import mk_btn, mk_entry, mk_label, mk_chk


_BEHAVIOUR_ROWS: List[Tuple[str, str, float]] = [
    ("Scan rate (seconds)",         "scan_rate",    1.0),
    ("Send timeout (seconds)",      "send_timeout", 30),
    ("File settle delay (seconds)", "file_delay",   0.8),
]

_STATS_ROWS: List[Tuple[str, str, int]] = [
    ("Max send records to keep",                "max_sends",       10000),
    ("Max error records to keep",               "max_errors",       2000),
    ("Months shown in bar chart",               "months",             12),
    ("Stats autosave every N sends  (0 = never)", "autosave_every",  10),
]

_COLOR_DEFS: List[Tuple[str, str]] = [
    ("bg",      "Background"),    ("bg2",     "Surface / header"),
    ("bg3",     "Input / card"),  ("accent",  "Accent (blue)"),
    ("accent2", "Success (green)"),("danger", "Danger (red)"),
    ("warning", "Warning (orange)"),("fg",    "Primary text"),
    ("fg2",     "Secondary text"),("border",  "Borders"),
]


class SettingsManager(BasePopup):
    def __init__(self, parent, store: SettingsStore, on_save: Callable):
        super().__init__(parent, "Settings", size="560x720")
        self._store         = store
        self._on_save       = on_save
        self._vars:         Dict[str, tk.Variable] = {}
        self._swatch_refs:  Dict[str, tk.Frame]    = {}
        self._custom_themes = dict(store.custom_themes)
        self._folder_themes: Dict[str, Dict[str, str]] = {}
        self._build()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _all_preset_names(self) -> List[str]:
        seen  = set()
        names = []
        for n in list(THEME_PRESETS.keys()) \
               + list(self._folder_themes.keys()) \
               + list(self._custom_themes.keys()):
            if n not in seen:
                seen.add(n)
                names.append(n)
        return names

    def _lookup_preset(self, name: str) -> Optional[Dict[str, str]]:
        return (THEME_PRESETS.get(name)
                or self._folder_themes.get(name)
                or self._custom_themes.get(name))

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        b = self.body
        from tkinter import ttk
        canvas = tk.Canvas(b, bg=C["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(b, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner    = tk.Frame(canvas, bg=C["bg"])
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(inner_id, width=canvas.winfo_width())
        inner.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(inner_id, width=e.width))

        # ── Behaviour ──
        self._section(inner, "Behaviour")
        for label, key, default in _BEHAVIOUR_ROWS:
            self._num_row(inner, label, key, default, self._store.values)
        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── File types ──
        self._section(inner, "Watched Extensions")
        mk_label(inner, "Comma-separated  (e.g.  .jpg,.png,.gif)",
                 fg=C["fg2"], font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 4))
        self._vars["formats"] = tk.StringVar(
            value=self._store.values.get("formats", DEFAULTS["formats"]))
        mk_entry(inner, textvariable=self._vars["formats"], width=50).pack(anchor="w", pady=(0, 4))
        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── Sound ──
        self._section(inner, "Sound Notifications")
        sound_row = tk.Frame(inner, bg=C["bg"])
        sound_row.pack(fill="x", pady=2)
        self._vars["sound_enabled"] = tk.BooleanVar(
            value=bool(self._store.values.get("sound_enabled", True)))
        mk_chk(sound_row, "Enable sounds  (validation.mp3 / exclamation.mp3)",
               self._vars["sound_enabled"], bg=C["bg"]).pack(side="left")
        vol_row = tk.Frame(inner, bg=C["bg"])
        vol_row.pack(fill="x", pady=2)
        mk_label(vol_row, "Volume  (0.0 – 1.0)", fg=C["fg"], width=30, anchor="w").pack(side="left")
        self._vars["sound_volume"] = tk.StringVar(
            value=str(self._store.values.get("sound_volume", 0.8)))
        mk_entry(vol_row, textvariable=self._vars["sound_volume"], width=8).pack(side="left", padx=(6, 0))
        from core.config import _PYGAME_OK
        if not _PYGAME_OK:
            mk_label(inner,
                     "pygame not installed — sounds disabled.  Run: pip install pygame",
                     fg=C["warning"], font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))
        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── Startup & Debug ──
        self._section(inner, "Startup & Debug")
        for var_name, label_text, attr in [
            ("_auto_start_var", "Auto-start monitoring on launch", "auto_start"),
            ("_debug_var",      "Debug mode  (log every scan cycle)", "debug_mode"),
        ]:
            row = tk.Frame(inner, bg=C["bg"])
            row.pack(fill="x", pady=2)
            bv = tk.BooleanVar(value=getattr(self._store, attr))
            setattr(self, var_name, bv)
            mk_chk(row, label_text, bv, bg=C["bg"]).pack(side="left")
        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── Statistics ──
        self._section(inner, "Statistics")
        for label, key, default in _STATS_ROWS:
            self._num_row(inner, label, key, default, self._store.stats_config)
        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── Shared Profiles ──
        self._section(inner, "Shared Profiles")
        mk_label(inner,
                 "Create named identities (username + avatar) to assign to shared webhooks.",
                 fg=C["fg2"], font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 4))
        sp_count_row = tk.Frame(inner, bg=C["bg"])
        sp_count_row.pack(fill="x", pady=(0, 2))
        n_sp = len(self._store.shared_profiles)
        self._sp_count_lbl = mk_label(sp_count_row,
            f"{n_sp} profile{'s' if n_sp != 1 else ''} configured",
            fg=C["accent2"] if n_sp else C["fg2"], font=("Segoe UI", 8))
        self._sp_count_lbl.pack(side="left")
        mk_btn(inner, "Manage Shared Profiles", self._open_shared_profiles,
               color=C["accent"], fg=C["bg"]).pack(anchor="w", pady=(0, 2))
        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── Theme Folder ──
        self._section(inner, "Theme Folder")
        mk_label(inner,
                 "Point to a folder of .wistheme / .json files to load them as presets.",
                 fg=C["fg2"], font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 4))
        tf_row = tk.Frame(inner, bg=C["bg"])
        tf_row.pack(fill="x", pady=(0, 2))
        self._vars["theme_folder"] = tk.StringVar(
            value=self._store.values.get("theme_folder", ""))
        mk_entry(tf_row, textvariable=self._vars["theme_folder"], width=2).pack(
            side="left", fill="x", expand=True, padx=(0, 6))
        mk_btn(tf_row, "Browse…", self._browse_theme_folder,
               color=C["bg3"], fg=C["fg"]).pack(side="left", padx=(0, 4))
        mk_btn(tf_row, "Clear", self._clear_theme_folder,
               color=C["bg3"], fg=C["danger"]).pack(side="left")
        tf_action_row = tk.Frame(inner, bg=C["bg"])
        tf_action_row.pack(fill="x", pady=(4, 0))
        mk_btn(tf_action_row, "Reload Folder Themes", self._reload_folder_themes,
               color=C["accent"], fg=C["bg"]).pack(side="left")
        self._tf_status = mk_label(tf_action_row, "", fg=C["fg2"], font=("Segoe UI", 8))
        self._tf_status.pack(side="left", padx=10)
        saved_folder = self._store.values.get("theme_folder", "")
        if saved_folder and os.path.isdir(saved_folder):
            self._folder_themes = load_themes_from_folder(saved_folder)
        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── Theme Presets ──
        self._section(inner, "Theme Presets")
        all_presets = self._all_preset_names()
        self._preset_var = tk.StringVar(value=all_presets[0] if all_presets else "")
        preset_row = tk.Frame(inner, bg=C["bg"])
        preset_row.pack(fill="x", pady=(0, 4))
        self._preset_menu = tk.OptionMenu(preset_row, self._preset_var, *(all_presets or ["—"]))
        self._preset_menu.config(
            bg=C["bg3"], fg=C["fg"], activebackground=C["bg2"],
            activeforeground=C["accent"], highlightthickness=0,
            relief="flat", font=("Segoe UI", 9), bd=0, anchor="w")
        self._preset_menu["menu"].config(bg=C["bg3"], fg=C["fg"], font=("Segoe UI", 9))
        self._preset_menu.pack(side="left", fill="x", expand=True, padx=(0, 6))
        mk_btn(preset_row, "Apply",         self._apply_preset,
               color=C["accent"], fg=C["bg"]).pack(side="left", padx=(0, 4))
        mk_btn(preset_row, "Delete Custom", self._delete_preset,
               color=C["bg3"], fg=C["danger"]).pack(side="left")
        save_preset_row = tk.Frame(inner, bg=C["bg"])
        save_preset_row.pack(fill="x", pady=(0, 4))
        mk_label(save_preset_row, "Save as:", fg=C["fg2"], width=8, anchor="w").pack(side="left")
        self._new_preset_var = tk.StringVar()
        mk_entry(save_preset_row, textvariable=self._new_preset_var, width=22).pack(side="left", padx=(0, 6))
        mk_btn(save_preset_row, "Save Preset", self._save_preset,
               color=C["accent2"], fg=C["bg"]).pack(side="left")
        ie_row = tk.Frame(inner, bg=C["bg"])
        ie_row.pack(fill="x", pady=(0, 2))
        mk_btn(ie_row, "Export Theme", self._export_theme,
               color=C["bg3"], fg=C["fg"]).pack(side="left", padx=(0, 6))
        mk_btn(ie_row, "Import Theme", self._import_theme,
               color=C["bg3"], fg=C["fg"]).pack(side="left")
        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── Color Editor ──
        self._section(inner, "Color Editor  (hex codes)")
        grid = tk.Frame(inner, bg=C["bg"])
        grid.pack(fill="x", pady=4)
        for i, (key, lbl_text) in enumerate(_COLOR_DEFS):
            row_frame = tk.Frame(grid, bg=C["bg"])
            row_frame.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 16), pady=3)
            mk_label(row_frame, lbl_text, fg=C["fg2"],
                     font=("Segoe UI", 8), width=16, anchor="w").pack(side="left")
            self._vars[key] = tk.StringVar(
                value=self._store.values.get(key, DEFAULTS.get(key, "")))
            mk_entry(row_frame, textvariable=self._vars[key], width=9).pack(side="left")
            swatch = tk.Frame(row_frame, width=18, height=18,
                              bg=self._vars[key].get() or C["bg3"], relief="flat", bd=1)
            swatch.pack(side="left", padx=(4, 0))
            swatch.pack_propagate(False)
            self._swatch_refs[key] = swatch
            self._vars[key].trace_add("write", lambda *_, k=key: self._update_swatch(k))

        tk.Frame(inner, bg=C["bg"], height=4).pack()
        mk_btn(inner, "Reset to defaults", self._reset_colors,
               color=C["bg3"], fg=C["fg2"]).pack(anchor="w", pady=4)
        self.add_footer_buttons(self._save)
        self._update_tf_status()

    # ── Shared Profiles ──────────────────────────────────────────────────────

    def _open_shared_profiles(self):
        def on_save(profiles):
            self._store.shared_profiles = profiles
            n = len(profiles)
            self._sp_count_lbl.config(
                text=f"{n} profile{'s' if n != 1 else ''} configured",
                fg=C["accent2"] if n else C["fg2"])
        SharedProfileManager(self, self._store.shared_profiles, on_save)

    # ── Theme Folder ─────────────────────────────────────────────────────────

    def _browse_theme_folder(self):
        folder = filedialog.askdirectory(parent=self, title="Select Theme Folder")
        if folder:
            self._vars["theme_folder"].set(folder)
            self._reload_folder_themes()

    def _clear_theme_folder(self):
        self._vars["theme_folder"].set("")
        self._folder_themes.clear()
        self._rebuild_preset_menu()
        self._update_tf_status()

    def _reload_folder_themes(self):
        folder = self._vars["theme_folder"].get().strip()
        if not folder:
            messagebox.showwarning("No Folder", "No theme folder is set.", parent=self); return
        if not os.path.isdir(folder):
            messagebox.showwarning("Not Found", f"Folder not found:\n{folder}", parent=self); return
        self._folder_themes = load_themes_from_folder(folder)
        self._rebuild_preset_menu()
        self._update_tf_status()
        n = len(self._folder_themes)
        if n:
            messagebox.showinfo("Loaded", f"Loaded {n} theme{'s' if n != 1 else ''} from folder.", parent=self)
        else:
            messagebox.showwarning("None Found",
                                   "No valid .wistheme / .json themes found in that folder.",
                                   parent=self)

    def _update_tf_status(self):
        folder = self._vars["theme_folder"].get().strip() if "theme_folder" in self._vars else ""
        if not folder:
            self._tf_status.config(text="No folder selected", fg=C["fg2"])
        elif not os.path.isdir(folder):
            self._tf_status.config(text="⚠ Folder not found", fg=C["warning"])
        else:
            n = len(self._folder_themes)
            label = f"{n} theme{'s' if n != 1 else ''} loaded  ·  {os.path.basename(folder)}"
            self._tf_status.config(text=label, fg=C["accent2"])

    # ── Section helpers ──────────────────────────────────────────────────────

    def _section(self, parent, text):
        mk_label(parent, text, fg=C["accent"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(4, 0))
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=(2, 6))

    def _num_row(self, parent, label_text: str, key: str, default, source: dict):
        row = tk.Frame(parent, bg=C["bg"])
        row.pack(fill="x", pady=2)
        mk_label(row, label_text, fg=C["fg"], width=30, anchor="w").pack(side="left")
        self._vars[key] = tk.StringVar(value=str(source.get(key, default)))
        mk_entry(row, textvariable=self._vars[key], width=8).pack(side="left", padx=(6, 0))

    # ── Color helpers ────────────────────────────────────────────────────────

    def _reset_colors(self):
        for k in COLOR_KEYS:
            if k in self._vars:
                self._vars[k].set(DEFAULTS[k])

    def _update_swatch(self, key):
        val = self._vars[key].get().strip()
        sw  = self._swatch_refs.get(key)
        if sw and len(val) == 7 and val.startswith("#"):
            try:
                sw.config(bg=val)
            except Exception:
                pass

    def _current_colors(self) -> dict:
        return {k: self._vars[k].get().strip() for k in COLOR_KEYS if k in self._vars}

    def _load_colors(self, colors: dict):
        for k in COLOR_KEYS:
            if k in colors and k in self._vars:
                self._vars[k].set(colors[k])
                self._update_swatch(k)

    # ── Preset actions ───────────────────────────────────────────────────────

    def _apply_preset(self):
        name   = self._preset_var.get()
        colors = self._lookup_preset(name)
        if colors:
            self._load_colors(colors)
        else:
            messagebox.showwarning("Not Found", f"Preset '{name}' not found.", parent=self)

    def _save_preset(self):
        name = self._new_preset_var.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Enter a name for the preset.", parent=self); return
        if name in THEME_PRESETS:
            messagebox.showwarning("Reserved", f"{name!r} is a built-in preset.", parent=self); return
        self._custom_themes[name] = self._current_colors()
        self._rebuild_preset_menu()
        self._preset_var.set(name)
        self._new_preset_var.set("")
        messagebox.showinfo("Saved", f"Preset '{name}' saved.", parent=self)

    def _delete_preset(self):
        name = self._preset_var.get()
        if name in THEME_PRESETS:
            messagebox.showwarning("Built-in", "Cannot delete built-in presets.", parent=self); return
        if name in self._folder_themes:
            messagebox.showwarning("Folder Theme",
                                   f"'{name}' comes from the theme folder and cannot be deleted here.\n"
                                   "Remove or edit the file in the folder instead.", parent=self); return
        if name not in self._custom_themes:
            messagebox.showwarning("Not Found", f"'{name}' is not a custom preset.", parent=self); return
        if messagebox.askyesno("Delete", f"Delete preset '{name}'?", parent=self):
            del self._custom_themes[name]
            self._rebuild_preset_menu()

    def _rebuild_preset_menu(self):
        all_names = self._all_preset_names()
        menu = self._preset_menu["menu"]
        menu.delete(0, "end")
        for n in all_names:
            menu.add_command(label=n, command=lambda v=n: self._preset_var.set(v))
        if all_names and self._preset_var.get() not in all_names:
            self._preset_var.set(all_names[0])

    # ── Import / Export ──────────────────────────────────────────────────────

    def _export_theme(self):
        colors = self._current_colors()
        name   = self._preset_var.get() or "my_theme"
        path   = filedialog.asksaveasfilename(
            parent=self, title="Export Theme",
            defaultextension=".wistheme", initialfile=name.replace(" ", "_"),
            filetypes=[("WIS Theme", "*.wistheme"), ("JSON", "*.json"), ("All", "*.*")])
        if not path: return
        try:
            with open(path, "w") as f:
                json.dump({"wis_theme": True, "name": name, "colors": colors}, f, indent=2)
            messagebox.showinfo("Exported", f"Theme exported to:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Export Failed", str(e), parent=self)

    def _import_theme(self):
        path = filedialog.askopenfilename(
            parent=self, title="Import Theme",
            filetypes=[("WIS Theme", "*.wistheme"), ("JSON", "*.json"), ("All", "*.*")])
        if not path: return
        try:
            with open(path) as f:
                data = json.load(f)
            if not data.get("wis_theme"):
                messagebox.showwarning("Invalid File", "Not a WIS theme.", parent=self); return
            valid = {k: v for k, v in data.get("colors", {}).items()
                     if k in COLOR_KEYS and isinstance(v, str)
                     and v.startswith("#") and len(v) == 7}
            if not valid:
                messagebox.showwarning("Empty", "No valid colors found.", parent=self); return
            self._load_colors(valid)
            imported_name = data.get("name", os.path.splitext(os.path.basename(path))[0])
            if messagebox.askyesno("Save Preset?", f"Save as preset '{imported_name}'?", parent=self):
                if imported_name not in THEME_PRESETS:
                    self._custom_themes[imported_name] = valid
                    self._rebuild_preset_menu()
                    self._preset_var.set(imported_name)
        except Exception as e:
            messagebox.showerror("Import Failed", str(e), parent=self)

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self):
        for key in ("scan_rate", "send_timeout", "file_delay"):
            try:
                self._store.values[key] = float(self._vars[key].get())
            except ValueError:
                self._store.values[key] = DEFAULTS[key]
        self._store.values["formats"]       = self._vars["formats"].get().strip()
        self._store.values["sound_enabled"] = bool(self._vars["sound_enabled"].get())
        try:
            vol = float(self._vars["sound_volume"].get())
            self._store.values["sound_volume"] = max(0.0, min(1.0, vol))
        except ValueError:
            self._store.values["sound_volume"] = DEFAULTS["sound_volume"]
        self._store.values["theme_folder"] = self._vars["theme_folder"].get().strip()
        self._store.values.update({
            k: (v if v.startswith("#") and len(v) == 7 else DEFAULTS.get(k))
            for k in COLOR_KEYS
            if (v := self._vars[k].get().strip())
        })
        for _, key, default in _STATS_ROWS:
            try:
                self._store.stats_config[key] = int(float(self._vars[key].get()))
            except (ValueError, KeyError):
                self._store.stats_config[key] = default
        self._store.auto_start    = self._auto_start_var.get()
        self._store.debug_mode    = self._debug_var.get()
        self._store.custom_themes = self._custom_themes
        try:    self._on_save(self._store)
        finally: self.destroy()
