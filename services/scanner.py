"""
services/scanner.py
-------------------
FolderScanner: iterates image files inside a directory.
"""

import os


class FolderScanner:
    def __init__(self, formats: set):
        self._formats = formats

    def iter_images(self, root: str, recursive: bool):
        if recursive:
            for dirpath, _, files in os.walk(root):
                for fn in files:
                    if os.path.splitext(fn)[1].lower() in self._formats:
                        yield os.path.join(dirpath, fn)
        else:
            try:
                with os.scandir(root) as it:
                    for entry in it:
                        if entry.is_file() and \
                                os.path.splitext(entry.name)[1].lower() in self._formats:
                            yield entry.path
            except Exception:
                pass
