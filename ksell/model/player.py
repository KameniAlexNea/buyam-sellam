"""Player model for KSell Entreprise."""

from typing import Any, List, Optional

from ksell.pojo.card import Card
from ksell.pojo.product import Product
from ksell.pojo.tool import Tool
from ksell.pojo.user import User
from ksell.model.product import ProductModel


class Player:
    """Game player with user profile, tools, markets, and economy."""

    def __init__(
        self,
        user: Optional[User] = None,
        tools: Optional[List[Tool]] = None,
        markets: Optional[List[Any]] = None,
        avatar: Optional[str] = None,
    ):
        self.user = user or User()
        self.tools = tools or []
        self.markets = markets or []
        self.avatar = avatar or "default_avatar.png"
        self.inventory: List[ProductModel] = []

    # ---- User property shortcuts ----

    @property
    def username(self) -> str:
        return self.user.username

    @username.setter
    def username(self, value: str):
        self.user.username = value

    @property
    def balance(self) -> float:
        return self.user.balance

    @balance.setter
    def balance(self, value: float):
        self.user.balance = value

    @property
    def card_count(self) -> int:
        return self.user.card_count

    @card_count.setter
    def card_count(self, value: int):
        self.user.card_count = value

    @property
    def star_count(self) -> int:
        return self.user.star_count

    @star_count.setter
    def star_count(self, value: int):
        self.user.star_count = value

    @property
    def competition_count(self) -> int:
        return self.user.competition_count

    @competition_count.setter
    def competition_count(self, value: int):
        self.user.competition_count = value

    @property
    def follower_count(self) -> int:
        return self.user.follower_count

    @follower_count.setter
    def follower_count(self, value: int):
        self.user.follower_count = value

    @property
    def cards(self) -> List[str]:
        return self.user.cards

    @cards.setter
    def cards(self, value: List[str]):
        self.user.cards = value

    # ---- Tool management ----

    def add_tool(self, tool: Tool) -> bool:
        if tool not in self.tools:
            self.tools.append(tool)
            return True
        return False

    def remove_tool(self, tool_id: str) -> bool:
        for i, t in enumerate(self.tools):
            if t.id == tool_id:
                self.tools.pop(i)
                return True
        return False

    def get_total_capacity(self) -> int:
        return sum(t.capacity for t in self.tools)

    # ---- Market management ----

    def add_market(self, market: Any) -> bool:
        if market not in self.markets:
            self.markets.append(market)
            return True
        return False

    def remove_market(self, market_id: int) -> bool:
        if 0 <= market_id < len(self.markets):
            self.markets.pop(market_id)
            return True
        return False

    # ---- Card management ----

    def add_card(self, card: Card) -> bool:
        if card.id not in self.user.cards:
            self.user.cards.append(card.id)
            self.user.card_count += 1
            return True
        return False

    def remove_card(self, card_id: str) -> bool:
        if card_id in self.user.cards:
            self.user.cards.remove(card_id)
            self.user.card_count -= 1
            return True
        return False

    # ---- Economy ----

    def add_fortune(self, amount: float) -> float:
        self.user.balance += amount
        return self.user.balance

    def subtract_fortune(self, amount: float) -> float:
        self.user.balance = max(0.0, self.user.balance - amount)
        return self.user.balance

    def can_afford(self, amount: float) -> bool:
        return self.user.balance >= amount

    # ---- Inventory management ----

    def add_to_inventory(self, product: Product, quantity: int) -> None:
        """Add product to inventory. Price from product.price is used as cost basis."""
        for item in self.inventory:
            if item.product.name == product.name:
                item.add_units(quantity, product.price)
                return
        self.inventory.append(ProductModel(product=product, quantity=quantity, avg_cost=product.price))

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

    def __repr__(self) -> str:
        return f"Player(username={self.username!r}, balance={self.balance})"
