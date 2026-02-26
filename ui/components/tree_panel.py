"""
ui/components/tree_panel.py
---------------------------
Reusable Treeview widget wrapper used across all manager dialogs.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from core.config import C


class TreePanel(tk.Frame):
    def __init__(self, parent, columns, headings, widths, height=9):
        super().__init__(parent, bg=C["bg"])
        self.tree = ttk.Treeview(self, columns=columns, show="headings",
                                  height=height, selectmode="browse")
        for col, hd, w in zip(columns, headings, widths):
            self.tree.heading(col, text=hd)
            self.tree.column(col, width=w,
                             anchor="center" if w <= 60 else "w",
                             stretch=(col == columns[-1]))
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def selected_idx(self) -> Optional[int]:
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def clear(self):
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)

    def insert(self, iid, values):
        self.tree.insert("", "end", iid=str(iid), values=values)
