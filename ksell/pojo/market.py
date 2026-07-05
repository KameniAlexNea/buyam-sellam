"""Market (Sales Location) POJO for KSell Entreprise."""

from dataclasses import dataclass, field

from ksell.pojo.constraint import Constraint


@dataclass
class Market:
    """Sales location with quantity range and tax rate."""

    id: str = ""
    name: str = ""
    image: str = ""
    min_qty: int = 50
    max_qty: int = 200
    tax_rate: float = 0.05
    product: str = ""
    fixed_price: int = 1000
    constraint: Constraint = field(default_factory=Constraint)
