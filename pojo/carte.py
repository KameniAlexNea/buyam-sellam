"""Card POJO for KSell Entreprise."""

from dataclasses import dataclass


@dataclass
class Card:
    """Game card with value and price."""

    id: str = ""
    name: str = ""
    description: str = ""
    value: int = 0
    price: int = 0
    game_price: int = 0
