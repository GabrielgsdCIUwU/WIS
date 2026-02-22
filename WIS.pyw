import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import time
import requests
import json
from threading import Thread
import mimetypes
import math
from collections import defaultdict
from datetime import datetime

# Optional audio — pygame handles MP3 + volume on all platforms
try:
    import pygame
    pygame.mixer.init()
    _AUDIO_OK = True
except Exception:
    _AUDIO_OK = False

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────
#  DEFAULTS
# ─────────────────────────────────────────────
DEFAULTS = {
    "bg":           "#0f1117",
    "bg2":          "#181c26",
    "bg3":          "#1f2433",
    "accent":       "#4f8ef7",
    "accent2":      "#2ecc8f",
    "danger":       "#e05252",
    "warning":      "#f0a500",
    "fg":           "#d6dce8",
    "fg2":          "#7a8499",
    "border":       "#2a3045",
    "scan_rate":    1.0,
    "send_timeout": 30,
    "file_delay":   0.8,
    "formats":      ".jpg,.jpeg,.png,.gif,.bmp,.webp",
    "sound_enabled": True,
    "sound_volume":  0.8,
}


# ─────────────────────────────────────────────
#  BUILT-IN THEME PRESETS
# ─────────────────────────────────────────────

COLOUR_KEYS = ["bg", "bg2", "bg3", "accent", "accent2", "danger", "warning", "fg", "fg2", "border"]

THEME_PRESETS = {
    "Dark Blue (default)": {
        "bg": "#0f1117", "bg2": "#181c26", "bg3": "#1f2433",
        "accent": "#4f8ef7", "accent2": "#2ecc8f", "danger": "#e05252",
        "warning": "#f0a500", "fg": "#d6dce8", "fg2": "#7a8499", "border": "#2a3045",
    },
    "Midnight": {
        "bg": "#0d0d12", "bg2": "#14141e", "bg3": "#1a1a28",
        "accent": "#9b7cf4", "accent2": "#56d8a4", "danger": "#f26d6d",
        "warning": "#f5c542", "fg": "#e2e2f0", "fg2": "#6e6e99", "border": "#2a2a40",
    },
    "Mocha": {
        "bg": "#1c1410", "bg2": "#241c16", "bg3": "#2e231c",
        "accent": "#d4956a", "accent2": "#a8bf7a", "danger": "#d46a6a",
        "warning": "#d4b06a", "fg": "#e8ddd5", "fg2": "#9e8878", "border": "#3e2e24",
    },
    "Solarized Dark": {
        "bg": "#002b36", "bg2": "#073642", "bg3": "#0d4452",
        "accent": "#268bd2", "accent2": "#2aa198", "danger": "#dc322f",
        "warning": "#b58900", "fg": "#839496", "fg2": "#586e75", "border": "#124652",
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
    "Rose Pine": {
        "bg": "#191724", "bg2": "#1f1d2e", "bg3": "#26233a",
        "accent": "#c4a7e7", "accent2": "#9ccfd8", "danger": "#eb6f92",
        "warning": "#f6c177", "fg": "#e0def4", "fg2": "#908caa", "border": "#393552",
    },
}

C = dict(DEFAULTS)  # live colour dict, mutated by settings


def _lighten(hex_color, amt=25):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return "#{:02x}{:02x}{:02x}".format(min(255,r+amt), min(255,g+amt), min(255,b+amt))


def apply_treeview_style():
    """Set ttk dark theme once globally."""
    s = ttk.Style()
    s.theme_use("clam")
    s.configure("Treeview",
                background=C["bg2"], foreground=C["fg"],
                fieldbackground=C["bg2"], rowheight=26,
                font=("Segoe UI", 9))
    s.configure("Treeview.Heading",
                background=C["bg3"], foreground=C["accent"],
                font=("Segoe UI", 9, "bold"), relief="flat")
    s.map("Treeview",
          background=[("selected", C["bg3"])],
          foreground=[("selected", C["accent"])])
    s.configure("Vertical.TScrollbar",
                background=C["bg3"], troughcolor=C["bg2"],
                arrowcolor=C["fg2"])


# ─────────────────────────────────────────────
#  WIDGET FACTORY HELPERS
# ─────────────────────────────────────────────

def mk_btn(parent, text, command, color=None, fg=None, **kw):
    color = color or C["bg3"]
    fg    = fg    or C["accent"]
    b = tk.Button(parent, text=text, command=command,
                  bg=color, fg=fg,
                  activebackground=_lighten(color), activeforeground=fg,
                  relief="flat", bd=0, padx=12, pady=5,
                  font=("Segoe UI", 9, "bold"), cursor="hand2", **kw)
    b.bind("<Enter>", lambda e: b.config(bg=_lighten(color)))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b


def mk_entry(parent, textvariable=None, width=40):
    return tk.Entry(parent, textvariable=textvariable, width=width,
                    bg=C["bg3"], fg=C["fg"], insertbackground=C["accent"],
                    relief="flat", bd=0, font=("Segoe UI", 9),
                    highlightthickness=1,
                    highlightbackground=C["border"],
                    highlightcolor=C["accent"])


def mk_label(parent, text, fg=None, font=None, bg=None, **kw):
    bg = bg if bg is not None else C["bg"]
    return tk.Label(parent, text=text, bg=bg, fg=fg or C["fg"],
                    font=font or ("Segoe UI", 9), **kw)


def mk_sep(parent):
    """Horizontal separator — always uses pack on parent."""
    tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=6)


def mk_chk(parent, text, variable, command=None, bg=None):
    bg = bg if bg is not None else C["bg"]
    c = tk.Checkbutton(parent, text=text, variable=variable,
                       bg=bg, fg=C["fg"], selectcolor=C["bg3"],
                       activebackground=bg, activeforeground=C["fg"],
                       font=("Segoe UI", 9), highlightthickness=0,
                       command=command)
    return c


def mk_section(parent, text):
    tk.Label(parent, text=text, bg=C["bg"], fg=C["fg2"],
             font=("Segoe UI", 7, "bold")).pack(anchor="w")
    tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=3)


# ─────────────────────────────────────────────
#  TREEVIEW PANEL  (reusable)
# ─────────────────────────────────────────────

class TreePanel(tk.Frame):
    def __init__(self, parent, columns, headings, widths, height=9):
        super().__init__(parent, bg=C["bg"])
        self.tree = ttk.Treeview(self, columns=columns, show="headings",
                                  height=height, selectmode="browse")
        for col, hd, w in zip(columns, headings, widths):
            self.tree.heading(col, text=hd)
            anchor = "center" if w <= 60 else "w"
            self.tree.column(col, width=w, anchor=anchor,
                             stretch=(col == columns[-1]))
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def selected_idx(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def insert(self, iid, values):
        self.tree.insert("", "end", iid=str(iid), values=values)


# ─────────────────────────────────────────────
#  BASE POPUP
#
#  Layout (top → bottom, all via pack on self):
#    [header frame]
#    [body frame]          ← subclasses put content here
#    [footer frame]        ← added by self._add_footer()
#
#  RULE: never call pack/grid on `self` (Toplevel) inside subclass —
#  only add children to self.body.
# ─────────────────────────────────────────────

class BasePopup(tk.Toplevel):
    def __init__(self, parent, title, subtitle="", size="560x500"):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.geometry(size)

        # ── header ──
        hdr = tk.Frame(self, bg=C["bg2"])
        hdr.pack(fill="x", side="top")
        mk_label(hdr, title, fg=C["accent"], bg=C["bg2"],
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=14, pady=10)
        if subtitle:
            mk_label(hdr, subtitle, fg=C["fg2"], bg=C["bg2"],
                     font=("Segoe UI", 8)).pack(side="left")

        # ── footer (packed to bottom BEFORE body so body fills remaining space) ──
        self._footer_frame = tk.Frame(self, bg=C["bg"])
        self._footer_frame.pack(fill="x", side="bottom", padx=12, pady=8)
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", side="bottom")

        # ── body (fills all space between header and footer) ──
        self.body = tk.Frame(self, bg=C["bg"])
        self.body.pack(fill="both", expand=True, padx=14, pady=10, side="top")

    def add_footer_buttons(self, save_cmd, cancel_cmd=None):
        """Call this at the END of subclass _build() to add Save/Cancel."""
        mk_btn(self._footer_frame, "Save & Close", save_cmd,
               color=C["accent"], fg=C["bg"]).pack(side="right", padx=(4, 0))
        mk_btn(self._footer_frame, "Cancel",
               cancel_cmd or self.destroy,
               color=C["bg3"], fg=C["fg2"]).pack(side="right")


# ─────────────────────────────────────────────
#  WEBHOOK MANAGER
# ─────────────────────────────────────────────

class WebhookManager(BasePopup):
    def __init__(self, parent, webhooks, on_save):
        super().__init__(parent, "Webhook Manager",
                         "One detection is sent to all enabled webhooks",
                         size="600x540")
        self.webhooks  = [dict(w) for w in webhooks]
        self.on_save   = on_save
        self._edit_idx = None
        self._build()
        self._refresh()

    def _build(self):
        b = self.body

        # ── TOP: tree + action buttons (no expand) ──
        top = tk.Frame(b, bg=C["bg"])
        top.pack(fill="x", side="top")

        self.panel = TreePanel(top,
            columns=("on", "name", "url"),
            headings=("On", "Name", "URL"),
            widths=(44, 140, 340),
            height=7)
        self.panel.pack(fill="x")

        act = tk.Frame(top, bg=C["bg"])
        act.pack(fill="x", pady=(4, 0))
        mk_btn(act, "Edit",   self._edit,   color=C["bg3"], fg=C["accent"]).pack(side="left", padx=(0, 4))
        mk_btn(act, "Toggle", self._toggle, color=C["bg3"], fg=C["warning"]).pack(side="left", padx=4)
        mk_btn(act, "Remove", self._remove, color=C["bg3"], fg=C["danger"]).pack(side="left", padx=4)

        tk.Frame(b, bg=C["border"], height=1).pack(fill="x", pady=8, side="top")

        # ── BOTTOM: add / edit form (always visible) ──
        bottom = tk.Frame(b, bg=C["bg"])
        bottom.pack(fill="x", side="top")

        mk_label(bottom, "Add / Edit Webhook", fg=C["accent"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 6))

        # Name row
        name_row = tk.Frame(bottom, bg=C["bg"])
        name_row.pack(fill="x", pady=2)
        mk_label(name_row, "Name:", fg=C["fg2"], width=6, anchor="w").pack(side="left")
        self._name_var = tk.StringVar()
        mk_entry(name_row, textvariable=self._name_var, width=26).pack(side="left", padx=(4, 0))

        # URL row
        url_row = tk.Frame(bottom, bg=C["bg"])
        url_row.pack(fill="x", pady=2)
        mk_label(url_row, "URL:", fg=C["fg2"], width=6, anchor="w").pack(side="left")
        self._url_var = tk.StringVar()
        mk_entry(url_row, textvariable=self._url_var, width=56).pack(side="left", padx=(4, 0), fill="x", expand=True)

        # Buttons
        btn_row = tk.Frame(bottom, bg=C["bg"])
        btn_row.pack(fill="x", pady=(8, 0))
        self._add_btn = mk_btn(btn_row, "+ Add", self._commit, color=C["accent2"], fg=C["bg"])
        self._add_btn.pack(side="left")
        mk_btn(btn_row, "Clear", self._clear_form, color=C["bg3"], fg=C["fg2"]).pack(side="left", padx=8)

        self.add_footer_buttons(self._save)

    def _refresh(self):
        self.panel.clear()
        for i, w in enumerate(self.webhooks):
            on = "✔" if w.get("enabled", True) else "—"
            self.panel.insert(i, (on, w.get("name", ""), w.get("url", "")))

    def _edit(self):
        idx = self.panel.selected_idx()
        if idx is None: return
        w = self.webhooks[idx]
        self._name_var.set(w.get("name", ""))
        self._url_var.set(w.get("url", ""))
        self._edit_idx = idx
        self._add_btn.config(text="Update")

    def _toggle(self):
        idx = self.panel.selected_idx()
        if idx is None: return
        self.webhooks[idx]["enabled"] = not self.webhooks[idx].get("enabled", True)
        self._refresh()

    def _remove(self):
        idx = self.panel.selected_idx()
        if idx is None: return
        name = self.webhooks[idx].get("name", "this webhook")
        if messagebox.askyesno("Remove", f"Remove '{name}'?", parent=self):
            del self.webhooks[idx]
            self._refresh()

    def _commit(self):
        name = self._name_var.get().strip()
        url  = self._url_var.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Enter a name.", parent=self); return
        if not url.startswith("http"):
            messagebox.showwarning("Invalid URL", "URL must start with http.", parent=self); return
        if self._edit_idx is not None:
            self.webhooks[self._edit_idx].update(name=name, url=url)
            self._edit_idx = None
        else:
            self.webhooks.append({"name": name, "url": url, "enabled": True})
        self._clear_form()
        self._refresh()

    def _clear_form(self):
        self._name_var.set("")
        self._url_var.set("")
        self._edit_idx = None
        self._add_btn.config(text="+ Add")

    def _save(self):
        try:
            self.on_save(self.webhooks)
        finally:
            self.destroy()


# ─────────────────────────────────────────────
#  FOLDER MANAGER
# ─────────────────────────────────────────────

class FolderManager(BasePopup):
    def __init__(self, parent, folders, on_save):
        super().__init__(parent, "Folder Manager",
                         "All enabled folders are scanned simultaneously",
                         size="640x540")
        self.folders  = [dict(f) for f in folders]
        self.on_save  = on_save
        self._build()
        self._refresh()

    def _build(self):
        b = self.body

        # ── TOP: tree + action buttons (fixed height, does NOT expand) ──
        top = tk.Frame(b, bg=C["bg"])
        top.pack(fill="x", side="top")

        self.panel = TreePanel(top,
            columns=("on", "rec", "path"),
            headings=("On", "Recursive", "Folder Path"),
            widths=(44, 80, 440),
            height=7)
        self.panel.pack(fill="x")

        act = tk.Frame(top, bg=C["bg"])
        act.pack(fill="x", pady=(4, 0))
        mk_btn(act, "Toggle",           self._toggle,     color=C["bg3"], fg=C["warning"]).pack(side="left", padx=(0, 4))
        mk_btn(act, "Toggle Recursive", self._toggle_rec, color=C["bg3"], fg=C["accent"]).pack(side="left", padx=4)
        mk_btn(act, "Remove",           self._remove,     color=C["bg3"], fg=C["danger"]).pack(side="left", padx=4)

        tk.Frame(b, bg=C["border"], height=1).pack(fill="x", pady=8, side="top")

        # ── BOTTOM: add form (fixed, always visible) ──
        bottom = tk.Frame(b, bg=C["bg"])
        bottom.pack(fill="x", side="top")

        mk_label(bottom, "Add Folder", fg=C["accent"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 8))

        # Path row: Browse packed RIGHT first, then entry fills remaining space
        path_row = tk.Frame(bottom, bg=C["bg"])
        path_row.pack(fill="x", pady=(0, 6))
        self._path_var = tk.StringVar()
        mk_btn(path_row, "Browse", self._browse,
               color=C["bg3"], fg=C["fg"]).pack(side="right", padx=(6, 0))
        self._path_entry = mk_entry(path_row, textvariable=self._path_var, width=2)
        self._path_entry.pack(side="left", fill="x", expand=True)

        # Recursive checkbox
        self._recursive_var = tk.BooleanVar(value=True)
        mk_chk(bottom, "Recursive (include subfolders)", self._recursive_var,
               bg=C["bg"]).pack(anchor="w", pady=(0, 8))

        # Add button in its own frame so it is never clipped
        add_frame = tk.Frame(bottom, bg=C["bg"])
        add_frame.pack(fill="x")
        mk_btn(add_frame, "+ Add Folder", self._add,
               color=C["accent2"], fg=C["bg"]).pack(side="left")

        self.add_footer_buttons(self._save)

    def _refresh(self):
        self.panel.clear()
        for i, f in enumerate(self.folders):
            on  = "✔" if f.get("enabled",   True)  else "—"
            rec = "✔" if f.get("recursive", False) else "—"
            self.panel.insert(i, (on, rec, f.get("path", "")))

    def _toggle(self):
        idx = self.panel.selected_idx()
        if idx is None: return
        self.folders[idx]["enabled"] = not self.folders[idx].get("enabled", True)
        self._refresh()

    def _toggle_rec(self):
        idx = self.panel.selected_idx()
        if idx is None: return
        self.folders[idx]["recursive"] = not self.folders[idx].get("recursive", False)
        self._refresh()

    def _remove(self):
        idx = self.panel.selected_idx()
        if idx is None: return
        path = self.folders[idx].get("path", "?")
        if messagebox.askyesno("Remove", f"Remove '{os.path.basename(path)}'?", parent=self):
            del self.folders[idx]
            self._refresh()

    def _browse(self):
        folder = filedialog.askdirectory(parent=self)
        if folder:
            self._path_var.set(folder)

    def _add(self):
        path = self._path_var.get().strip()
        if not path:
            messagebox.showwarning("Missing", "Select or type a folder path.", parent=self)
            return
        if not os.path.isdir(path):
            messagebox.showwarning("Invalid", f"Not a valid directory:\n{path}", parent=self)
            return
        existing = [f["path"] for f in self.folders]
        if path in existing:
            messagebox.showinfo("Duplicate", "This folder is already in the list.", parent=self)
            return
        self.folders.append({
            "path":      path,
            "enabled":   True,
            "recursive": self._recursive_var.get()
        })
        self._path_var.set("")
        self._refresh()

    def _save(self):
        try:
            self.on_save(self.folders)
        finally:
            self.destroy()


# ─────────────────────────────────────────────
#  SETTINGS MANAGER
# ─────────────────────────────────────────────

class SettingsManager(BasePopup):
    def __init__(self, parent, settings, on_save,
                 auto_start=None, debug_mode=None, stats_config=None, on_save_extra=None,
                 custom_themes=None, on_themes_save=None):
        super().__init__(parent, "Settings", size="560x680")
        self.settings        = dict(settings)
        self.on_save         = on_save
        self._vars           = {}
        self._auto_start     = auto_start
        self._debug_mode     = debug_mode
        self._stats_cfg      = stats_config if stats_config is not None else {}
        self._on_save_extra  = on_save_extra
        self._custom_themes  = dict(custom_themes) if custom_themes else {}
        self._on_themes_save = on_themes_save
        self._swatch_refs    = {}   # key -> tk.Frame swatch widget
        self._build()

    def _build(self):
        b = self.body

        # Scrollable canvas so content fits on small screens
        canvas = tk.Canvas(b, bg=C["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(b, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=C["bg"])
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(inner_id, width=canvas.winfo_width())
        inner.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(inner_id, width=e.width))

        # ── Behaviour ──
        self._section(inner, "Behaviour")
        self._num_row(inner, "Scan rate (seconds)",         "scan_rate",    1.0)
        self._num_row(inner, "Send timeout (seconds)",      "send_timeout", 30)
        self._num_row(inner, "File settle delay (seconds)", "file_delay",   0.8)

        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── File types ──
        self._section(inner, "Watched Extensions")
        mk_label(inner, "Comma-separated  (e.g.  .jpg,.png,.gif)",
                 fg=C["fg2"], font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 4))
        self._vars["formats"] = tk.StringVar(value=self.settings.get("formats", DEFAULTS["formats"]))
        mk_entry(inner, textvariable=self._vars["formats"], width=50).pack(anchor="w", pady=(0, 4))

        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── Sound ──
        self._section(inner, "Sound Notifications")

        sound_row = tk.Frame(inner, bg=C["bg"])
        sound_row.pack(fill="x", pady=2)
        self._vars["sound_enabled"] = tk.BooleanVar(
            value=bool(self.settings.get("sound_enabled", True)))
        mk_chk(sound_row, "Enable sounds  (validation.mp3 / exclamation.mp3)",
               self._vars["sound_enabled"], bg=C["bg"]).pack(side="left")

        vol_row = tk.Frame(inner, bg=C["bg"])
        vol_row.pack(fill="x", pady=2)
        mk_label(vol_row, "Volume  (0.0 – 1.0)", fg=C["fg"], width=30, anchor="w").pack(side="left")
        self._vars["sound_volume"] = tk.StringVar(
            value=str(self.settings.get("sound_volume", 0.8)))
        mk_entry(vol_row, textvariable=self._vars["sound_volume"], width=8).pack(side="left", padx=(6, 0))

        if not _AUDIO_OK:
            mk_label(inner,
                     "pygame not installed — sounds disabled.  Run: pip install pygame",
                     fg=C["warning"], font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))

        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── Startup & Debug ──
        self._section(inner, "Startup & Debug")

        startup_row = tk.Frame(inner, bg=C["bg"])
        startup_row.pack(fill="x", pady=2)
        self._auto_start_var = tk.BooleanVar(
            value=self._auto_start.get() if self._auto_start else False)
        mk_chk(startup_row, "Auto-start monitoring on launch",
               self._auto_start_var, bg=C["bg"]).pack(side="left")

        debug_row = tk.Frame(inner, bg=C["bg"])
        debug_row.pack(fill="x", pady=2)
        self._debug_mode_var = tk.BooleanVar(
            value=self._debug_mode.get() if self._debug_mode else False)
        mk_chk(debug_row, "Debug mode  (log every scan cycle)",
               self._debug_mode_var, bg=C["bg"]).pack(side="left")

        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── Statistics ──
        self._section(inner, "Statistics")

        self._stats_num_row(inner, "Max send records to keep",  "max_sends",  10000)
        self._stats_num_row(inner, "Max error records to keep", "max_errors",  2000)
        self._stats_num_row(inner, "Months shown in bar chart", "months",        12)

        save_row = tk.Frame(inner, bg=C["bg"])
        save_row.pack(fill="x", pady=2)
        mk_label(save_row, "Stats autosave every N sends  (0 = never)",
                 fg=C["fg"], width=38, anchor="w").pack(side="left")
        self._vars["autosave_every"] = tk.StringVar(
            value=str(self._stats_cfg.get("autosave_every", 10)))
        mk_entry(save_row, textvariable=self._vars["autosave_every"],
                 width=8).pack(side="left", padx=(6, 0))

        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── Theme Presets ──
        self._section(inner, "Theme Presets")

        # Preset selector row
        preset_row = tk.Frame(inner, bg=C["bg"])
        preset_row.pack(fill="x", pady=(0, 4))

        all_presets = list(THEME_PRESETS.keys()) + list(self._custom_themes.keys())
        self._preset_var = tk.StringVar(value=all_presets[0] if all_presets else "")
        self._preset_menu = tk.OptionMenu(preset_row, self._preset_var, *all_presets if all_presets else ["—"])
        self._preset_menu.config(
            bg=C["bg3"], fg=C["fg"], activebackground=C["bg2"], activeforeground=C["accent"],
            highlightthickness=0, relief="flat", font=("Segoe UI", 9), bd=0,
            indicatoron=True, anchor="w")
        self._preset_menu["menu"].config(bg=C["bg3"], fg=C["fg"], font=("Segoe UI", 9))
        self._preset_menu.pack(side="left", fill="x", expand=True, padx=(0, 6))
        mk_btn(preset_row, "Apply", self._apply_preset,
               color=C["accent"], fg=C["bg"]).pack(side="left", padx=(0, 4))
        mk_btn(preset_row, "Delete Custom", self._delete_preset,
               color=C["bg3"], fg=C["danger"]).pack(side="left")

        # Save current as custom preset
        save_preset_row = tk.Frame(inner, bg=C["bg"])
        save_preset_row.pack(fill="x", pady=(0, 4))
        mk_label(save_preset_row, "Save as:", fg=C["fg2"], width=8, anchor="w").pack(side="left")
        self._new_preset_var = tk.StringVar()
        mk_entry(save_preset_row, textvariable=self._new_preset_var, width=22).pack(side="left", padx=(0, 6))
        mk_btn(save_preset_row, "Save Preset", self._save_preset,
               color=C["accent2"], fg=C["bg"]).pack(side="left")

        # Import / Export row
        ie_row = tk.Frame(inner, bg=C["bg"])
        ie_row.pack(fill="x", pady=(0, 2))
        mk_btn(ie_row, "⬆ Export Theme", self._export_theme,
               color=C["bg3"], fg=C["fg"]).pack(side="left", padx=(0, 6))
        mk_btn(ie_row, "⬇ Import Theme", self._import_theme,
               color=C["bg3"], fg=C["fg"]).pack(side="left")

        tk.Frame(inner, bg=C["bg"], height=6).pack()

        # ── Colour Editor ──
        self._section(inner, "Colour Editor  (hex codes)")

        colour_defs = [
            ("bg",      "Background"),
            ("bg2",     "Surface / header"),
            ("bg3",     "Input / card"),
            ("accent",  "Accent (blue)"),
            ("accent2", "Success (green)"),
            ("danger",  "Danger (red)"),
            ("warning", "Warning (orange)"),
            ("fg",      "Primary text"),
            ("fg2",     "Secondary text"),
            ("border",  "Borders"),
        ]

        grid = tk.Frame(inner, bg=C["bg"])
        grid.pack(fill="x", pady=4)

        for i, (key, lbl_text) in enumerate(colour_defs):
            row_frame = tk.Frame(grid, bg=C["bg"])
            row_frame.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 16), pady=3)
            mk_label(row_frame, lbl_text, fg=C["fg2"],
                     font=("Segoe UI", 8), width=16, anchor="w").pack(side="left")
            self._vars[key] = tk.StringVar(value=self.settings.get(key, DEFAULTS.get(key, "")))
            entry = mk_entry(row_frame, textvariable=self._vars[key], width=9)
            entry.pack(side="left")
            # Live colour swatch
            swatch = tk.Frame(row_frame, width=18, height=18,
                              bg=self._vars[key].get() or C["bg3"],
                              relief="flat", bd=1)
            swatch.pack(side="left", padx=(4, 0))
            swatch.pack_propagate(False)
            self._swatch_refs[key] = swatch
            self._vars[key].trace_add("write", lambda *_, k=key: self._update_swatch(k))

        tk.Frame(inner, bg=C["bg"], height=4).pack()
        mk_btn(inner, "Reset to defaults", self._reset_colours,
               color=C["bg3"], fg=C["fg2"]).pack(anchor="w", pady=4)

        self.add_footer_buttons(self._save)

    def _section(self, parent, text):
        mk_label(parent, text, fg=C["accent"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(4, 0))
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=(2, 6))

    def _num_row(self, parent, label_text, key, default):
        row = tk.Frame(parent, bg=C["bg"])
        row.pack(fill="x", pady=2)
        mk_label(row, label_text, fg=C["fg"], width=30, anchor="w").pack(side="left")
        self._vars[key] = tk.StringVar(value=str(self.settings.get(key, default)))
        mk_entry(row, textvariable=self._vars[key], width=8).pack(side="left", padx=(6, 0))

    def _stats_num_row(self, parent, label_text, key, default):
        """Like _num_row but reads initial value from self._stats_cfg."""
        row = tk.Frame(parent, bg=C["bg"])
        row.pack(fill="x", pady=2)
        mk_label(row, label_text, fg=C["fg"], width=30, anchor="w").pack(side="left")
        self._vars[key] = tk.StringVar(value=str(self._stats_cfg.get(key, default)))
        mk_entry(row, textvariable=self._vars[key], width=8).pack(side="left", padx=(6, 0))

    def _reset_colours(self):
        for k in COLOUR_KEYS:
            if k in self._vars:
                self._vars[k].set(DEFAULTS[k])

    # ── Swatch live preview ───────────────────────────────────────────────────
    def _update_swatch(self, key):
        val = self._vars[key].get().strip()
        sw = self._swatch_refs.get(key)
        if sw:
            try:
                if len(val) == 7 and val.startswith("#"):
                    sw.config(bg=val)
            except Exception:
                pass

    # ── Theme preset actions ──────────────────────────────────────────────────
    def _current_colours(self):
        """Return dict of current colour values from entry fields."""
        out = {}
        for k in COLOUR_KEYS:
            v = self._vars.get(k)
            out[k] = v.get().strip() if v else DEFAULTS.get(k, "#000000")
        return out

    def _load_colours(self, colours: dict):
        """Push a colour dict into the entry fields and update swatches."""
        for k in COLOUR_KEYS:
            if k in colours and k in self._vars:
                self._vars[k].set(colours[k])
                self._update_swatch(k)

    def _apply_preset(self):
        name = self._preset_var.get()
        colours = THEME_PRESETS.get(name) or self._custom_themes.get(name)
        if colours:
            self._load_colours(colours)
        else:
            messagebox.showwarning("Not Found", f"Preset '{name}' not found.", parent=self)

    def _save_preset(self):
        name = self._new_preset_var.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Enter a name for the preset.", parent=self)
            return
        if name in THEME_PRESETS:
            messagebox.showwarning("Reserved",
                f"{name!r} is a built-in preset name. Choose a different name.", parent=self)
            return
        self._custom_themes[name] = self._current_colours()
        # Rebuild preset dropdown
        self._rebuild_preset_menu()
        self._preset_var.set(name)
        self._new_preset_var.set("")
        messagebox.showinfo("Saved", f"Preset '{name}' saved.", parent=self)

    def _delete_preset(self):
        name = self._preset_var.get()
        if name in THEME_PRESETS:
            messagebox.showwarning("Built-in", "Cannot delete built-in presets.", parent=self)
            return
        if name not in self._custom_themes:
            messagebox.showwarning("Not Found", f"'{name}' is not a custom preset.", parent=self)
            return
        if messagebox.askyesno("Delete", f"Delete preset '{name}'?", parent=self):
            del self._custom_themes[name]
            self._rebuild_preset_menu()

    def _rebuild_preset_menu(self):
        """Refresh the OptionMenu to include updated custom presets."""
        all_names = list(THEME_PRESETS.keys()) + list(self._custom_themes.keys())
        menu = self._preset_menu["menu"]
        menu.delete(0, "end")
        for n in all_names:
            menu.add_command(label=n, command=lambda v=n: self._preset_var.set(v))
        if all_names and self._preset_var.get() not in all_names:
            self._preset_var.set(all_names[0])

    def _export_theme(self):
        colours = self._current_colours()
        name    = self._preset_var.get() or "my_theme"
        path    = filedialog.asksaveasfilename(
            parent=self,
            title="Export Theme",
            defaultextension=".wistheme",
            initialfile=name.replace(" ", "_"),
            filetypes=[("WIS Theme", "*.wistheme"), ("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w") as f:
                json.dump({"wis_theme": True, "name": name, "colours": colours}, f, indent=2)
            messagebox.showinfo("Exported", f"Theme exported to:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Export Failed", str(e), parent=self)

    def _import_theme(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Import Theme",
            filetypes=[("WIS Theme", "*.wistheme"), ("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            with open(path) as f:
                data = json.load(f)
            if not data.get("wis_theme"):
                messagebox.showwarning("Invalid File", "This file is not a WIS theme.", parent=self)
                return
            colours = data.get("colours", {})
            valid   = {k: v for k, v in colours.items()
                       if k in COLOUR_KEYS and isinstance(v, str) and v.startswith("#") and len(v) == 7}
            if not valid:
                messagebox.showwarning("Empty", "No valid colours found in theme file.", parent=self)
                return
            self._load_colours(valid)
            # Offer to save as preset
            imported_name = data.get("name", os.path.splitext(os.path.basename(path))[0])
            if messagebox.askyesno("Save Preset?",
                                   f"Save imported theme as preset '{imported_name}'?", parent=self):
                if imported_name not in THEME_PRESETS:
                    self._custom_themes[imported_name] = valid
                    self._rebuild_preset_menu()
                    self._preset_var.set(imported_name)
        except Exception as e:
            messagebox.showerror("Import Failed", str(e), parent=self)

    def _save(self):
        out = {}
        for key in ("scan_rate", "send_timeout", "file_delay"):
            try:
                out[key] = float(self._vars[key].get())
            except ValueError:
                out[key] = DEFAULTS[key]
        out["formats"] = self._vars["formats"].get().strip()
        out["sound_enabled"] = bool(self._vars["sound_enabled"].get())
        try:
            vol = float(self._vars["sound_volume"].get())
            out["sound_volume"] = max(0.0, min(1.0, vol))
        except ValueError:
            out["sound_volume"] = DEFAULTS["sound_volume"]
        for key in COLOUR_KEYS:
            val = self._vars[key].get().strip()
            out[key] = val if val.startswith("#") and len(val) == 7 else DEFAULTS.get(key)

        # Save custom themes
        if self._on_themes_save:
            self._on_themes_save(self._custom_themes)

        # Propagate startup / debug booleans back to live WIS vars
        if self._auto_start is not None:
            self._auto_start.set(self._auto_start_var.get())
        if self._debug_mode is not None:
            self._debug_mode.set(self._debug_mode_var.get())

        # Stats config
        new_stats_cfg = {}
        for k, default in [("max_sends", 10000), ("max_errors", 2000),
                            ("months", 12), ("autosave_every", 10)]:
            try:
                new_stats_cfg[k] = int(float(self._vars[k].get()))
            except (ValueError, KeyError):
                new_stats_cfg[k] = default
        if self._on_save_extra:
            self._on_save_extra(new_stats_cfg)

        try:
            self.on_save(out)
        finally:
            self.destroy()


# ─────────────────────────────────────────────
#  STATS WINDOW
# ─────────────────────────────────────────────

class BarChart(tk.Canvas):
    """Minimal bar chart drawn on a Canvas."""
    def __init__(self, parent, data, title="", color=None, bg=None, value_fmt=None, **kw):
        bg = bg or C["bg2"]
        super().__init__(parent, bg=bg, highlightthickness=0, **kw)
        self._data      = data        # list of (label, value)
        self._title     = title
        self._color     = color or C["accent"]
        self._value_fmt = value_fmt or (lambda v: str(v))
        self.bind("<Configure>", lambda e: self._draw())

    def update_data(self, data):
        self._data = data
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10 or not self._data:
            if not self._data:
                self.create_text(w//2, h//2, text="No data yet",
                                 fill=C["fg2"], font=("Segoe UI", 9))
            return

        pad_l, pad_r, pad_t, pad_b = 48, 16, 28, 52
        chart_w = w - pad_l - pad_r
        chart_h = h - pad_t - pad_b

        # Title
        if self._title:
            self.create_text(w//2, pad_t//2, text=self._title,
                             fill=C["fg2"], font=("Segoe UI", 8, "bold"))

        max_val = max(v for _, v in self._data) if self._data else 1
        if max_val == 0: max_val = 1

        n      = len(self._data)
        gap    = 6
        bar_w  = max(6, (chart_w - gap * (n + 1)) // n)
        bar_w  = min(bar_w, 60)

        # Y axis
        self.create_line(pad_l, pad_t, pad_l, pad_t + chart_h, fill=C["border"], width=1)
        # X axis
        self.create_line(pad_l, pad_t + chart_h, pad_l + chart_w, pad_t + chart_h,
                         fill=C["border"], width=1)

        # Y gridlines / labels (5 steps)
        steps = 4
        for i in range(steps + 1):
            yv  = max_val * i / steps
            y   = pad_t + chart_h - int(chart_h * i / steps)
            self.create_line(pad_l - 3, y, pad_l + chart_w, y,
                             fill=C["border"], dash=(2, 4), width=1)
            self.create_text(pad_l - 5, y, text=self._value_fmt(round(yv)),
                             fill=C["fg2"], font=("Segoe UI", 7), anchor="e")

        total_bars_w = n * bar_w + (n + 1) * gap
        start_x      = pad_l + max(0, (chart_w - total_bars_w) // 2) + gap

        for i, (lbl, val) in enumerate(self._data):
            x0 = start_x + i * (bar_w + gap)
            x1 = x0 + bar_w
            bh = int(chart_h * val / max_val) if max_val else 0
            y0 = pad_t + chart_h - bh
            y1 = pad_t + chart_h

            # Shadow
            self.create_rectangle(x0+2, y0+2, x1+2, y1+2,
                                  fill=C["bg"], outline="", tags="shadow")
            # Bar
            self.create_rectangle(x0, y0, x1, y1,
                                  fill=self._color, outline="", width=0)
            # Value label on top
            if bh > 14:
                self.create_text((x0+x1)//2, y0+6, text=self._value_fmt(val),
                                 fill=C["bg"], font=("Segoe UI", 7, "bold"), anchor="n")
            else:
                self.create_text((x0+x1)//2, y0-6, text=self._value_fmt(val),
                                 fill=C["fg"], font=("Segoe UI", 7), anchor="s")

            # X label (rotated via wraplength trick — just abbreviate)
            short = lbl if len(lbl) <= 9 else lbl[:8] + "…"
            self.create_text((x0+x1)//2, y1 + 10, text=short,
                             fill=C["fg2"], font=("Segoe UI", 7), anchor="n",
                             width=bar_w + gap)


class PieChart(tk.Canvas):
    """Simple pie / donut chart."""
    PALETTE = ["#4f8ef7","#2ecc8f","#f0a500","#e05252","#a78bfa","#fb923c","#34d399","#f472b6"]

    def __init__(self, parent, data, title="", bg=None, **kw):
        bg = bg or C["bg2"]
        super().__init__(parent, bg=bg, highlightthickness=0, **kw)
        self._data  = data   # list of (label, value)
        self._title = title
        self.bind("<Configure>", lambda e: self._draw())

    def update_data(self, data):
        self._data = data
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10: return

        if self._title:
            self.create_text(w//2, 12, text=self._title,
                             fill=C["fg2"], font=("Segoe UI", 8, "bold"))

        total = sum(v for _, v in self._data if v > 0) if self._data else 0
        if total == 0:
            self.create_text(w//2, h//2, text="No data yet",
                             fill=C["fg2"], font=("Segoe UI", 9))
            return

        legend_h = min(len(self._data) * 16 + 4, 100)
        pie_area  = h - 24 - legend_h - 8
        r         = min(w // 2 - 30, pie_area // 2 - 8, 80)
        cx        = w // 2
        cy        = 24 + pie_area // 2

        start = -90.0
        for i, (lbl, val) in enumerate(self._data):
            if val <= 0: continue
            extent = 360.0 * val / total
            color  = self.PALETTE[i % len(self.PALETTE)]
            self.create_arc(cx-r, cy-r, cx+r, cy+r,
                            start=start, extent=extent,
                            fill=color, outline=C["bg2"], width=2)
            start += extent

        # Inner circle (donut)
        ir = int(r * 0.55)
        self.create_oval(cx-ir, cy-ir, cx+ir, cy+ir,
                         fill=C["bg2"], outline="")
        self.create_text(cx, cy, text=str(total), fill=C["fg"],
                         font=("Segoe UI", 11, "bold"))
        self.create_text(cx, cy+14, text="total", fill=C["fg2"],
                         font=("Segoe UI", 7))

        # Legend
        ly = cy + r + 12
        for i, (lbl, val) in enumerate(self._data):
            color = self.PALETTE[i % len(self.PALETTE)]
            pct   = f"{100*val/total:.0f}%" if total else "0%"
            col   = i % 2
            row   = i // 2
            lx    = 16 + col * (w // 2)
            lyi   = ly + row * 16
            self.create_rectangle(lx, lyi+2, lx+10, lyi+12, fill=color, outline="")
            short = lbl if len(lbl) <= 14 else lbl[:13] + "…"
            self.create_text(lx+14, lyi+7, text=f"{short}  {val} ({pct})",
                             fill=C["fg2"], font=("Segoe UI", 7), anchor="w")


class StatsWindow(BasePopup):
    def __init__(self, parent, stats_data, stats_config=None):
        super().__init__(parent, "Statistics", "Send history & analytics", size="860x640")
        self.resizable(True, True)
        self.geometry("860x640")
        self._stats  = stats_data    # reference to live dict
        self._config = stats_config or {}
        self._build()

    # ── helpers ──────────────────────────────

    def _months_data(self, n=None):
        """Returns list of (YYYY-MM label, count) for last n months."""
        if n is None:
            n = max(1, self._config.get("months", 12))
        now   = datetime.now()
        out   = []
        sends = self._stats.get("sends", [])
        for offset in range(n-1, -1, -1):
            # Calculate target month
            month = now.month - offset
            year  = now.year
            while month <= 0:
                month += 12
                year  -= 1
            key   = f"{year}-{month:02d}"
            label = datetime(year, month, 1).strftime("%b %y")
            count = sum(1 for s in sends if s.get("month") == key)
            out.append((label, count))
        return out

    def _webhook_data(self):
        sends = self._stats.get("sends", [])
        counts = defaultdict(int)
        for s in sends:
            if s.get("ok"):
                counts[s.get("webhook", "Unknown")] += 1
        return sorted(counts.items(), key=lambda x: -x[1])

    def _folder_data(self):
        sends = self._stats.get("sends", [])
        counts = defaultdict(int)
        for s in sends:
            if s.get("ok"):
                counts[s.get("folder", "Unknown")] += 1
        return sorted(counts.items(), key=lambda x: -x[1])

    def _error_data(self):
        errors = self._stats.get("errors", [])
        counts = defaultdict(int)
        for e in errors:
            counts[e.get("type", "Unknown")] += 1
        return sorted(counts.items(), key=lambda x: -x[1])

    def _ext_data(self):
        sends = self._stats.get("sends", [])
        counts = defaultdict(int)
        for s in sends:
            if s.get("ok"):
                counts[s.get("ext", "unknown")] += 1
        return sorted(counts.items(), key=lambda x: -x[1])

    # ── build ─────────────────────────────────

    def _build(self):
        b = self.body

        # Tab bar
        nb = ttk.Notebook(b)
        nb.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("TNotebook",       background=C["bg"],  borderwidth=0)
        style.configure("TNotebook.Tab",   background=C["bg3"], foreground=C["fg2"],
                        padding=[10, 5],   font=("Segoe UI", 9))
        style.map("TNotebook.Tab",
                  background=[("selected", C["bg2"])],
                  foreground=[("selected", C["accent"])])

        self._tab_overview  = tk.Frame(nb, bg=C["bg"])
        self._tab_webhooks  = tk.Frame(nb, bg=C["bg"])
        self._tab_folders   = tk.Frame(nb, bg=C["bg"])
        self._tab_errors    = tk.Frame(nb, bg=C["bg"])
        self._tab_recent    = tk.Frame(nb, bg=C["bg"])

        nb.add(self._tab_overview, text="  Overview  ")
        nb.add(self._tab_webhooks, text="  Webhooks  ")
        nb.add(self._tab_folders,  text="  Folders  ")
        nb.add(self._tab_errors,   text="  Errors  ")
        nb.add(self._tab_recent,   text="  Recent  ")

        self._build_overview()
        self._build_webhooks()
        self._build_folders()
        self._build_errors()
        self._build_recent()

        # Footer: close + clear
        mk_btn(self._footer_frame, "Close", self.destroy,
               color=C["bg3"], fg=C["fg2"]).pack(side="right")
        mk_btn(self._footer_frame, "Clear All Stats", self._clear_stats,
               color=C["danger"], fg="white").pack(side="left")
        mk_btn(self._footer_frame, "↻ Refresh", self._refresh_all,
               color=C["bg3"], fg=C["accent"]).pack(side="left", padx=(0, 6))

    # ── Overview tab ─────────────────────────

    def _build_overview(self):
        p = self._tab_overview

        # Summary pills row
        summary = tk.Frame(p, bg=C["bg2"], pady=8)
        summary.pack(fill="x", padx=8, pady=(8, 4))

        sends  = self._stats.get("sends", [])
        errors = self._stats.get("errors", [])
        total  = len(sends)
        ok     = sum(1 for s in sends if s.get("ok"))
        fail   = total - ok
        rate   = f"{100*ok/total:.1f}%" if total else "—"

        for val, lbl, col in [
            (str(total), "Total Sent",    C["accent"]),
            (str(ok),    "Successful",    C["accent2"]),
            (str(fail),  "Failed",        C["danger"]),
            (rate,       "Success Rate",  C["warning"]),
            (str(len(errors)), "Errors",  C["fg2"]),
        ]:
            f = tk.Frame(summary, bg=C["bg2"])
            f.pack(side="left", padx=18)
            tk.Label(f, text=val, bg=C["bg2"], fg=col,
                     font=("Segoe UI", 18, "bold")).pack()
            tk.Label(f, text=lbl, bg=C["bg2"], fg=C["fg2"],
                     font=("Segoe UI", 8)).pack()

        # Monthly bar chart
        chart_frame = tk.Frame(p, bg=C["bg"])
        chart_frame.pack(fill="both", expand=True, padx=8, pady=4)

        lbl_f = tk.Frame(chart_frame, bg=C["bg"])
        lbl_f.pack(fill="x")
        mk_label(lbl_f, "Images Sent — Last 12 Months",
                 fg=C["fg2"], font=("Segoe UI", 8, "bold")).pack(side="left", pady=(4,2))

        self._monthly_chart = BarChart(chart_frame,
            data=self._months_data(),
            color=C["accent"],
            bg=C["bg2"],
            height=220)
        self._monthly_chart.pack(fill="both", expand=True)

        # Extension pie
        ext_row = tk.Frame(p, bg=C["bg"])
        ext_row.pack(fill="x", padx=8, pady=(4, 8))

        mk_label(ext_row, "By File Type", fg=C["fg2"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 2))
        self._ext_pie = PieChart(ext_row,
            data=self._ext_data(),
            bg=C["bg2"],
            height=150)
        self._ext_pie.pack(fill="x")

    # ── Webhooks tab ─────────────────────────

    def _build_webhooks(self):
        p = self._tab_webhooks

        mk_label(p, "Images Sent per Webhook",
                 fg=C["fg2"], font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(10,2))

        self._webhook_bar = BarChart(p,
            data=self._webhook_data(),
            color=C["accent2"],
            bg=C["bg2"],
            height=220)
        self._webhook_bar.pack(fill="x", padx=8, pady=4)

        mk_label(p, "Webhook Breakdown",
                 fg=C["fg2"], font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=(6,2))

        self._webhook_tree = TreePanel(p,
            columns=("name", "sent", "failed", "rate"),
            headings=("Webhook", "Sent", "Failed", "Success Rate"),
            widths=(220, 80, 80, 120),
            height=8)
        self._webhook_tree.pack(fill="both", expand=True, padx=8, pady=4)
        self._populate_webhook_tree()

    def _populate_webhook_tree(self):
        self._webhook_tree.clear()
        sends = self._stats.get("sends", [])
        wh_stats = defaultdict(lambda: {"ok": 0, "fail": 0})
        for s in sends:
            name = s.get("webhook", "Unknown")
            if s.get("ok"):
                wh_stats[name]["ok"]   += 1
            else:
                wh_stats[name]["fail"] += 1
        for i, (name, st) in enumerate(sorted(wh_stats.items(), key=lambda x: -x[1]["ok"])):
            tot  = st["ok"] + st["fail"]
            rate = f"{100*st['ok']/tot:.1f}%" if tot else "—"
            self._webhook_tree.insert(i, (name, st["ok"], st["fail"], rate))

    # ── Folders tab ──────────────────────────

    def _build_folders(self):
        p = self._tab_folders

        mk_label(p, "Images Sent per Folder",
                 fg=C["fg2"], font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(10,2))

        self._folder_bar = BarChart(p,
            data=[(os.path.basename(l) or l, v) for l, v in self._folder_data()],
            color=C["warning"],
            bg=C["bg2"],
            height=200)
        self._folder_bar.pack(fill="x", padx=8, pady=4)

        mk_label(p, "Folder Detail",
                 fg=C["fg2"], font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=(6,2))

        self._folder_tree = TreePanel(p,
            columns=("path", "sent"),
            headings=("Folder Path", "Images Sent"),
            widths=(480, 100),
            height=8)
        self._folder_tree.pack(fill="both", expand=True, padx=8, pady=4)
        self._populate_folder_tree()

    def _populate_folder_tree(self):
        self._folder_tree.clear()
        for i, (path, cnt) in enumerate(self._folder_data()):
            self._folder_tree.insert(i, (path, cnt))

    # ── Errors tab ───────────────────────────

    def _build_errors(self):
        p = self._tab_errors

        mk_label(p, "Error Breakdown",
                 fg=C["fg2"], font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(10,2))

        err_row = tk.Frame(p, bg=C["bg"])
        err_row.pack(fill="x", padx=8, pady=4)

        self._error_pie = PieChart(err_row,
            data=self._error_data(),
            bg=C["bg2"],
            height=200)
        self._error_pie.pack(side="left", fill="both", expand=True)

        self._error_bar = BarChart(err_row,
            data=self._error_data(),
            color=C["danger"],
            bg=C["bg2"],
            height=200)
        self._error_bar.pack(side="left", fill="both", expand=True)

        mk_label(p, "Recent Errors",
                 fg=C["fg2"], font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=(6,2))

        self._error_tree = TreePanel(p,
            columns=("time", "type", "file", "webhook", "detail"),
            headings=("Time", "Type", "File", "Webhook", "Detail"),
            widths=(80, 100, 160, 120, 220),
            height=8)
        self._error_tree.pack(fill="both", expand=True, padx=8, pady=4)
        self._populate_error_tree()

    def _populate_error_tree(self):
        self._error_tree.clear()
        errors = list(reversed(self._stats.get("errors", [])))
        for i, e in enumerate(errors[:200]):
            self._error_tree.insert(i, (
                e.get("time",    ""),
                e.get("type",    ""),
                e.get("file",    ""),
                e.get("webhook", ""),
                e.get("detail",  ""),
            ))

    # ── Recent tab ───────────────────────────

    def _build_recent(self):
        p = self._tab_recent

        hdr = tk.Frame(p, bg=C["bg"])
        hdr.pack(fill="x", padx=8, pady=(10,2))
        mk_label(hdr, "Recent Sends (latest 500)",
                 fg=C["fg2"], font=("Segoe UI", 9, "bold")).pack(side="left")

        sends = self._stats.get("sends", [])
        ok    = sum(1 for s in sends if s.get("ok"))
        fail  = len(sends) - ok
        mk_label(hdr, f"  {ok} ok  |  {fail} failed",
                 fg=C["fg2"], font=("Segoe UI", 8)).pack(side="left", padx=8)

        self._recent_tree = TreePanel(p,
            columns=("time", "file", "webhook", "folder", "ext", "status"),
            headings=("Time", "File", "Webhook", "Folder", "Ext", "Status"),
            widths=(90, 200, 120, 140, 50, 70),
            height=22)
        self._recent_tree.pack(fill="both", expand=True, padx=8, pady=4)
        self._populate_recent_tree()

    def _populate_recent_tree(self):
        self._recent_tree.clear()
        sends = list(reversed(self._stats.get("sends", [])))
        for i, s in enumerate(sends[:500]):
            status = "✓ OK" if s.get("ok") else "✗ Fail"
            folder = os.path.basename(s.get("folder","")) or s.get("folder","")
            self._recent_tree.insert(i, (
                s.get("time",    ""),
                s.get("file",    ""),
                s.get("webhook", ""),
                folder,
                s.get("ext",    ""),
                status,
            ))

    # ── Actions ──────────────────────────────

    def _refresh_all(self):
        self._monthly_chart.update_data(self._months_data())
        self._ext_pie.update_data(self._ext_data())
        self._webhook_bar.update_data(self._webhook_data())
        self._populate_webhook_tree()
        self._folder_bar.update_data(
            [(os.path.basename(l) or l, v) for l, v in self._folder_data()])
        self._populate_folder_tree()
        self._error_pie.update_data(self._error_data())
        self._error_bar.update_data(self._error_data())
        self._populate_error_tree()
        self._populate_recent_tree()

    def _clear_stats(self):
        if messagebox.askyesno("Clear Stats",
                               "Delete ALL statistics history? This cannot be undone.",
                               parent=self):
            self._stats["sends"]  = []
            self._stats["errors"] = []
            self._refresh_all()


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────

class WIS:
    def __init__(self, root):
        self.root = root
        self.root.title("WIS — Webhook Image Sender")
        self.root.minsize(720, 540)
        self.root.geometry("820x640")

        self.settings_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "wis_settings.json")

        self.webhooks: list = []
        self.folders:  list = []
        self.settings: dict = dict(DEFAULTS)

        self.auto_start = tk.BooleanVar()
        self.debug_mode = tk.BooleanVar(value=False)

        self.is_monitoring     = False
        self.monitoring_thread = None
        self.sent_files: set   = set()
        self._sent_count       = 0
        self._fail_count       = 0

        # Statistics
        self._stats_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "wis_stats.json")
        self._stats: dict = {"sends": [], "errors": []}
        self._stats_config: dict = {
            "max_sends":      10000,
            "max_errors":     2000,
            "months":         12,
            "autosave_every": 10,
        }

        # Custom user-saved themes (name -> colour dict)
        self._custom_themes: dict = {}

        self.load_settings()
        self._load_stats()

        C.update({k: self.settings[k] for k in DEFAULTS if k in self.settings})
        self.root.configure(bg=C["bg"])
        apply_treeview_style()

        self._build_ui()

        if self.auto_start.get() and self._ready():
            self.root.after(1000, self.start_monitoring)

    # ── UI ──────────────────────────────────────

    def _build_ui(self):
        # Title bar
        tb = tk.Frame(self.root, bg=C["bg2"])
        tb.pack(fill="x", side="top")
        mk_label(tb, "WIS", fg=C["accent"], bg=C["bg2"],
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=16, pady=8)
        mk_label(tb, "Webhook Image Sender", fg=C["fg2"], bg=C["bg2"],
                 font=("Segoe UI", 10)).pack(side="left")
        self._status_pill = mk_label(tb, "  IDLE  ", fg=C["fg2"], bg=C["bg3"],
                                     font=("Segoe UI", 8, "bold"))
        self._status_pill.pack(side="right", padx=16, pady=8, ipadx=6, ipady=3)

        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x", side="top")

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=C["bg"], width=270)
        left.pack(side="left", fill="y", padx=14, pady=12)
        left.pack_propagate(False)
        self._build_left(left)

        right = tk.Frame(body, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True, padx=(0, 14), pady=12)
        self._build_right(right)

    def _build_left(self, p):
        mk_section(p, "MONITORED FOLDERS")
        self._folder_lbl = tk.Label(p, text=self._folder_summary(),
                                    bg=C["bg2"], fg=C["fg"], font=("Segoe UI", 9),
                                    wraplength=250, justify="left",
                                    padx=8, pady=6, anchor="nw")
        self._folder_lbl.pack(fill="x", pady=(0, 4))
        mk_btn(p, "Manage Folders", self._open_folders,
               color=C["bg3"], fg=C["accent"]).pack(fill="x", pady=2)

        tk.Frame(p, bg=C["bg"], height=10).pack()

        mk_section(p, "WEBHOOKS")
        self._webhook_lbl = tk.Label(p, text=self._webhook_summary(),
                                     bg=C["bg2"], fg=C["fg"], font=("Segoe UI", 9),
                                     wraplength=250, justify="left",
                                     padx=8, pady=6, anchor="nw")
        self._webhook_lbl.pack(fill="x", pady=(0, 4))
        mk_btn(p, "Manage Webhooks", self._open_webhooks,
               color=C["bg3"], fg=C["accent"]).pack(fill="x", pady=2)

        tk.Frame(p, bg=C["bg"], height=10).pack()
        mk_btn(p, "Settings", self._open_settings,
               color=C["bg3"], fg=C["fg"]).pack(fill="x", pady=2)
        mk_btn(p, "Statistics", self._open_stats,
               color=C["bg3"], fg=C["accent"]).pack(fill="x", pady=2)

        tk.Frame(p, bg=C["bg"], height=8).pack()

        self.start_btn = mk_btn(p, "Start Monitoring", self.start_monitoring,
                                color=C["accent2"], fg=C["bg"])
        self.start_btn.pack(fill="x", pady=3)

        self.stop_btn = mk_btn(p, "Stop Monitoring", self.stop_monitoring,
                               color=C["danger"], fg="white")
        self.stop_btn.pack(fill="x", pady=3)
        self.stop_btn.config(state="disabled")

    def _build_right(self, p):
        hdr = tk.Frame(p, bg=C["bg"])
        hdr.pack(fill="x", pady=(0, 6))
        mk_label(hdr, "ACTIVITY LOG", fg=C["fg2"],
                 font=("Segoe UI", 7, "bold")).pack(side="left")
        mk_btn(hdr, "Clear", self.clear_log,
               color=C["bg3"], fg=C["fg2"]).pack(side="right")

        stats = tk.Frame(p, bg=C["bg2"], pady=6)
        stats.pack(fill="x", pady=(0, 6))
        self._s_sent  = self._pill(stats, "0", "Sent")
        self._s_fail  = self._pill(stats, "0", "Failed")
        self._s_hooks = self._pill(stats, "0", "Webhooks")
        self._s_dirs  = self._pill(stats, "0", "Folders")
        self._refresh_stats()

        log_wrap = tk.Frame(p, bg=C["bg3"],
                            highlightthickness=1, highlightbackground=C["border"])
        log_wrap.pack(fill="both", expand=True)

        self.log_box = tk.Text(log_wrap, bg=C["bg3"], fg=C["fg"],
                               insertbackground=C["accent"],
                               relief="flat", bd=0,
                               font=("Consolas", 9), wrap="word",
                               state="disabled")
        self.log_box.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        sb = ttk.Scrollbar(log_wrap, orient="vertical", command=self.log_box.yview)
        sb.pack(side="right", fill="y")
        self.log_box.configure(yscrollcommand=sb.set)

        self.log_box.tag_config("ok",    foreground=C["accent2"])
        self.log_box.tag_config("err",   foreground=C["danger"])
        self.log_box.tag_config("warn",  foreground=C["warning"])
        self.log_box.tag_config("info",  foreground=C["accent"])
        self.log_box.tag_config("debug", foreground=C["fg2"])
        self.log_box.tag_config("ts",    foreground=C["fg2"])

    def _pill(self, parent, value, label):
        f = tk.Frame(parent, bg=C["bg2"])
        f.pack(side="left", padx=14)
        v = mk_label(f, value, fg=C["accent"], bg=C["bg2"],
                     font=("Segoe UI", 16, "bold"))
        v.pack()
        mk_label(f, label, fg=C["fg2"], bg=C["bg2"],
                 font=("Segoe UI", 8)).pack()
        return v

    # ── Summaries ──────────────────────────────

    def _folder_summary(self):
        enabled = [f for f in self.folders if f.get("enabled", True)]
        if not self.folders: return "No folders configured"
        if not enabled:      return "All folders disabled"
        lines = []
        for f in enabled[:4]:
            rec = " (recursive)" if f.get("recursive") else ""
            name = os.path.basename(f["path"]) or f["path"]
            lines.append(f"• {name}{rec}")
        if len(enabled) > 4:
            lines.append(f"  +{len(enabled)-4} more")
        return "\n".join(lines)

    def _webhook_summary(self):
        enabled = [w for w in self.webhooks if w.get("enabled", True)]
        if not self.webhooks: return "No webhooks configured"
        if not enabled:       return "All webhooks disabled"
        lines = [f"• {w.get('name','Unnamed')}" for w in enabled[:4]]
        if len(enabled) > 4: lines.append(f"  +{len(enabled)-4} more")
        return "\n".join(lines)

    def _refresh_stats(self):
        self._s_hooks.config(text=str(sum(1 for w in self.webhooks if w.get("enabled", True))))
        self._s_dirs.config( text=str(sum(1 for f in self.folders  if f.get("enabled", True))))

    # ── Sub-windows ────────────────────────────

    def _open_folders(self):
        def on_save(v):
            self.folders = v
            self.save_settings()
            self._folder_lbl.config(text=self._folder_summary())
            self._refresh_stats()
            self.log("Folder list updated", "info")
        FolderManager(self.root, self.folders, on_save)

    def _open_webhooks(self):
        def on_save(v):
            self.webhooks = v
            self.save_settings()
            self._webhook_lbl.config(text=self._webhook_summary())
            self._refresh_stats()
            self.log("Webhook list updated", "info")
        WebhookManager(self.root, self.webhooks, on_save)

    def _open_settings(self):
        def on_save(new_s):
            self.settings.update(new_s)
            C.update(new_s)
            apply_treeview_style()
            self.save_settings()
            self.log("Settings saved — restart to fully apply colour changes", "warn")

        def on_save_extra(new_stats_cfg):
            self._stats_config.update(new_stats_cfg)
            self.save_settings()

        SettingsManager(self.root, self.settings, on_save,
                        auto_start=self.auto_start,
                        debug_mode=self.debug_mode,
                        stats_config=self._stats_config,
                        on_save_extra=on_save_extra,
                        custom_themes=self._custom_themes,
                        on_themes_save=lambda t: (self._custom_themes.update(t), self.save_settings()))

    def _open_stats(self):
        StatsWindow(self.root, self._stats, self._stats_config)

    # ── Logging ────────────────────────────────

    def log(self, message, kind="info"):
        icons = {"ok": "✓", "err": "✗", "warn": "!", "info": "·", "debug": ">"}
        ts   = time.strftime("%H:%M:%S")
        icon = icons.get(kind, "·")
        self.log_box.config(state="normal")
        self.log_box.insert("end", f"[{ts}] ", "ts")
        self.log_box.insert("end", f"{icon} {message}\n", kind)
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    # ── Persistence ────────────────────────────

    def load_settings(self):
        try:
            # Legacy migration: rename old settings file
            old_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webhook_settings.json")
            if os.path.exists(old_file) and not os.path.exists(self.settings_file):
                os.rename(old_file, self.settings_file)
            if not os.path.exists(self.settings_file):
                return
            with open(self.settings_file) as f:
                s = json.load(f)
            self.webhooks = s.get("webhooks", [])
            self.folders  = s.get("folders",  [])
            self.auto_start.set(s.get("auto_start", False))
            self.debug_mode.set(s.get("debug_mode", False))
            for k in DEFAULTS:
                if k in s:
                    self.settings[k] = s[k]
            sc = s.get("stats_config", {})
            for k in self._stats_config:
                if k in sc:
                    self._stats_config[k] = sc[k]
            self._custom_themes = s.get("custom_themes", {})
            # Legacy migration
            if not self.webhooks and s.get("webhook_url"):
                self.webhooks = [{"name": "Default", "url": s["webhook_url"], "enabled": True}]
            if not self.folders and s.get("folder_path"):
                self.folders = [{"path": s["folder_path"], "enabled": True, "recursive": False}]
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            s = {"webhooks": self.webhooks, "folders": self.folders,
                 "auto_start": self.auto_start.get(),
                 "debug_mode": self.debug_mode.get(),
                 "stats_config": self._stats_config,
                 "custom_themes": self._custom_themes}
            s.update(self.settings)
            with open(self.settings_file, "w") as f:
                json.dump(s, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def _load_stats(self):
        try:
            if os.path.exists(self._stats_file):
                with open(self._stats_file) as f:
                    data = json.load(f)
                self._stats["sends"]  = data.get("sends",  [])
                self._stats["errors"] = data.get("errors", [])
        except Exception as e:
            print(f"Error loading stats: {e}")

    def _save_stats(self):
        try:
            max_s = self._stats_config.get("max_sends",  10000)
            max_e = self._stats_config.get("max_errors",  2000)
            self._stats["sends"]  = self._stats["sends"][-max(1, max_s):]
            self._stats["errors"] = self._stats["errors"][-max(1, max_e):]
            with open(self._stats_file, "w") as f:
                json.dump(self._stats, f)
        except Exception as e:
            print(f"Error saving stats: {e}")

    # ── Monitoring ─────────────────────────────

    def _ready(self):
        af = [f for f in self.folders  if f.get("enabled") and os.path.isdir(f.get("path",""))]
        aw = [w for w in self.webhooks if w.get("enabled") and w.get("url")]
        return bool(af) and bool(aw)

    def _formats(self):
        raw = self.settings.get("formats", DEFAULTS["formats"])
        return {e.strip().lower() for e in raw.split(",") if e.strip()}

    def start_monitoring(self):
        active_folders  = [f for f in self.folders  if f.get("enabled", True)]
        active_webhooks = [w for w in self.webhooks if w.get("enabled", True) and w.get("url")]

        if not active_folders:
            self.log("No folders configured.", "warn"); return
        if not active_webhooks:
            self.log("No webhooks configured.", "warn"); return

        valid = [f for f in active_folders if os.path.isdir(f.get("path", ""))]
        for f in active_folders:
            if f not in valid:
                self.log(f"Folder not found, skipping: {f['path']}", "warn")
        if not valid:
            self.log("No valid folders found.", "err"); return

        self._sent_count = 0
        self._fail_count = 0
        self._s_sent.config(text="0")
        self._s_fail.config(text="0")
        self.sent_files.clear()

        self.is_monitoring = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self._status_pill.config(text="  MONITORING  ", bg="#1a3320", fg=C["accent2"])

        self._snapshot(valid)

        self.monitoring_thread = Thread(
            target=self._loop, args=(valid, active_webhooks), daemon=True)
        self.monitoring_thread.start()

        names = ", ".join(w["name"] for w in active_webhooks)
        self.log(f"Started — {len(valid)} folder(s) → {len(active_webhooks)} webhook(s): {names}", "ok")

    def stop_monitoring(self):
        self.is_monitoring = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self._status_pill.config(text="  STOPPED  ", bg="#2a1a1a", fg=C["danger"])
        self.log("Monitoring stopped", "warn")
        self._save_stats()

    def _snapshot(self, folders):
        fmts = self._formats()
        count = 0
        for fc in folders:
            for fp in self._iter_images(fc["path"], fc.get("recursive", False), fmts):
                self.sent_files.add(os.path.abspath(fp))
                count += 1
        self.log(f"Snapshot: {count} existing file(s) marked as seen", "debug")

    def _iter_images(self, root, recursive, fmts):
        if recursive:
            for dirpath, _, files in os.walk(root):
                for fn in files:
                    if os.path.splitext(fn)[1].lower() in fmts:
                        yield os.path.join(dirpath, fn)
        else:
            try:
                for fn in os.listdir(root):
                    fp = os.path.join(root, fn)
                    if os.path.isfile(fp) and os.path.splitext(fn)[1].lower() in fmts:
                        yield fp
            except Exception:
                pass

    def _loop(self, folders, webhooks):
        fmts       = self._formats()
        scan_rate  = float(self.settings.get("scan_rate",  1.0))
        file_delay = float(self.settings.get("file_delay", 0.8))
        scan = 0
        while self.is_monitoring:
            scan += 1
            if self.debug_mode.get():
                self.log(f"Scan #{scan}", "debug")
            for fc in folders:
                try:
                    for fp in self._iter_images(fc["path"], fc.get("recursive", False), fmts):
                        abs_fp = os.path.abspath(fp)
                        if abs_fp in self.sent_files:
                            continue
                        rel = os.path.relpath(abs_fp, fc["path"])
                        self.log(f"New: {rel}  [{os.path.basename(fc['path'])}]", "info")
                        time.sleep(file_delay)
                        if not os.path.exists(abs_fp):
                            continue
                        try:
                            if os.path.getsize(abs_fp) == 0:
                                self.log(f"Empty, skipping: {rel}", "warn")
                                continue
                        except Exception:
                            continue
                        all_ok = all(self._send(abs_fp, wh, fc["path"]) for wh in webhooks)
                        self.sent_files.add(abs_fp)
                        self._play_sound(all_ok)
                        if all_ok: self._sent_count += 1
                        else:      self._fail_count += 1
                        self.root.after(0, lambda sc=self._sent_count, fc=self._fail_count: (
                            self._s_sent.config(text=str(sc)),
                            self._s_fail.config(text=str(fc))
                        ))
                except Exception as e:
                    self.log(f"Error scanning {fc['path']}: {e}", "err")
            time.sleep(scan_rate)

    def _play_sound(self, ok: bool):
        """Play validation.mp3 on success or exclamation.mp3 on failure (background thread)."""
        if not _AUDIO_OK:
            return
        if not self.settings.get("sound_enabled", True):
            return
        fname = "validation.mp3" if ok else "exclamation.mp3"
        path  = os.path.join(_SCRIPT_DIR, fname)
        if not os.path.isfile(path):
            return
        def _play():
            try:
                vol = float(self.settings.get("sound_volume", 0.8))
                vol = max(0.0, min(1.0, vol))
                sound = pygame.mixer.Sound(path)
                sound.set_volume(vol)
                sound.play()
            except Exception as e:
                self.log(f"Sound error: {e}", "debug")
        Thread(target=_play, daemon=True).start()

    def _send(self, file_path, webhook, folder_path=""):
        fname   = os.path.basename(file_path)
        name    = webhook.get("name", "?")
        url     = webhook.get("url", "")
        timeout = int(self.settings.get("send_timeout", 30))
        mime, _ = mimetypes.guess_type(file_path)
        mime    = mime or "application/octet-stream"
        ext     = os.path.splitext(fname)[1].lower()
        ts      = time.strftime("%H:%M:%S")
        month   = time.strftime("%Y-%m")

        def _record(ok, err_type="", detail=""):
            entry = {
                "time":    ts,
                "month":   month,
                "file":    fname,
                "webhook": name,
                "folder":  folder_path,
                "ext":     ext,
                "ok":      ok,
            }
            self._stats["sends"].append(entry)
            if not ok:
                self._stats["errors"].append({
                    "time":    ts,
                    "type":    err_type,
                    "file":    fname,
                    "webhook": name,
                    "detail":  detail,
                })
            # Save stats every N sends (configured in Settings → Statistics)
            every = max(1, self._stats_config.get("autosave_every", 10))
            if len(self._stats["sends"]) % every == 0:
                Thread(target=self._save_stats, daemon=True).start()

        try:
            with open(file_path, "rb") as fh:
                r = requests.post(url, files={"file": (fname, fh, mime)}, timeout=timeout)
            if r.status_code in (200, 201, 204):
                self.log(f"{fname}  →  {name}", "ok")
                _record(True)
                return True
            detail = f"HTTP {r.status_code}"
            self.log(f"{detail}  {fname}  →  {name}", "err")
            _record(False, err_type=f"HTTP {r.status_code}", detail=detail)
            return False
        except requests.exceptions.Timeout as e:
            self.log(f"Timeout  {fname}  →  {name}", "err")
            _record(False, err_type="Timeout", detail=str(e)[:120])
            return False
        except requests.exceptions.ConnectionError as e:
            self.log(f"Connection error  {fname}  →  {name}", "err")
            _record(False, err_type="Connection Error", detail=str(e)[:120])
            return False
        except Exception as e:
            self.log(f"Error  {fname}  →  {name}: {e}", "err")
            _record(False, err_type=type(e).__name__, detail=str(e)[:120])
            return False


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

def main():
    root = tk.Tk()
    WIS(root)
    root.mainloop()


if __name__ == "__main__":
    main()