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

    The "favorable" tests are defined against the free starter-stock reality:
      - Buys only the cheap end of this round's markets (bottom 40%), and is
        allowed to average into a small position it already holds — otherwise,
        because starter stock covers most products, it would never buy.
      - Sells bought stock only with a real 25%+ margin over cost; sells FREE
        (starter) stock only into a clearly expensive market (top 40%).
      - Keeps positions small and skips most markets to preserve capital.
    """

    label = "ConservativeTrader"
    description = "Trade only on very favorable conditions; preserve capital"

    BUY_THRESHOLD = 0.4  # buy only if price is in the bottom 40% of round prices
    SELL_MARGIN = 0.25  # sell bought stock only with 25%+ margin over cost
    SELL_RANK = 0.6  # sell free stock only into the top 40% markets
    MIN_EXIT_BUFFER = 0.10  # a buy needs an exit ≥10% above the entry price
    MAX_POSITION = 30  # don't hoard more than this many units of one product
    BUY_RESERVE = 10  # keep at least 10x the unit price in cash

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

        # Price statistics for this round → cheap/expensive rank per market.
        prices = [m["market_fixed_price"] for m in markets]
        if not prices:
            return [(m["market_index"], "skip") for m in markets]

        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price if max_price > min_price else 1

        # Highest-priced market for each product THIS round → is there an exit?
        best_exit_price: Dict[str, float] = {}
        for m in markets:
            prod = m["product"]
            best_exit_price[prod] = max(
                best_exit_price.get(prod, 0.0), m["market_fixed_price"]
            )

        strategy: List[Tuple[int, str]] = []
        for m in markets:
            product = m["product"]
            price = m["market_fixed_price"]
            # Normalized price position (0.0 = cheapest, 1.0 = most expensive)
            norm = (price - min_price) / price_range

            item = owned.get(product)
            position = item["quantity"] if item else 0
            avg_cost = item["avg_cost"] if item else 0.0

            # Favorable sell?
            if item is not None:
                if avg_cost > 0:
                    margin = (price - avg_cost) / avg_cost
                    favorable_sell = margin >= self.SELL_MARGIN
                else:
                    # Free starter stock: any price is profit, but stay picky —
                    # only take it to a clearly expensive market.
                    favorable_sell = norm >= self.SELL_RANK
            else:
                favorable_sell = False

            # Cheap buy — but only when this product can ALSO exit higher THIS
            # round. Requiring a real exit stops the bot from hoarding stock it
            # can never sell (that's exactly how it bled cash before).
            exit_price = best_exit_price.get(product, price)
            favorable_buy = (
                norm <= self.BUY_THRESHOLD
                and exit_price >= price * (1 + self.MIN_EXIT_BUFFER)
                and balance > price * self.BUY_RESERVE
                and position < self.MAX_POSITION
            )

            if favorable_buy:
                strategy.append((m["market_index"], "buy"))
            elif favorable_sell:
                strategy.append((m["market_index"], "sell"))
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
