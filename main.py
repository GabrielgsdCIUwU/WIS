"""
main.py
-------
Entry point. Boots the WIS application.
"""

import os
import tkinter as tk

from core.config import _PYGAME_OK, SettingsStore, StatisticsStore
from services.audio import NullAudioPlayer, PygameAudioPlayer
from services.sender import HttpSender
from ui.main_window import WIS


def main():
    base  = os.path.dirname(os.path.abspath(__file__))
    store = SettingsStore(os.path.join(base, "wis_settings.json"))
    store.load()
    stats = StatisticsStore(os.path.join(base, "wis_stats.json"), store.stats_config)
    stats.load()
    sender = HttpSender()
    audio  = PygameAudioPlayer() if _PYGAME_OK else NullAudioPlayer()
    root   = tk.Tk()
    WIS(root, sender=sender, audio=audio, store=store, stats=stats)
    root.mainloop()


if __name__ == "__main__":
    main()
