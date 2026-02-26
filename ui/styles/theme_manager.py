"""
ui/styles/theme_manager.py
--------------------------
Style helpers: _lighten, apply_treeview_style, and widget factories.
"""

import tkinter as tk
from tkinter import ttk

from core.config import C


def _lighten(hex_color: str, amt: int = 25) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#{:02x}{:02x}{:02x}".format(
        min(255, r + amt), min(255, g + amt), min(255, b + amt)
    )


def apply_treeview_style() -> None:
    s = ttk.Style()
    s.theme_use("clam")
    s.configure("Treeview", background=C["bg2"], foreground=C["fg"],
                fieldbackground=C["bg2"], rowheight=26, font=("Segoe UI", 9))
    s.configure("Treeview.Heading", background=C["bg3"], foreground=C["accent"],
                font=("Segoe UI", 9, "bold"), relief="flat")
    s.map("Treeview",
          background=[("selected", C["bg3"])],
          foreground=[("selected", C["accent"])])
    s.configure("Vertical.TScrollbar", background=C["bg3"],
                troughcolor=C["bg2"], arrowcolor=C["fg2"])


def mk_btn(parent, text, command, color=None, fg=None, **kw):
    color   = color or C["bg3"]
    fg      = fg    or C["accent"]
    lighter = _lighten(color)
    b = tk.Button(parent, text=text, command=command, bg=color, fg=fg,
                  activebackground=lighter, activeforeground=fg,
                  relief="flat", bd=0, padx=12, pady=5,
                  font=("Segoe UI", 9, "bold"), cursor="hand2", **kw)
    b.bind("<Enter>", lambda e: b.config(bg=lighter))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b


def mk_entry(parent, textvariable=None, width=40):
    return tk.Entry(parent, textvariable=textvariable, width=width,
                    bg=C["bg3"], fg=C["fg"], insertbackground=C["accent"],
                    relief="flat", bd=0, font=("Segoe UI", 9),
                    highlightthickness=1, highlightbackground=C["border"],
                    highlightcolor=C["accent"])


def mk_label(parent, text, fg=None, font=None, bg=None, **kw):
    bg = bg if bg is not None else C["bg"]
    return tk.Label(parent, text=text, bg=bg, fg=fg or C["fg"],
                    font=font or ("Segoe UI", 9), **kw)


def mk_sep(parent):
    tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=6)


def mk_chk(parent, text, variable, command=None, bg=None):
    bg = bg if bg is not None else C["bg"]
    return tk.Checkbutton(parent, text=text, variable=variable,
                          bg=bg, fg=C["fg"], selectcolor=C["bg3"],
                          activebackground=bg, activeforeground=C["fg"],
                          font=("Segoe UI", 9), highlightthickness=0, command=command)


def mk_section(parent, text):
    tk.Label(parent, text=text, bg=C["bg"], fg=C["fg2"],
             font=("Segoe UI", 7, "bold")).pack(anchor="w")
    tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=3)
