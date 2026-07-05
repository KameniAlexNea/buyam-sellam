"""Product wrapper model for KSell Entreprise.

Wraps a pojo.Product with a quantity for trading purposes.
"""

from dataclasses import asdict
from typing import Any, Dict

from pojo.product import Product


class ProductModel:
    """Wrapper that pairs a product with a quantity for trading."""

    def __init__(
        self,
        product: Product = None,
        quantity: int = 0,
    ):
        self.product = product or Product()
        self.quantity = quantity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product": asdict(self.product),
            "quantity": self.quantity,
        }

    def __repr__(self) -> str:
        return f"ProductModel(name={self.product.name!r}, quantity={self.quantity})"
