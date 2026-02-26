import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable

from core.config import C
from ui.components.factory import mk_btn, mk_entry, mk_label, mk_chk
from ui.components.factory import BasePopup
from ui.components.tree_panel import TreePanel

class FolderManager(BasePopup):
    def __init__(self, parent, folders: list, on_save: Callable):
        super().__init__(parent, "Folder Manager",
                         "All enabled folders are scanned simultaneously", size="640x540")
        self.folders = [dict(f) for f in folders]
        self.on_save = on_save
        self._build()
        self._refresh()

    def _build(self):
        b = self.body
        top = tk.Frame(b, bg=C["bg"])
        top.pack(fill="x", side="top")
        self.panel = TreePanel(top, columns=("on", "rec", "path"),
                               headings=("On", "Recursive", "Folder Path"),
                               widths=(44, 80, 440), height=7)
        self.panel.pack(fill="x")
        act = tk.Frame(top, bg=C["bg"])
        act.pack(fill="x", pady=(4, 0))
        mk_btn(act, "Toggle",           self._toggle,     color=C["bg3"], fg=C["warning"]).pack(side="left", padx=(0, 4))
        mk_btn(act, "Toggle Recursive", self._toggle_rec, color=C["bg3"], fg=C["accent"]).pack(side="left", padx=4)
        mk_btn(act, "Remove",           self._remove,     color=C["bg3"], fg=C["danger"]).pack(side="left", padx=4)
        tk.Frame(b, bg=C["border"], height=1).pack(fill="x", pady=8, side="top")
        bottom = tk.Frame(b, bg=C["bg"])
        bottom.pack(fill="x", side="top")
        mk_label(bottom, "Add Folder", fg=C["accent"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 8))
        path_row = tk.Frame(bottom, bg=C["bg"])
        path_row.pack(fill="x", pady=(0, 6))
        self._path_var = tk.StringVar()
        mk_btn(path_row, "Browse", self._browse, color=C["bg3"], fg=C["fg"]).pack(side="right", padx=(6, 0))
        mk_entry(path_row, textvariable=self._path_var, width=2).pack(side="left", fill="x", expand=True)
        self._recursive_var = tk.BooleanVar(value=True)
        mk_chk(bottom, "Recursive (include subfolders)", self._recursive_var, bg=C["bg"]).pack(anchor="w", pady=(0, 8))
        add_frame = tk.Frame(bottom, bg=C["bg"])
        add_frame.pack(fill="x")
        mk_btn(add_frame, "+ Add Folder", self._add, color=C["accent2"], fg=C["bg"]).pack(side="left")
        self.add_footer_buttons(self._save)

    def _refresh(self):
        self.panel.clear()
        for i, f in enumerate(self.folders):
            self.panel.insert(i, (
                "✔" if f.get("enabled",   True)  else "—",
                "✔" if f.get("recursive", False) else "—",
                f.get("path", ""),
            ))

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
            messagebox.showwarning("Missing", "Select or type a folder path.", parent=self); return
        if not os.path.isdir(path):
            messagebox.showwarning("Invalid", f"Not a valid directory:\n{path}", parent=self); return
        if path in {f["path"] for f in self.folders}:
            messagebox.showinfo("Duplicate", "This folder is already in the list.", parent=self); return
        self.folders.append({"path": path, "enabled": True, "recursive": self._recursive_var.get()})
        self._path_var.set("")
        self._refresh()

    def _save(self):
        try:    self.on_save(self.folders)
        finally: self.destroy()
