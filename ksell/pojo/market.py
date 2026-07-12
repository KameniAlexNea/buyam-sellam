"""Market (Sales Location) POJO for KSell Entreprise."""

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class Market:
    """Sales location with quantity range and tax rate."""

    id: str = ""
    name: str = ""
    min_qty: int = 50
    max_qty: int = 200
    tax_rate: float = 0.05
    product: str = ""
    fixed_price: int = 1000

    def to_dict(self) -> Dict[str, Any]:
        """Serialize market to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Market":
        """Deserialize market from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
