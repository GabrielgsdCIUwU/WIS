"""
services/sender.py
------------------
HTTP and null implementations of ISender.
"""

import json
import mimetypes
import os

import requests

from core.events import ISender


class HttpSender(ISender):
    def send(self, file_path: str, url: str, timeout: int,
             username: str = "", avatar_url: str = "") -> bool:
        fname = os.path.basename(file_path)
        mime, _ = mimetypes.guess_type(file_path)
        mime = mime or "application/octet-stream"
        with open(file_path, "rb") as fh:
            files = {"file": (fname, fh, mime)}
            if username or avatar_url:
                payload = {}
                if username:   payload["username"]   = username
                if avatar_url: payload["avatar_url"] = avatar_url
                files["payload_json"] = (None, json.dumps(payload), "application/json")
            r = requests.post(url, files=files, timeout=timeout)
        return r.status_code in (200, 201, 204)


class NullSender(ISender):
    """No-op sender used for testing."""
    def send(self, file_path: str, url: str, timeout: int,
             username: str = "", avatar_url: str = "") -> bool:
        return True
