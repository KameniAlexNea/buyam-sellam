"""ProductDish (Product-Dish Combination) POJO for KSell Entreprise."""

from dataclasses import dataclass, field

from ksell.pojo.dish import Dish
from ksell.pojo.product import Product


@dataclass
class ProductDish:
    """Combination of a product and a dish with a percentage."""

    id: str = ""
    dish: Dish = field(default_factory=Dish)
    product: Product = field(default_factory=Product)
    percentage: float = 0.0
