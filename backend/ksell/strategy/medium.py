"""Medium bots — the MEDIUM roster.

Classic heuristics: they react to prices and supply but ignore the 2d6 odds,
so they're a fair step up from beginner without being unbeatable. This is the
pool the user picks from on Medium difficulty.
"""

import random
from typing import Any, Dict, List, Tuple

from ksell.strategy.base import MarketDict, PlayerDict, StateDict, Strategy


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
        round_number: int | None = None,
        total_rounds: int | None = None,
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
        round_number: int | None = None,
        total_rounds: int | None = None,
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
        round_number: int | None = None,
        total_rounds: int | None = None,
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
