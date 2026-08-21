"""Beginner bots — the EASY roster.

Deliberately weak: they ignore the 2d6 odds and trade rarely / conservatively,
so an Easy table is forgiving. ``ksell.model.difficulty`` restricts the Easy
pool to this tier (the user can only change the number of opponents).
"""

import random
from typing import Any, Dict, List, Tuple

from ksell.strategy.base import MarketDict, PlayerDict, StateDict, Strategy


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
        round_number: int | None = None,
        total_rounds: int | None = None,
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
        round_number: int | None = None,
        total_rounds: int | None = None,
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
