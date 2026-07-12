"""Product POJO for KSell Entreprise."""

from dataclasses import dataclass


@dataclass
class Product:
    """A product in the game with name, price, and image."""

    id: str = ""
    name: str = ""
    price: int = 0
    image: str = ""
