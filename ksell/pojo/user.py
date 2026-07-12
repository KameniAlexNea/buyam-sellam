"""User POJO for KSell Entreprise."""

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class User:
    """User data object."""

    id: Optional[str] = None
    username: str = ""
    email: str = ""
    profil: str = ""
    country: str = ""
    birth_date: Optional[str] = None
    gender: str = ""
    competition_count: int = 0
    star_count: int = 0
    balance: float = 0.0
    card_count: int = 0
    cards: List[str] = field(default_factory=list)
    follower_count: int = 0
    followers: List[str] = field(default_factory=list)
    following_count: int = 0
    following: List[str] = field(default_factory=list)
    is_verified: bool = False

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize user to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Deserialize user from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
