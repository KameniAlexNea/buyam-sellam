"""Penalty POJO for KSell Entreprise."""

from dataclasses import dataclass


@dataclass
class Penalty:
    """Penalty that can be applied to a player."""

    id: str = ""
    name: str = ""
    amount: int = 0
