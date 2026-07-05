"""Message model for KSell Entreprise."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Message:
    """Chat/communication message in the game."""

    action: str = ""
    content: str = ""
    sender: str = ""
    receiver: str = ""
    time: Optional[str] = None
    other: Optional[Any] = None

    def __post_init__(self):
        if self.time is None:
            self.time = datetime.now().strftime("%H:%M:%S")

    def set_time(self) -> None:
        self.time = datetime.now().strftime("%H:%M:%S")

    def __str__(self) -> str:
        return f"[{self.time}] {self.sender}: {self.content}"
