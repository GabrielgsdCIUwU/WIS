"""
ui/main_window.py
-----------------
WIS: the root application window and main controller.
"""

import os
import time
import tkinter as tk
from threading import Thread
from typing import Callable

from core.config import C, DEFAULTS, _LOG_ICONS, SettingsStore, StatisticsStore
from core.events import ISender, IAudioPlayer
from services.monitor import MonitoringService
from ui.dialogs.folder_manager import FolderManager
from ui.dialogs.settings_manager import SettingsManager
from ui.dialogs.stats_dashboard import StatsWindow
from ui.dialogs.webhook_manager import WebhookManager
from ui.styles.theme_manager import (
    apply_treeview_style, mk_btn, mk_label, mk_section,
)


class WIS:
    def __init__(self, root: tk.Tk,
                 sender: ISender,
                 audio:  IAudioPlayer,
                 store:  SettingsStore,
                 stats:  StatisticsStore):
        self.root   = root
        self._store = store
        self._stats = stats

        self.root.title("WIS — Webhook Image Sender")
        self.root.minsize(720, 540)
        self.root.geometry("820x640")

        self._auto_start_var = tk.BooleanVar(value=store.auto_start)
        self._debug_var      = tk.BooleanVar(value=store.debug_mode)

        self._monitoring = MonitoringService(
            sender=sender, audio=audio, stats=stats,
            on_log=self._log_from_thread,
            on_counters=self._update_counters,
        )

        C.update({k: store.values[k] for k in DEFAULTS if k in store.values})
        self.root.configure(bg=C["bg"])
        apply_treeview_style()
        self._build_ui()

        if store.auto_start and self._ready():
            self.root.after(1000, self.start_monitoring)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
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
                                    wraplength=250, justify="left", padx=8, pady=6, anchor="nw")
        self._folder_lbl.pack(fill="x", pady=(0, 4))
        mk_btn(p, "Manage Folders",  self._open_folders,  color=C["bg3"], fg=C["accent"]).pack(fill="x", pady=2)
        tk.Frame(p, bg=C["bg"], height=10).pack()
        mk_section(p, "WEBHOOKS")
        self._webhook_lbl = tk.Label(p, text=self._webhook_summary(),
                                     bg=C["bg2"], fg=C["fg"], font=("Segoe UI", 9),
                                     wraplength=250, justify="left", padx=8, pady=6, anchor="nw")
        self._webhook_lbl.pack(fill="x", pady=(0, 4))
        mk_btn(p, "Manage Webhooks", self._open_webhooks, color=C["bg3"], fg=C["accent"]).pack(fill="x", pady=2)
        tk.Frame(p, bg=C["bg"], height=10).pack()
        mk_btn(p, "Settings",   self._open_settings, color=C["bg3"], fg=C["fg"]).pack(fill="x", pady=2)
        mk_btn(p, "Statistics", self._open_stats,    color=C["bg3"], fg=C["accent"]).pack(fill="x", pady=2)
        tk.Frame(p, bg=C["bg"], height=8).pack()
        self._start_btn = mk_btn(p, "Start Monitoring", self.start_monitoring,
                                  color=C["accent2"], fg=C["bg"])
        self._start_btn.pack(fill="x", pady=3)
        self._stop_btn = mk_btn(p, "Stop Monitoring", self.stop_monitoring,
                                 color=C["danger"], fg="white")
        self._stop_btn.pack(fill="x", pady=3)
        self._stop_btn.config(state="disabled")

    def _build_right(self, p):
        hdr = tk.Frame(p, bg=C["bg"])
        hdr.pack(fill="x", pady=(0, 6))
        mk_label(hdr, "ACTIVITY LOG", fg=C["fg2"], font=("Segoe UI", 7, "bold")).pack(side="left")
        mk_btn(hdr, "Clear", self.clear_log, color=C["bg3"], fg=C["fg2"]).pack(side="right")

        stats_bar = tk.Frame(p, bg=C["bg2"], pady=6)
        stats_bar.pack(fill="x", pady=(0, 6))
        self._s_sent  = self._pill(stats_bar, "0", "Sent")
        self._s_fail  = self._pill(stats_bar, "0", "Failed")
        self._s_hooks = self._pill(stats_bar, "0", "Webhooks")
        self._s_dirs  = self._pill(stats_bar, "0", "Folders")
        self._refresh_pill_stats()

        from tkinter import ttk
        log_wrap = tk.Frame(p, bg=C["bg3"],
                            highlightthickness=1, highlightbackground=C["border"])
        log_wrap.pack(fill="both", expand=True)
        self._log_box = tk.Text(log_wrap, bg=C["bg3"], fg=C["fg"],
                                insertbackground=C["accent"], relief="flat", bd=0,
                                font=("Consolas", 9), wrap="word", state="disabled")
        self._log_box.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        sb = ttk.Scrollbar(log_wrap, orient="vertical", command=self._log_box.yview)
        sb.pack(side="right", fill="y")
        self._log_box.configure(yscrollcommand=sb.set)
        for tag, fg in [("ok",  C["accent2"]), ("err",   C["danger"]),
                         ("warn", C["warning"]), ("info",  C["accent"]),
                         ("debug", C["fg2"]),   ("ts",    C["fg2"])]:
            self._log_box.tag_config(tag, foreground=fg)

    def _pill(self, parent, value, label):
        f = tk.Frame(parent, bg=C["bg2"])
        f.pack(side="left", padx=14)
        v = mk_label(f, value, fg=C["accent"], bg=C["bg2"], font=("Segoe UI", 16, "bold"))
        v.pack()
        mk_label(f, label, fg=C["fg2"], bg=C["bg2"], font=("Segoe UI", 8)).pack()
        return v

    # ── Summaries ─────────────────────────────────────────────────────────────

    def _summary(self, items: list, none_msg: str, all_disabled_msg: str,
                 label_fn: Callable) -> str:
        enabled = [x for x in items if x.get("enabled", True)]
        if not items:   return none_msg
        if not enabled: return all_disabled_msg
        lines = [label_fn(x) for x in enabled[:4]]
        if len(enabled) > 4:
            lines.append(f"  +{len(enabled) - 4} more")
        return "\n".join(lines)

    def _folder_summary(self) -> str:
        return self._summary(
            self._store.folders,
            "No folders configured", "All folders disabled",
            lambda f: f"• {os.path.basename(f['path']) or f['path']}"
                      + (" (recursive)" if f.get("recursive") else ""),
        )

    def _webhook_summary(self) -> str:
        return self._summary(
            self._store.webhooks,
            "No webhooks configured", "All webhooks disabled",
            lambda w: f"• {w.get('name', 'Unnamed')}",
        )

    def _refresh_pill_stats(self):
        self._s_hooks.config(
            text=str(sum(1 for w in self._store.webhooks if w.get("enabled", True))))
        self._s_dirs.config(
            text=str(sum(1 for f in self._store.folders  if f.get("enabled", True))))

    # ── Dialog openers ────────────────────────────────────────────────────────

    def _open_folders(self):
        def on_save(v):
            self._store.folders = v
            self._store.save()
            self._folder_lbl.config(text=self._folder_summary())
            self._refresh_pill_stats()
            self.log("Folder list updated", "info")
        FolderManager(self.root, self._store.folders, on_save)

    def _open_webhooks(self):
        def on_save(v):
            self._store.webhooks = v
            self._store.save()
            self._webhook_lbl.config(text=self._webhook_summary())
            self._refresh_pill_stats()
            self.log("Webhook list updated", "info")
        WebhookManager(self.root, self._store.webhooks, self._store.shared_profiles, on_save)

    def _open_settings(self):
        def on_save(updated_store: SettingsStore):
            C.update(updated_store.values)
            apply_treeview_style()
            updated_store.save()
            self.log("Settings saved — restart to fully apply color changes", "warn")
        SettingsManager(self.root, self._store, on_save)

    def _open_stats(self):
        StatsWindow(self.root, self._stats)

    # ── Logging ───────────────────────────────────────────────────────────────

    def log(self, message: str, kind: str = "info"):
        ts   = time.strftime("%H:%M:%S")
        icon = _LOG_ICONS.get(kind, "·")
        self._log_box.config(state="normal")
        self._log_box.insert("end", f"[{ts}] ", "ts")
        self._log_box.insert("end", f"{icon} {message}\n", kind)
        self._log_box.see("end")
        self._log_box.config(state="disabled")

    def _log_from_thread(self, message: str, kind: str):
        self.root.after(0, self.log, message, kind)

    def _update_counters(self, sent: int, fail: int):
        self.root.after(0, lambda: (
            self._s_sent.config(text=str(sent)),
            self._s_fail.config(text=str(fail)),
        ))

    def clear_log(self):
        self._log_box.config(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.config(state="disabled")

    # ── Monitoring control ────────────────────────────────────────────────────

    def _ready(self) -> bool:
        return (
            any(f.get("enabled") and os.path.isdir(f.get("path", "")) for f in self._store.folders)
            and any(w.get("enabled") and w.get("url") for w in self._store.webhooks)
        )

    def start_monitoring(self):
        active_webhooks = [w for w in self._store.webhooks
                           if w.get("enabled", True) and w.get("url")]
        if not active_webhooks:
            self.log("No webhooks configured.", "warn"); return

        profile_map = {p["name"]: p for p in self._store.shared_profiles}
        resolved_webhooks = []
        for w in active_webhooks:
            wc = dict(w)
            if w.get("shared_profile_enabled") and w.get("shared_profile"):
                wc["_resolved_profile"] = profile_map.get(w["shared_profile"], {})
            else:
                wc["_resolved_profile"] = {}
            resolved_webhooks.append(wc)

        valid, invalid = [], []
        for f in self._store.folders:
            if not f.get("enabled", True):
                continue
            (valid if os.path.isdir(f.get("path", "")) else invalid).append(f)
        for f in invalid:
            self.log(f"Folder not found, skipping: {f['path']}", "warn")
        if not valid:
            self.log("No valid folders found.", "err"); return

        self._s_sent.config(text="0")
        self._s_fail.config(text="0")
        self._start_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        self._status_pill.config(text="  MONITORING  ", bg="#1a3320", fg=C["accent2"])

        self._monitoring.start(valid, resolved_webhooks, self._store.values, self._store.debug_mode)
        names = ", ".join(w["name"] for w in resolved_webhooks)
        self.log(f"Started — {len(valid)} folder(s) → {len(resolved_webhooks)} webhook(s): {names}", "ok")

    def stop_monitoring(self):
        self._monitoring.stop()
        self._start_btn.config(state="normal")
        self._stop_btn.config(state="disabled")
        self._status_pill.config(text="  STOPPED  ", bg="#2a1a1a", fg=C["danger"])
        self.log("Monitoring stopped", "warn")
        Thread(target=self._stats.save, daemon=True).start()
