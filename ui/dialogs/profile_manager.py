import tkinter as tk
from tkinter import messagebox
from typing import Callable

from core.config import C
from ui.components.factory import BasePopup, mk_btn, mk_entry, mk_label
from ui.components.tree_panel import TreePanel


class SharedProfileManager(BasePopup):
    """Manage named identity profiles (username + avatar URL) for shared webhooks."""

    def __init__(self, parent, profiles: list, on_save: Callable):
        super().__init__(parent, "Shared Profiles",
                         "Identities that override a webhook's default appearance",
                         size="580x540")
        self.profiles  = [dict(p) for p in profiles]
        self.on_save   = on_save
        self._edit_idx = None
        self._build()
        self._refresh()

    def _build(self):
        b = self.body
        top = tk.Frame(b, bg=C["bg"])
        top.pack(fill="x", side="top")
        self.panel = TreePanel(top,
            columns=("name", "username", "avatar"),
            headings=("Profile Name", "Display Username", "Avatar URL"),
            widths=(130, 140, 260), height=6)
        self.panel.pack(fill="x")
        act = tk.Frame(top, bg=C["bg"])
        act.pack(fill="x", pady=(4, 0))
        mk_btn(act, "Edit",   self._edit,   color=C["bg3"], fg=C["accent"]).pack(side="left", padx=(0, 4))
        mk_btn(act, "Remove", self._remove, color=C["bg3"], fg=C["danger"]).pack(side="left", padx=4)
        tk.Frame(b, bg=C["border"], height=1).pack(fill="x", pady=8, side="top")
        bottom = tk.Frame(b, bg=C["bg"])
        bottom.pack(fill="x", side="top")
        mk_label(bottom, "Add / Edit Profile", fg=C["accent"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 6))
        for label, attr in [("Profile name:",    "_pname_var"),
                             ("Display username:", "_pusername_var"),
                             ("Avatar image URL:", "_pavatar_var")]:
            row = tk.Frame(bottom, bg=C["bg"])
            row.pack(fill="x", pady=2)
            mk_label(row, label, fg=C["fg2"], width=18, anchor="w").pack(side="left")
            var = tk.StringVar()
            setattr(self, attr, var)
            mk_entry(row, textvariable=var, width=42).pack(side="left", padx=(4, 0),
                                                            fill="x", expand=True)
        mk_label(bottom,
                 "Avatar URL must be a direct image link (https://…).  Leave blank to keep default.",
                 fg=C["fg2"], font=("Segoe UI", 7)).pack(anchor="w", pady=(4, 0))
        btn_row = tk.Frame(bottom, bg=C["bg"])
        btn_row.pack(fill="x", pady=(8, 0))
        self._add_btn = mk_btn(btn_row, "+ Add", self._commit, color=C["accent2"], fg=C["bg"])
        self._add_btn.pack(side="left")
        mk_btn(btn_row, "Clear", self._clear_form, color=C["bg3"], fg=C["fg2"]).pack(side="left", padx=8)
        self.add_footer_buttons(self._save)

    def _refresh(self):
        self.panel.clear()
        for i, p in enumerate(self.profiles):
            self.panel.insert(i, (p.get("name", ""), p.get("username", ""), p.get("avatar_url", "")))

    def _edit(self):
        idx = self.panel.selected_idx()
        if idx is None: return
        p = self.profiles[idx]
        self._pname_var.set(p.get("name", ""))
        self._pusername_var.set(p.get("username", ""))
        self._pavatar_var.set(p.get("avatar_url", ""))
        self._edit_idx = idx
        self._add_btn.config(text="Update")

    def _remove(self):
        idx = self.panel.selected_idx()
        if idx is None: return
        name = self.profiles[idx].get("name", "this profile")
        if messagebox.askyesno("Remove", f"Remove profile '{name}'?", parent=self):
            del self.profiles[idx]
            self._refresh()

    def _commit(self):
        name     = self._pname_var.get().strip()
        username = self._pusername_var.get().strip()
        avatar   = self._pavatar_var.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Enter a profile name.", parent=self); return
        if not username:
            messagebox.showwarning("Missing", "Enter a display username.", parent=self); return
        if avatar and not avatar.startswith("http"):
            messagebox.showwarning("Invalid URL", "Avatar URL must start with http.", parent=self); return
        if self._edit_idx is not None:
            self.profiles[self._edit_idx].update(name=name, username=username, avatar_url=avatar)
            self._edit_idx = None
        else:
            if name in {p["name"] for p in self.profiles}:
                messagebox.showwarning("Duplicate", f"A profile named '{name}' already exists.", parent=self); return
            self.profiles.append({"name": name, "username": username, "avatar_url": avatar})
        self._clear_form()
        self._refresh()

    def _clear_form(self):
        self._pname_var.set("")
        self._pusername_var.set("")
        self._pavatar_var.set("")
        self._edit_idx = None
        self._add_btn.config(text="+ Add")

    def _save(self):
        try:    self.on_save(self.profiles)
        finally: self.destroy()
