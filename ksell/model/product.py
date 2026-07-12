"""Product wrapper model for KSell Entreprise.

Wraps a pojo.Product with a quantity and average cost for trading purposes.
"""

from dataclasses import asdict
from typing import Any, Dict

from ksell.pojo.product import Product


class ProductModel:
    """Wrapper that pairs a product with a quantity and average cost for trading."""

    def __init__(
        self,
        product: Product = None,
        quantity: int = 0,
        avg_cost: float = 0.0,
    ):
        self.product = product or Product()
        self.quantity = quantity
        self.avg_cost = avg_cost  # Average purchase price per unit

    def add_units(self, quantity: int, price_per_unit: float) -> None:
        """Add units and update average cost (weighted average)."""
        total_cost = self.avg_cost * self.quantity + price_per_unit * quantity
        self.quantity += quantity
        self.avg_cost = (
            round(total_cost / self.quantity, 2) if self.quantity > 0 else 0.0
        )

    def remove_units(self, quantity: int) -> bool:
        """Remove units (avg_cost stays the same — FIFO not tracked)."""
        if self.quantity < quantity:
            return False
        self.quantity -= quantity
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product": asdict(self.product),
            "quantity": self.quantity,
            "avg_cost": self.avg_cost,
        }

    def __repr__(self) -> str:
        return f"ProductModel(name={self.product.name!r}, quantity={self.quantity}, avg_cost={self.avg_cost})"
