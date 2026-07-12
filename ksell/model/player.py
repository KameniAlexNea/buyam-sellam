"""Player model for KSell Entreprise."""

from typing import Any, Dict, Optional

from ksell.pojo.product import Product
from ksell.pojo.user import User
from ksell.model.product import ProductModel


class Player:
    """Game player with user profile and economy."""

    def __init__(
        self,
        user: Optional[User] = None,
    ):
        self.user = user or User()
        self.inventory: list[ProductModel] = []

    # ---- User property shortcuts ----

    @property
    def username(self) -> str:
        return self.user.username

    @property
    def balance(self) -> float:
        return self.user.balance

    @balance.setter
    def balance(self, value: float):
        self.user.balance = value

    # ---- Inventory management ----

    def add_to_inventory(self, product: Product, quantity: int) -> None:
        """Add product to inventory. Price from product.price is used as cost basis."""
        for item in self.inventory:
            if item.product.name == product.name:
                item.add_units(quantity, product.price)
                return
        self.inventory.append(
            ProductModel(product=product, quantity=quantity, avg_cost=product.price)
        )

    def remove_from_inventory(self, product_name: str, quantity: int) -> bool:
        """Remove product from inventory. Returns True if successful."""
        for item in self.inventory:
            if item.product.name == product_name:
                if not item.remove_units(quantity):
                    return False
                if item.quantity == 0:
                    self.inventory.remove(item)
                return True
        return False

    def get_inventory_quantity(self, product_name: str) -> int:
        """Get quantity of a product in inventory."""
        for item in self.inventory:
            if item.product.name == product_name:
                return item.quantity
        return 0

    def get_inventory_avg_cost(self, product_name: str) -> float:
        """Get average cost of a product in inventory."""
        for item in self.inventory:
            if item.product.name == product_name:
                return item.avg_cost
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize player to dictionary."""
        return {
            "user": self.user.to_dict(),
            "inventory": [item.to_dict() for item in self.inventory],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        """Deserialize player from dictionary."""
        from ksell.pojo.user import User

        user = User.from_dict(data["user"])
        player = cls(user=user)
        player.inventory = [ProductModel.from_dict(item) for item in data.get("inventory", [])]
        return player

    def __repr__(self) -> str:
        return f"Player(username={self.username!r}, balance={self.balance})"
