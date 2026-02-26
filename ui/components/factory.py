"""
ui/components/factory.py
------------------------
Central UI factory utilities and BasePopup class.
"""

import tkinter as tk

from core.config import C
from ui.styles.theme_manager import mk_btn, mk_label


# ------------------------------------------------------------------
# Additional themed components
# ------------------------------------------------------------------

def mk_entry(parent, **kwargs):
    entry = tk.Entry(
        parent,
        bg=C["bg3"],
        fg=C["fg"],
        insertbackground=C["fg"],
        relief="flat",
        highlightthickness=1,
        highlightbackground=C["border"],
        highlightcolor=C["accent"],
        **kwargs
    )
    return entry


def mk_chk(parent, text, variable, **kwargs):
    chk = tk.Checkbutton(
        parent,
        text=text,
        variable=variable,
        bg=C["bg"],
        fg=C["fg"],
        activebackground=C["bg"],
        activeforeground=C["fg"],
        selectcolor=C["bg3"],
        highlightthickness=0,
        bd=0,
        **kwargs
    )
    return chk


# ------------------------------------------------------------------
# Base popup window
# ------------------------------------------------------------------

class BasePopup(tk.Toplevel):
    def __init__(self, parent, title, subtitle="", size="560x500"):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.geometry(size)

        hdr = tk.Frame(self, bg=C["bg2"])
        hdr.pack(fill="x", side="top")

        mk_label(
            hdr,
            title,
            fg=C["accent"],
            bg=C["bg2"],
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=14, pady=10)

        if subtitle:
            mk_label(
                hdr,
                subtitle,
                fg=C["fg2"],
                bg=C["bg2"],
                font=("Segoe UI", 8),
            ).pack(side="left")

        self._footer_frame = tk.Frame(self, bg=C["bg"])
        self._footer_frame.pack(fill="x", side="bottom", padx=12, pady=8)

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", side="bottom")

        self.body = tk.Frame(self, bg=C["bg"])
        self.body.pack(fill="both", expand=True, padx=14, pady=10, side="top")

    def add_footer_buttons(self, save_cmd, cancel_cmd=None):
        mk_btn(
            self._footer_frame,
            "Save & Close",
            save_cmd,
            color=C["accent"],
            fg=C["bg"],
        ).pack(side="right", padx=(4, 0))

        mk_btn(
            self._footer_frame,
            "Cancel",
            cancel_cmd or self.destroy,
            color=C["bg3"],
            fg=C["fg2"],
        ).pack(side="right")