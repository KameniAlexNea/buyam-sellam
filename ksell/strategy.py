"""AI strategy classes for Buyam-Sellam simulation.

Each strategy implements two decisions:
  1. **Strategy phase** — which action (buy/sell/skip) per market.
  2. **Action phase** — what quantity to buy/sell when prompted.

Strategies receive the same data that the REST API returns, so they
work identically whether driven by `game_sim_api.py` or `batch_sim.py`.
"""

from __future__ import annotations

import abc
import random
from typing import Any, Dict, List, Tuple


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

MarketDict = Dict[
    str, Any
]  # market_index, name, product, market_fixed_price, market_supply
PlayerDict = Dict[str, Any]  # username, balance, inventory[...]
StateDict = Dict[str, Any]  # full GameStateResponse


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class Strategy(abc.ABC):
    """Abstract AI strategy."""

    # Human-readable label shown in reports.
    label: str = "Base"

    # One-line description for help text.
    description: str = ""

    # ------------------------------------------------------------------
    # Strategy phase
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def choose_strategy(
        self,
        markets: List[MarketDict],
        players: List[PlayerDict],
        username: str,
    ) -> List[Tuple[int, str]]:
        """Return a list of (market_index, action) tuples.

        Actions are 'buy', 'sell', or 'skip'.
        Only return 'sell' if the player owns the market's product.
        """
        ...

    # ------------------------------------------------------------------
    # Action phase
    # ------------------------------------------------------------------

    def choose_buy_quantity(self, state: StateDict) -> int:
        """Return quantity to buy when can_buy is True.

        Default: random between 1 and max_affordable.
        Override for smarter quantity decisions.
        """
        max_aff = max(state.get("max_affordable", 1), 1)
        return random.randint(1, max_aff)

    def choose_sell_quantity(self, state: StateDict) -> int:
        """Return quantity to sell when can_sell is True.

        Default: random between 1 and seller_qty.
        Override for smarter quantity decisions.
        """
        max_qty = max(state.get("seller_qty", 1), 1)
        return random.randint(1, max_qty)

    # ------------------------------------------------------------------
    # Helpers (available to subclasses)
    # ------------------------------------------------------------------

    @staticmethod
    def _player_info(players: List[PlayerDict], username: str) -> PlayerDict | None:
        """Look up a player dict by username."""
        return next((p for p in players if p["username"] == username), None)

    @staticmethod
    def _owned_products(player: PlayerDict) -> Dict[str, Dict[str, Any]]:
        """Return {product_name: inventory_item} for a player."""
        return {item["product"]["name"]: item for item in player.get("inventory", [])}

    @staticmethod
    def _inventory_value(player: PlayerDict) -> float:
        """Total inventory value (quantity × avg_cost)."""
        return sum(
            item["quantity"] * item["avg_cost"] for item in player.get("inventory", [])
        )

    @staticmethod
    def _total_net_worth(player: PlayerDict) -> float:
        """Balance + inventory value."""
        return player.get("balance", 0) + Strategy._inventory_value(player)


# ---------------------------------------------------------------------------
# Concrete strategies
# ---------------------------------------------------------------------------


class RandomStrategy(Strategy):
    """Pure random baseline — picks buy/sell/skip uniformly.

    Respects inventory constraints (won't sell what you don't have).
    """

    label = "Random"
    description = "Uniform random choices; baseline for comparison"

    def choose_strategy(
        self,
        markets: List[MarketDict],
        players: List[PlayerDict],
        username: str,
    ) -> List[Tuple[int, str]]:
        player = self._player_info(players, username)
        if not player:
            return [(m["market_index"], "skip") for m in markets]

        owned = self._owned_products(player)
        actions = ["buy", "sell", "skip"]
        strategy: List[Tuple[int, str]] = []
        market_list = list(markets)
        random.shuffle(market_list)
        for m in market_list:
            allowed = actions if m["product"] in owned else ["buy", "skip"]
            strategy.append((m["market_index"], random.choice(allowed)))
        return strategy


class BuyLowSellHigh(Strategy):
    """Classic arbitrage — buy when market price is low, sell when high.

    Heuristic:
      - Compare market_fixed_price to the player's avg_cost for that product.
      - If market price > avg_cost + margin → sell (profit opportunity).
      - If market price < avg_cost - margin → buy (cheap pickup).
      - If player has no inventory of the product and price is below
        a fraction of starting balance → buy to build inventory.
    """

    label = "BuyLowSellHigh"
    description = "Buy when cheap, sell when profitable; classic arbitrage"

    MARGIN = 0.15  # 15% profit margin threshold

    def choose_strategy(
        self,
        markets: List[MarketDict],
        players: List[PlayerDict],
        username: str,
    ) -> List[Tuple[int, str]]:
        player = self._player_info(players, username)
        if not player:
            return [(m["market_index"], "skip") for m in markets]

        owned = self._owned_products(player)
        balance = player.get("balance", 0)
        strategy: List[Tuple[int, str]] = []

        for m in markets:
            product = m["product"]
            price = m["market_fixed_price"]
            supply = m["market_supply"]

            if product in owned:
                avg_cost = owned[product]["avg_cost"]
                # Sell if market price is at least MARGIN% above our cost
                if price >= avg_cost * (1 + self.MARGIN):
                    strategy.append((m["market_index"], "sell"))
                # Buy if market price is below our cost (rebalance cheap)
                elif price < avg_cost * (1 - self.MARGIN) and balance > price * 5:
                    strategy.append((m["market_index"], "buy"))
                else:
                    strategy.append((m["market_index"], "skip"))
            else:
                # No inventory — buy if price is affordable and supply is decent
                can_afford = balance > price * 5
                if can_afford and supply > 20:
                    strategy.append((m["market_index"], "buy"))
                else:
                    strategy.append((m["market_index"], "skip"))

        return strategy

    def choose_buy_quantity(self, state: StateDict) -> int:
        max_aff = max(state.get("max_affordable", 1), 1)
        # Buy a moderate amount (40-70% of what we can afford)
        return max(1, int(max_aff * random.uniform(0.4, 0.7)))

    def choose_sell_quantity(self, state: StateDict) -> int:
        max_qty = max(state.get("seller_qty", 1), 1)
        # Sell most of what the market will take
        return max(1, int(max_qty * random.uniform(0.7, 1.0)))


class AggressiveBuyer(Strategy):
    """Always buy, always max quantity.

    Accumulates inventory rapidly; bets on selling at high prices later.
    """

    label = "AggressiveBuyer"
    description = "Buy everything at max quantity; accumulate inventory fast"

    def choose_strategy(
        self,
        markets: List[MarketDict],
        players: List[PlayerDict],
        username: str,
    ) -> List[Tuple[int, str]]:
        player = self._player_info(players, username)
        if not player:
            return [(m["market_index"], "skip") for m in markets]

        owned = self._owned_products(player)
        balance = player.get("balance", 0)
        strategy: List[Tuple[int, str]] = []

        for m in markets:
            price = m["market_fixed_price"]
            product = m["product"]
            # Only buy if we can afford at least a few units
            if balance > price * 3:
                strategy.append((m["market_index"], "buy"))
            elif product in owned:
                # If broke but have inventory, try to sell
                strategy.append((m["market_index"], "sell"))
            else:
                strategy.append((m["market_index"], "skip"))

        return strategy

    def choose_buy_quantity(self, state: StateDict) -> int:
        # Always max
        return max(state.get("max_affordable", 1), 1)

    def choose_sell_quantity(self, state: StateDict) -> int:
        return max(state.get("seller_qty", 1), 1)


class ConservativeTrader(Strategy):
    """Only trades when conditions are very favorable.

    - Buys only when market price is in the bottom quartile (very cheap).
    - Sells only when there's a clear profit (>25% margin).
    - Skips most markets to preserve capital.
    """

    label = "ConservativeTrader"
    description = "Trade only on very favorable conditions; preserve capital"

    BUY_THRESHOLD = 0.4  # Buy only if price is in bottom 40% of round prices
    SELL_MARGIN = 0.25  # Sell only with 25%+ margin

    def choose_strategy(
        self,
        markets: List[MarketDict],
        players: List[PlayerDict],
        username: str,
    ) -> List[Tuple[int, str]]:
        player = self._player_info(players, username)
        if not player:
            return [(m["market_index"], "skip") for m in markets]

        owned = self._owned_products(player)
        balance = player.get("balance", 0)

        # Compute price statistics for this round
        prices = [m["market_fixed_price"] for m in markets]
        if not prices:
            return [(m["market_index"], "skip") for m in markets]

        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price if max_price > min_price else 1

        strategy: List[Tuple[int, str]] = []

        for m in markets:
            product = m["product"]
            price = m["market_fixed_price"]
            # Normalized price position (0.0 = cheapest, 1.0 = most expensive)
            norm = (price - min_price) / price_range

            if product in owned:
                avg_cost = owned[product]["avg_cost"]
                margin = (price - avg_cost) / avg_cost if avg_cost > 0 else 0
                if margin >= self.SELL_MARGIN:
                    strategy.append((m["market_index"], "sell"))
                else:
                    strategy.append((m["market_index"], "skip"))
            else:
                # Only buy if price is very low relative to other markets
                if norm <= self.BUY_THRESHOLD and balance > price * 10:
                    strategy.append((m["market_index"], "buy"))
                else:
                    strategy.append((m["market_index"], "skip"))

        return strategy

    def choose_buy_quantity(self, state: StateDict) -> int:
        max_aff = max(state.get("max_affordable", 1), 1)
        # Small, cautious purchases (10-30% of affordable)
        return max(1, int(max_aff * random.uniform(0.1, 0.3)))

    def choose_sell_quantity(self, state: StateDict) -> int:
        max_qty = max(state.get("seller_qty", 1), 1)
        # Sell conservatively (30-60%)
        return max(1, int(max_qty * random.uniform(0.3, 0.6)))


class MarketSniper(Strategy):
    """Focus on high-supply markets with the best price-to-supply ratio.

    Computes a 'value score' = supply / price for each market.
    Prioritizes the top-scoring markets for buying.
    Sells into markets where the score is low (overpriced, low supply —
    other buyers won't compete, so the market is more likely to buy).
    """

    label = "MarketSniper"
    description = "Target high-supply, low-price markets; avoid competition"

    TOP_N = 2  # Only act on the top-N scored markets

    def choose_strategy(
        self,
        markets: List[MarketDict],
        players: List[PlayerDict],
        username: str,
    ) -> List[Tuple[int, str]]:
        player = self._player_info(players, username)
        if not player:
            return [(m["market_index"], "skip") for m in markets]

        owned = self._owned_products(player)
        balance = player.get("balance", 0)

        # Score each market: higher supply / lower price = better buy target
        scored: List[Tuple[int, float, MarketDict]] = []
        for m in markets:
            price = max(m["market_fixed_price"], 1)
            supply = m["market_supply"]
            score = supply / price  # value per FCFA
            scored.append((m["market_index"], score, m))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_indices = {idx for idx, _, _ in scored[: self.TOP_N]}
        bottom_indices = {idx for idx, _, _ in scored[-self.TOP_N :]}

        strategy: List[Tuple[int, str]] = []

        for m in markets:
            idx = m["market_index"]
            product = m["product"]

            if (
                idx in top_indices
                and product not in owned
                and balance > m["market_fixed_price"] * 5
            ):
                strategy.append((idx, "buy"))
            elif product in owned and idx in bottom_indices:
                # Low supply / high price market — good place to sell
                avg_cost = owned[product]["avg_cost"]
                if m["market_fixed_price"] > avg_cost:
                    strategy.append((idx, "sell"))
                else:
                    strategy.append((idx, "skip"))
            else:
                strategy.append((idx, "skip"))

        return strategy

    def choose_buy_quantity(self, state: StateDict) -> int:
        max_aff = max(state.get("max_affordable", 1), 1)
        # Sniper buys a focused chunk (50-80%)
        return max(1, int(max_aff * random.uniform(0.5, 0.8)))

    def choose_sell_quantity(self, state: StateDict) -> int:
        max_qty = max(state.get("seller_qty", 1), 1)
        return max(1, int(max_qty * random.uniform(0.6, 1.0)))


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_STRATEGIES: dict[str, type[Strategy]] = {
    cls.label.lower().replace(" ", ""): cls
    for cls in [
        RandomStrategy,
        BuyLowSellHigh,
        AggressiveBuyer,
        ConservativeTrader,
        MarketSniper,
    ]
}


def get_strategy(name: str) -> Strategy:
    """Instantiate a strategy by label (case-insensitive)."""
    cls = ALL_STRATEGIES.get(name.lower().replace(" ", ""))
    if cls is None:
        available = ", ".join(sorted(ALL_STRATEGIES.keys()))
        raise ValueError(f"Unknown strategy '{name}'. Available: {available}")
    return cls()


def list_strategies() -> list[tuple[str, str]]:
    """Return sorted list of (label, description) for all strategies."""
    return sorted(
        [(cls.label, cls.description) for cls in ALL_STRATEGIES.values()],
        key=lambda x: x[0],
    )
