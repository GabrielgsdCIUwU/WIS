import tkinter as tk
from tkinter import messagebox
from typing import Callable, List

from core.config import C
from ui.components.factory import mk_btn, mk_entry, mk_label, mk_chk
from ui.components.factory import BasePopup
from ui.components.tree_panel import TreePanel
from ui.dialogs.profile_manager import SharedProfileManager


class WebhookManager(BasePopup):
    def __init__(self, parent, webhooks: list, profiles: list, on_save: Callable):
        super().__init__(parent, "Webhook Manager",
                         "One detection is sent to all enabled webhooks", size="620x600")
        self.webhooks  = [dict(w) for w in webhooks]
        self.profiles  = profiles
        self.on_save   = on_save
        self._edit_idx = None
        self._build()
        self._refresh()

    def _profile_names(self) -> List[str]:
        return [p["name"] for p in self.profiles]

    def _build(self):
        b = self.body
        top = tk.Frame(b, bg=C["bg"])
        top.pack(fill="x", side="top")
        self.panel = TreePanel(top, columns=("on", "name", "profile", "url"),
                               headings=("On", "Name", "Shared Profile", "URL"),
                               widths=(44, 120, 120, 260), height=7)
        self.panel.pack(fill="x")
        act = tk.Frame(top, bg=C["bg"])
        act.pack(fill="x", pady=(4, 0))
        mk_btn(act, "Edit",   self._edit,   color=C["bg3"], fg=C["accent"]).pack(side="left", padx=(0, 4))
        mk_btn(act, "Toggle", self._toggle, color=C["bg3"], fg=C["warning"]).pack(side="left", padx=4)
        mk_btn(act, "Remove", self._remove, color=C["bg3"], fg=C["danger"]).pack(side="left", padx=4)
        tk.Frame(b, bg=C["border"], height=1).pack(fill="x", pady=8, side="top")
        bottom = tk.Frame(b, bg=C["bg"])
        bottom.pack(fill="x", side="top")
        mk_label(bottom, "Add / Edit Webhook", fg=C["accent"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 6))
        name_row = tk.Frame(bottom, bg=C["bg"])
        name_row.pack(fill="x", pady=2)
        mk_label(name_row, "Name:", fg=C["fg2"], width=6, anchor="w").pack(side="left")
        self._name_var = tk.StringVar()
        mk_entry(name_row, textvariable=self._name_var, width=26).pack(side="left", padx=(4, 0))
        url_row = tk.Frame(bottom, bg=C["bg"])
        url_row.pack(fill="x", pady=2)
        mk_label(url_row, "URL:", fg=C["fg2"], width=6, anchor="w").pack(side="left")
        self._url_var = tk.StringVar()
        mk_entry(url_row, textvariable=self._url_var, width=56).pack(
            side="left", padx=(4, 0), fill="x", expand=True)
        tk.Frame(bottom, bg=C["border"], height=1).pack(fill="x", pady=(8, 4))
        mk_label(bottom, "Shared Profile  (optional)", fg=C["accent2"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        sp_row = tk.Frame(bottom, bg=C["bg"])
        sp_row.pack(fill="x", pady=(4, 0))
        self._sp_enabled_var = tk.BooleanVar(value=False)
        self._sp_chk = mk_chk(sp_row, "Enable shared profile for this webhook",
                               self._sp_enabled_var, command=self._on_sp_toggle, bg=C["bg"])
        self._sp_chk.pack(side="left")
        sp_pick_row = tk.Frame(bottom, bg=C["bg"])
        sp_pick_row.pack(fill="x", pady=(4, 2))
        mk_label(sp_pick_row, "Profile:", fg=C["fg2"], width=8, anchor="w").pack(side="left")
        names = self._profile_names()
        self._sp_var = tk.StringVar(value=names[0] if names else "")
        self._sp_menu = tk.OptionMenu(sp_pick_row, self._sp_var, *(names or ["— no profiles —"]))
        self._sp_menu.config(bg=C["bg3"], fg=C["fg"], activebackground=C["bg2"],
                             activeforeground=C["accent"], highlightthickness=0,
                             relief="flat", font=("Segoe UI", 9), bd=0, width=20)
        self._sp_menu["menu"].config(bg=C["bg3"], fg=C["fg"], font=("Segoe UI", 9))
        self._sp_menu.pack(side="left", padx=(4, 0))
        mk_btn(sp_pick_row, "+ Manage Profiles", self._open_profile_manager,
               color=C["bg3"], fg=C["accent2"]).pack(side="left", padx=(8, 0))
        mk_label(bottom,
                 "The selected profile's username & avatar will override the webhook's default identity.",
                 fg=C["fg2"], font=("Segoe UI", 7)).pack(anchor="w", pady=(2, 0))
        self._on_sp_toggle()
        btn_row = tk.Frame(bottom, bg=C["bg"])
        btn_row.pack(fill="x", pady=(10, 0))
        self._add_btn = mk_btn(btn_row, "+ Add", self._commit, color=C["accent2"], fg=C["bg"])
        self._add_btn.pack(side="left")
        mk_btn(btn_row, "Clear", self._clear_form, color=C["bg3"], fg=C["fg2"]).pack(side="left", padx=8)
        self.add_footer_buttons(self._save)

    def _on_sp_toggle(self):
        state = "normal" if self._sp_enabled_var.get() else "disabled"
        self._sp_menu.config(state=state)

    def _rebuild_sp_menu(self):
        names = self._profile_names()
        menu = self._sp_menu["menu"]
        menu.delete(0, "end")
        for n in names:
            menu.add_command(label=n, command=lambda v=n: self._sp_var.set(v))
        if names:
            if self._sp_var.get() not in names:
                self._sp_var.set(names[0])
        else:
            self._sp_var.set("")

    def _open_profile_manager(self):
        def on_save(profiles):
            self.profiles[:] = profiles
            self._rebuild_sp_menu()
        SharedProfileManager(self, self.profiles, on_save)

    def _refresh(self):
        self.panel.clear()
        for i, w in enumerate(self.webhooks):
            profile_label = ""
            if w.get("shared_profile_enabled") and w.get("shared_profile"):
                profile_label = f"✔ {w['shared_profile']}"
            self.panel.insert(i, ("✔" if w.get("enabled", True) else "—",
                                  w.get("name", ""), profile_label, w.get("url", "")))

    def _edit(self):
        idx = self.panel.selected_idx()
        if idx is None: return
        w = self.webhooks[idx]
        self._name_var.set(w.get("name", ""))
        self._url_var.set(w.get("url", ""))
        self._sp_enabled_var.set(bool(w.get("shared_profile_enabled")))
        sp = w.get("shared_profile", "")
        names = self._profile_names()
        if sp and sp in names:
            self._sp_var.set(sp)
        elif names:
            self._sp_var.set(names[0])
        self._on_sp_toggle()
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
        sp_enabled = self._sp_enabled_var.get()
        sp_name    = self._sp_var.get() if sp_enabled else ""
        if sp_enabled and not self._profile_names():
            messagebox.showwarning("No Profiles",
                "No shared profiles exist yet.\nCreate one via Settings -> Shared Profiles.",
                parent=self); return
        entry = {"name": name, "url": url, "enabled": True,
                 "shared_profile_enabled": sp_enabled, "shared_profile": sp_name}
        if self._edit_idx is not None:
            entry["enabled"] = self.webhooks[self._edit_idx].get("enabled", True)
            self.webhooks[self._edit_idx] = entry
            self._edit_idx = None
        else:
            self.webhooks.append(entry)
        self._clear_form()
        self._refresh()

    def _clear_form(self):
        self._name_var.set("")
        self._url_var.set("")
        self._sp_enabled_var.set(False)
        self._on_sp_toggle()
        self._edit_idx = None
        self._add_btn.config(text="+ Add")

    def _save(self):
        try:    self.on_save(self.webhooks)
        finally: self.destroy()
