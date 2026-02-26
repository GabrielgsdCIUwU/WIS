"""
services/audio.py
-----------------
pygame and null implementations of IAudioPlayer.
"""

from threading import Thread

from core.events import IAudioPlayer


class PygameAudioPlayer(IAudioPlayer):
    def play(self, file_path: str, volume: float) -> None:
        def _play():
            try:
                import pygame
                sound = pygame.mixer.Sound(file_path)
                sound.set_volume(max(0.0, min(1.0, volume)))
                sound.play()
            except Exception:
                pass
        Thread(target=_play, daemon=True).start()


class NullAudioPlayer(IAudioPlayer):
    def play(self, file_path: str, volume: float) -> None:
        pass
