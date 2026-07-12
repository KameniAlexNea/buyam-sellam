"""Product POJO for KSell Entreprise."""

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class Product:
    """A product in the game with name, price, and image."""

    id: str = ""
    name: str = ""
    price: int = 0
    image: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize product to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Product":
        """Deserialize product from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
