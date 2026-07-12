"""Dice model for KSell Entreprise.

Represents two dice, each rolling 1-6.
"""

import random
from typing import Any, Dict, Optional


class Dice:
    """Two-dice roller for the KSell game."""

    def __init__(self, die1: Optional[int] = None, die2: Optional[int] = None):
        if die1 is not None and die2 is not None:
            self.die1 = die1
            self.die2 = die2
        else:
            self.die1, self.die2 = random.randint(1, 6), random.randint(1, 6)

    @classmethod
    def shake(cls) -> "Dice":
        """Roll both dice and return a new Dice instance."""
        return cls(random.randint(1, 6), random.randint(1, 6))

    @property
    def total(self) -> int:
        """Return the sum of both dice."""
        return self.die1 + self.die2

    def to_dict(self) -> Dict[str, Any]:
        """Convert dice to dictionary."""
        return {
            "die1": self.die1,
            "die2": self.die2,
            "total": self.total,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Dice":
        """Deserialize dice from dictionary."""
        return cls(die1=data["die1"], die2=data["die2"])

    def __repr__(self) -> str:
        return f"Dice(d1={self.die1}, d2={self.die2}, total={self.total})"

    def __str__(self) -> str:
        return f"🎲 [{self.die1}|{self.die2}] = {self.total}"
