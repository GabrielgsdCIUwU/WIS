import os
import tkinter as tk

from models.settings import SettingsStore
from services.audio import create_audio_player
from services.sender import HttpSender
from services.stats_manager import create_stats_store
from ui.main_window import WIS


class WISApplication:
    """Bootstrap class: loads config, wires dependencies, and runs the app."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self._app = None

    def initialize(self) -> None:
        base  = os.path.dirname(os.path.abspath(__file__))
        # Settings store
        store = SettingsStore(os.path.join(base, "..", "wis_settings.json"))
        store.load()
        # Stats store
        stats = create_stats_store(os.path.join(base, ".."), store)
        # Wire the main window
        self._app = WIS(
            root=self.root,
            sender=HttpSender(),
            audio=create_audio_player(),
            store=store,
            stats=stats,
        )

    def run(self) -> None:
        self.root.mainloop()
