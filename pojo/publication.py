"""Publication POJO for KSell Entreprise."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Publication:
    """A publication/post in the game community."""

    id: str = ""
    content: str = ""
    author_id: str = ""
    date: Optional[str] = None
    likes: int = 0
    comments: int = 0

    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now().isoformat()
