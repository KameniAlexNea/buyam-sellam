"""Dice model for KSell Entreprise.

Represents two dice, each rolling 1-6. Used to determine market conditions.
"""

import random
from typing import Any, Dict, Optional


class Dice:
    """Two-dice roller for the KSell game.

    Each die produces a value between 1 and 6 (inclusive).
    The total (2-12) determines market conditions:
    - 2-4: Bad market (low demand)
    - 5-8: Normal market
    - 9-12: Good market (high demand)
    """

    def __init__(self, die1: Optional[int] = None, die2: Optional[int] = None):
        if die1 is not None and die2 is not None:
            self.die1 = die1
            self.die2 = die2
        else:
            self.shake()

    def shake(self) -> "Dice":
        """Roll both dice and return a new Dice instance."""
        self.die1 = random.randint(1, 6)
        self.die2 = random.randint(1, 6)
        return self

    def total(self) -> int:
        """Return the sum of both dice."""
        return self.die1 + self.die2

    def market_condition(self) -> str:
        """Determine market condition based on dice total.

        Returns:
            'bad' for totals 2-4, 'normal' for 5-8, 'good' for 9-12
        """
        t = self.total()
        if t <= 4:
            return "bad"
        elif t <= 8:
            return "normal"
        else:
            return "good"

    def market_multiplier(self) -> float:
        """Return a multiplier for market quantity based on dice total.

        Good markets produce more demand, bad markets less.
        """
        t = self.total()
        if t <= 4:
            return 0.5  # 50% of normal
        elif t <= 8:
            return 1.0  # normal
        else:
            return 1.5  # 150% of normal

    def to_dict(self) -> Dict[str, Any]:
        """Convert dice to dictionary."""
        return {
            "die1": self.die1,
            "die2": self.die2,
            "total": self.total(),
            "condition": self.market_condition(),
        }

    def clone(self) -> "Dice":
        """Return a deep copy of this Dice."""
        return Dice(self.die1, self.die2)

    def __repr__(self) -> str:
        return f"Dice(d1={self.die1}, d2={self.die2}, total={self.total()})"

    def __str__(self) -> str:
        condition = self.market_condition()
        return f"🎲 [{self.die1}|{self.die2}] = {self.total()} ({condition})"
