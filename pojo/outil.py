"""Tool POJO for KSell Entreprise."""

from dataclasses import dataclass


@dataclass
class Tool:
    """Game tool with cost and capacity."""

    id: str = ""
    name: str = ""
    image: str = ""
    cost: int = 0
    capacity: int = 0
