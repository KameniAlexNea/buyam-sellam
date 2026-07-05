"""Player model for KSell Entreprise."""

from dataclasses import asdict
from typing import Any, List, Optional

from pojo.carte import Card
from pojo.lieu_vente import Market
from pojo.outil import Tool
from pojo.user import User


class Joueur:
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

    def __repr__(self) -> str:
        return f"Joueur(username={self.username!r}, balance={self.balance})"
