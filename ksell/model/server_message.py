"""ServerMessage model for KSell Entreprise."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ServerMessage:
    """Server communication message."""

    action: str = ""
    sender_id: str = ""
    other: Optional[Any] = None
