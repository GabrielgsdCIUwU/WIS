"""
ui/dialogs/stats_dashboard.py
------------------------------
StatsWindow: the statistics analytics dashboard.
"""

import os
import tkinter as tk
from tkinter import messagebox, ttk

from core.config import C, StatisticsStore
from ui.components.charts import BarChart, PieChart
from ui.components.factory import BasePopup
from ui.components.tree_panel import TreePanel
from ui.styles.theme_manager import mk_btn, mk_label


class StatsWindow(BasePopup):
    def __init__(self, parent, stats: StatisticsStore):
        super().__init__(parent, "Statistics", "Send history & analytics", size="860x640")
        self.resizable(True, True)
        self._stats = stats
        self._build()

    def _build(self):
        b  = self.body
        nb = ttk.Notebook(b)
        nb.pack(fill="both", expand=True)
        style = ttk.Style()
        style.configure("TNotebook",     background=C["bg"],  borderwidth=0)
        style.configure("TNotebook.Tab", background=C["bg3"], foreground=C["fg2"],
                        padding=[10, 5], font=("Segoe UI", 9))
        style.map("TNotebook.Tab",
                  background=[("selected", C["bg2"])],
                  foreground=[("selected", C["accent"])])

        tab_names = ["Overview", "Webhooks", "Folders", "Errors", "Recent"]
        self._tabs = {n: tk.Frame(nb, bg=C["bg"]) for n in tab_names}
        for name, frame in self._tabs.items():
            nb.add(frame, text=f"  {name}  ")

        self._build_overview()
        self._build_webhooks()
        self._build_folders()
        self._build_errors()
        self._build_recent()

        mk_btn(self._footer_frame, "Close",           self.destroy,
               color=C["bg3"],    fg=C["fg2"]).pack(side="right")
        mk_btn(self._footer_frame, "Clear All Stats", self._clear_stats,
               color=C["danger"], fg="white").pack(side="left")
        mk_btn(self._footer_frame, "Refresh",         self._refresh_all,
               color=C["bg3"],    fg=C["accent"]).pack(side="left", padx=(0, 6))

    def _repopulate(self, panel: TreePanel, rows):
        panel.clear()
        for i, row in enumerate(rows):
            panel.insert(i, row if isinstance(row, tuple) else (row,))

    def _build_overview(self):
        p = self._tabs["Overview"]
        summary = tk.Frame(p, bg=C["bg2"], pady=8)
        summary.pack(fill="x", padx=8, pady=(8, 4))
        sends  = self._stats.sends
        total  = len(sends)
        ok     = sum(1 for s in sends if s.get("ok"))
        fail   = total - ok
        rate   = f"{100 * ok / total:.1f}%" if total else "—"
        for val, lbl, col in [
            (str(total), "Total Sent",   C["accent"]),
            (str(ok),    "Successful",   C["accent2"]),
            (str(fail),  "Failed",       C["danger"]),
            (rate,       "Success Rate", C["warning"]),
            (str(len(self._stats.errors)), "Errors", C["fg2"]),
        ]:
            f = tk.Frame(summary, bg=C["bg2"])
            f.pack(side="left", padx=18)
            tk.Label(f, text=val, bg=C["bg2"], fg=col,  font=("Segoe UI", 18, "bold")).pack()
            tk.Label(f, text=lbl, bg=C["bg2"], fg=C["fg2"], font=("Segoe UI", 8)).pack()

        chart_frame = tk.Frame(p, bg=C["bg"])
        chart_frame.pack(fill="both", expand=True, padx=8, pady=4)
        mk_label(chart_frame, "Images Sent — Last 12 Months",
                 fg=C["fg2"], font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(4, 2))
        n = self._stats._config.get("months", 12)
        self._monthly_chart = BarChart(chart_frame, data=self._stats.months_data(n),
                                       color=C["accent"], bg=C["bg2"], height=220)
        self._monthly_chart.pack(fill="both", expand=True)

        ext_row = tk.Frame(p, bg=C["bg"])
        ext_row.pack(fill="x", padx=8, pady=(4, 8))
        mk_label(ext_row, "By File Type", fg=C["fg2"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 2))
        self._ext_pie = PieChart(ext_row, data=self._stats.ext_data(),
                                 bg=C["bg2"], height=150)
        self._ext_pie.pack(fill="x")

    def _build_webhooks(self):
        p = self._tabs["Webhooks"]
        mk_label(p, "Images Sent per Webhook", fg=C["fg2"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        self._webhook_bar = BarChart(p, data=self._stats.webhook_data(),
                                     color=C["accent2"], bg=C["bg2"], height=220)
        self._webhook_bar.pack(fill="x", padx=8, pady=4)
        mk_label(p, "Webhook Breakdown", fg=C["fg2"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=(6, 2))
        self._webhook_tree = TreePanel(p,
            columns=("name", "sent", "failed", "rate"),
            headings=("Webhook", "Sent", "Failed", "Success Rate"),
            widths=(220, 80, 80, 120), height=8)
        self._webhook_tree.pack(fill="both", expand=True, padx=8, pady=4)
        self._repopulate(self._webhook_tree, self._stats.webhook_table())

    def _build_folders(self):
        p = self._tabs["Folders"]
        mk_label(p, "Images Sent per Folder", fg=C["fg2"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        self._folder_bar = BarChart(p,
            data=[(os.path.basename(l) or l, v) for l, v in self._stats.folder_data()],
            color=C["warning"], bg=C["bg2"], height=200)
        self._folder_bar.pack(fill="x", padx=8, pady=4)
        mk_label(p, "Folder Detail", fg=C["fg2"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=(6, 2))
        self._folder_tree = TreePanel(p,
            columns=("path", "sent"),
            headings=("Folder Path", "Images Sent"),
            widths=(480, 100), height=8)
        self._folder_tree.pack(fill="both", expand=True, padx=8, pady=4)
        self._repopulate(self._folder_tree, self._stats.folder_data())

    def _build_errors(self):
        p = self._tabs["Errors"]
        mk_label(p, "Error Breakdown", fg=C["fg2"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        err_row = tk.Frame(p, bg=C["bg"])
        err_row.pack(fill="x", padx=8, pady=4)
        self._error_pie = PieChart(err_row, data=self._stats.error_type_data(),
                                   bg=C["bg2"], height=200)
        self._error_pie.pack(side="left", fill="both", expand=True)
        self._error_bar = BarChart(err_row, data=self._stats.error_type_data(),
                                   color=C["danger"], bg=C["bg2"], height=200)
        self._error_bar.pack(side="left", fill="both", expand=True)
        mk_label(p, "Recent Errors", fg=C["fg2"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=(6, 2))
        self._error_tree = TreePanel(p,
            columns=("time", "type", "file", "webhook", "detail"),
            headings=("Time", "Type", "File", "Webhook", "Detail"),
            widths=(80, 100, 160, 120, 220), height=8)
        self._error_tree.pack(fill="both", expand=True, padx=8, pady=4)
        errors = list(reversed(self._stats.errors[-200:]))
        self._repopulate(self._error_tree, [
            (e.get("time",""), e.get("type",""), e.get("file",""),
             e.get("webhook",""), e.get("detail",""))
            for e in errors
        ])

    def _build_recent(self):
        p    = self._tabs["Recent"]
        hdr  = tk.Frame(p, bg=C["bg"])
        hdr.pack(fill="x", padx=8, pady=(10, 2))
        ok   = sum(1 for s in self._stats.sends if s.get("ok"))
        fail = len(self._stats.sends) - ok
        mk_label(hdr, "Recent Sends (latest 500)", fg=C["fg2"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        mk_label(hdr, f"  {ok} ok  |  {fail} failed", fg=C["fg2"],
                 font=("Segoe UI", 8)).pack(side="left", padx=8)
        self._recent_tree = TreePanel(p,
            columns=("time", "file", "webhook", "folder", "ext", "status"),
            headings=("Time", "File", "Webhook", "Folder", "Ext", "Status"),
            widths=(90, 200, 120, 140, 50, 70), height=22)
        self._recent_tree.pack(fill="both", expand=True, padx=8, pady=4)
        self._populate_recent()

    def _populate_recent(self):
        recent = list(reversed(self._stats.sends[-500:]))
        self._repopulate(self._recent_tree, [
            (s.get("time",""), s.get("file",""), s.get("webhook",""),
             os.path.basename(s.get("folder","")) or s.get("folder",""),
             s.get("ext",""), "✓ OK" if s.get("ok") else "✗ Fail")
            for s in recent
        ])

    def _refresh_all(self):
        n = self._stats._config.get("months", 12)
        self._monthly_chart.update_data(self._stats.months_data(n))
        self._ext_pie.update_data(self._stats.ext_data())
        self._webhook_bar.update_data(self._stats.webhook_data())
        self._repopulate(self._webhook_tree, self._stats.webhook_table())
        self._folder_bar.update_data(
            [(os.path.basename(l) or l, v) for l, v in self._stats.folder_data()])
        self._repopulate(self._folder_tree, self._stats.folder_data())
        self._error_pie.update_data(self._stats.error_type_data())
        self._error_bar.update_data(self._stats.error_type_data())
        errors = list(reversed(self._stats.errors[-200:]))
        self._repopulate(self._error_tree, [
            (e.get("time",""), e.get("type",""), e.get("file",""),
             e.get("webhook",""), e.get("detail",""))
            for e in errors
        ])
        self._populate_recent()

    def _clear_stats(self):
        if messagebox.askyesno("Clear Stats",
                               "Delete ALL statistics history? This cannot be undone.",
                               parent=self):
            self._stats.clear()
            self._refresh_all()
