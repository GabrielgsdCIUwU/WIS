"""
services/monitor.py
-------------------
MonitoringService: the background thread that scans folders and sends images.
"""

import os
import time
from threading import Thread
from typing import Callable, Tuple

import requests

from core.config import DEFAULTS, _SCRIPT_DIR
from core.events import ISender, IAudioPlayer
from core.config import StatisticsStore
from services.scanner import FolderScanner


_SEND_ERRORS: Tuple = (
    (requests.exceptions.Timeout,        "Timeout",          "Timeout"),
    (requests.exceptions.ConnectionError, "Connection error", "Connection Error"),
)


class MonitoringService:
    def __init__(self,
                 sender:      ISender,
                 audio:       IAudioPlayer,
                 stats:       StatisticsStore,
                 on_log:      Callable[[str, str], None],
                 on_counters: Callable[[int, int], None]):
        self._sender      = sender
        self._audio       = audio
        self._stats       = stats
        self._on_log      = on_log
        self._on_counters = on_counters
        self._running     = False
        self._sent_files: set = set()
        self._sent_count  = 0
        self._fail_count  = 0

    @property
    def running(self) -> bool:
        return self._running

    def start(self, folders: list, webhooks: list, settings: dict, debug: bool) -> None:
        self._running    = True
        self._sent_count = 0
        self._fail_count = 0
        self._sent_files.clear()
        scanner = FolderScanner(self._formats(settings))
        self._snapshot(folders, scanner)
        Thread(target=self._loop,
               args=(folders, webhooks, settings, debug, scanner),
               daemon=True).start()

    def stop(self) -> None:
        self._running = False

    @staticmethod
    def _formats(settings: dict) -> set:
        raw = settings.get("formats", DEFAULTS["formats"])
        return {e.strip().lower() for e in raw.split(",") if e.strip()}

    def _snapshot(self, folders: list, scanner: FolderScanner) -> None:
        new_files = {
            os.path.abspath(fp)
            for fc in folders
            for fp in scanner.iter_images(fc["path"], fc.get("recursive", False))
        }
        self._sent_files.update(new_files)
        self._on_log(f"Snapshot: {len(new_files)} existing file(s) marked as seen", "debug")

    def _loop(self, folders, webhooks, settings, debug, scanner: FolderScanner) -> None:
        scan_rate  = float(settings.get("scan_rate",  1.0))
        file_delay = float(settings.get("file_delay", 0.8))
        timeout    = int(settings.get("send_timeout", 30))
        volume     = float(settings.get("sound_volume", 0.8))
        scan = 0
        while self._running:
            scan += 1
            if debug:
                self._on_log(f"Scan #{scan}", "debug")
            for fc in folders:
                try:
                    self._scan_folder(fc, webhooks, scanner, file_delay, timeout, volume)
                except Exception as e:
                    self._on_log(f"Error scanning {fc['path']}: {e}", "err")
            time.sleep(scan_rate)

    def _scan_folder(self, fc, webhooks, scanner, file_delay, timeout, volume) -> None:
        folder_path = fc["path"]
        recursive   = fc.get("recursive", False)
        base_name   = os.path.basename(folder_path)
        for fp in scanner.iter_images(folder_path, recursive):
            abs_fp = os.path.abspath(fp)
            if abs_fp in self._sent_files:
                continue
            rel = os.path.relpath(abs_fp, folder_path)
            self._on_log(f"New: {rel}  [{base_name}]", "info")
            time.sleep(file_delay)
            if not os.path.exists(abs_fp):
                continue
            try:
                if os.path.getsize(abs_fp) == 0:
                    self._on_log(f"Empty, skipping: {rel}", "warn")
                    continue
            except Exception:
                continue
            all_ok = all(
                self._send_to_webhook(abs_fp, wh, folder_path, timeout) for wh in webhooks
            )
            self._sent_files.add(abs_fp)
            # Sound files live next to main.py (two levels up from core/)
            root_dir = os.path.normpath(os.path.join(_SCRIPT_DIR, ".."))
            snd = os.path.join(root_dir, "validation.mp3" if all_ok else "exclamation.mp3")
            if os.path.isfile(snd):
                self._audio.play(snd, volume)
            self._sent_count += all_ok
            self._fail_count += not all_ok
            self._on_counters(self._sent_count, self._fail_count)

    def _send_to_webhook(self, abs_fp: str, wh: dict, folder_path: str, timeout: int) -> bool:
        fname = os.path.basename(abs_fp)
        url   = wh.get("url", "")
        name  = wh.get("name", "?")
        ext   = os.path.splitext(fname)[1].lower()

        profile    = wh.get("_resolved_profile") or {}
        username   = profile.get("username", "")
        avatar_url = profile.get("avatar_url", "")

        def _record(ok: bool, log_msg: str, log_kind: str,
                    err_type: str = "", detail: str = "") -> bool:
            self._on_log(log_msg, log_kind)
            self._stats.record_send(ok=ok, file=fname, webhook=name,
                                    folder=folder_path, ext=ext,
                                    err_type=err_type, detail=detail)
            return ok

        try:
            ok = self._sender.send(abs_fp, url, timeout, username=username, avatar_url=avatar_url)
            if ok:
                return _record(True, f"{fname}  →  {name}", "ok")
            return _record(False, f"Non-2xx  {fname}  →  {name}", "err",
                           "HTTP Error", "Non-2xx response")
        except tuple(exc for exc, _, __ in _SEND_ERRORS) as e:
            for exc_type, log_label, err_label in _SEND_ERRORS:
                if isinstance(e, exc_type):
                    return _record(False, f"{log_label}  {fname}  →  {name}", "err",
                                   err_label, str(e)[:120])
        except Exception as e:
            return _record(False, f"Error  {fname}  →  {name}: {e}", "err",
                           type(e).__name__, str(e)[:120])
        return False
