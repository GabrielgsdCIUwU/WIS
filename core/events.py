"""
core/events.py
--------------
Abstract base classes (interfaces) for pluggable components.
"""

from abc import ABC, abstractmethod


class ISender(ABC):
    @abstractmethod
    def send(self, file_path: str, url: str, timeout: int,
             username: str = "", avatar_url: str = "") -> bool: ...


class IAudioPlayer(ABC):
    @abstractmethod
    def play(self, file_path: str, volume: float) -> None: ...


class IChartWidget(ABC):
    @abstractmethod
    def update_data(self, data: list) -> None: ...
