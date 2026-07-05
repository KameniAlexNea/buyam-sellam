"""Dish POJO for KSell Entreprise."""

from dataclasses import dataclass


@dataclass
class Dish:
    """A dish type in the game."""

    name: str = ""
    profile: str = ""
