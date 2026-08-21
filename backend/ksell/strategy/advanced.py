"""Advanced bots — the HARD roster.

Probability-aware EV traders: they use the real 2d6 odds, choose the best sell
exit per product, size positions by edge + time pressure, and (Endgame) plan
for spoilage and adjust risk by standing. Hard games only — ``ksell.model.
difficulty`` restricts the Hard pool to this tier.
"""

import random
from typing import Any, Dict, List, Tuple

from ksell.utils.dice_prob import expected_sell_net
from ksell.strategy.base import (
    MarketDict,
    PlayerDict,
    StateDict,
    Strategy,
    best_exit_per_product,
    size_position,
)


class ExpectedValueBot(Strategy):
    """Probability-aware trader: uses the 2d6 odds to buy low / sell high.

    For every product it owns it sells into whichever market for that product
    maximises the **expected net revenue** — sell probability × expected dice
    price × (1 − tax) — and only when that clears the entry fee plus a margin.
    It buys only when holding the product has positive expected value versus
    the best available sell exit.
    """

    label = "ExpectedValue"
    description = "Buy/sell using 2d6 odds and expected value"

    MARGIN = 0.10  # buy only if expected exit beats cost by 10%
    SELL_GAIN = 0.05  # sell only if expected exit beats cost by 5%

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

        best_exit = best_exit_per_product(markets)

        strategy: List[Tuple[int, str]] = []
        for m in markets:
            idx = m["market_index"]
            prod = m["product"]
            price = m["market_fixed_price"]

            if prod in owned:
                item = owned[prod]
                exit_ev, exit_m = best_exit.get(prod, (0.0, None))
                # Only ever sell in the single best exit for a product —
                # selling twice would pay the entry fee twice.
                if exit_m is not None and exit_m["market_index"] == idx:
                    fee = m.get("sell_entry_fee", 0)
                    gross = exit_ev - item["avg_cost"]
                    if gross > item["avg_cost"] * self.SELL_GAIN + fee / max(
                        item["quantity"], 1
                    ):
                        strategy.append((idx, "sell"))
                    else:
                        strategy.append((idx, "skip"))
                else:
                    strategy.append((idx, "skip"))
            else:
                exit_ev, _ = best_exit.get(prod, (0.0, None))
                cost = price * (1 + m.get("tax_rate", 0.0))
                if exit_ev > cost * (1 + self.MARGIN) and balance > cost:
                    strategy.append((idx, "buy"))
                else:
                    strategy.append((idx, "skip"))

        return strategy

    def choose_buy_quantity(self, state: StateDict) -> int:
        max_aff = max(state.get("max_affordable", 1), 1)
        rounds_left = max(
            0, state.get("total_rounds", 1) - state.get("round_number", 0)
        )
        # Size by expected edge, staying calmer near the end (don't open
        # positions you can't exit).
        return size_position(0.15, max_aff, rounds_left, selling=False)

    def choose_sell_quantity(self, state: StateDict) -> int:
        max_qty = max(state.get("seller_qty", 1), 1)
        rounds_left = max(
            0, state.get("total_rounds", 1) - state.get("round_number", 0)
        )
        # Selling only at the best exit — offload more aggressively near the
        # end to dodge spoilage.
        return size_position(0.20, max_qty, rounds_left, selling=True)


class Arbitrageur(Strategy):
    """Cross-market spread hunter.

    Groups the active markets by product and buys in the CHEAPEST market while
    selling into the most EXPENSIVE one, whenever the spread clearly covers
    taxes, the entry fee and a margin. Concentrates on the top few products
    instead of scattering its bets.
    """

    label = "Arbitrageur"
    description = "Buy the cheap market, sell the expensive one, same product"

    TOP_N = 2  # only trade the N best spreads this round
    MIN_EDGE = 0.18  # expensive exit must beat cheap cost by 18%

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

        by_product: Dict[str, List[MarketDict]] = {}
        for m in markets:
            by_product.setdefault(m["product"], []).append(m)

        # Rank products by expected spread (expensive exit EV − cheap buy cost).
        spreads: List[Tuple[float, str, MarketDict, MarketDict]] = []
        for prod, ms in by_product.items():
            if len(ms) < 2:
                continue
            cheap = min(ms, key=lambda m: m["market_fixed_price"])
            rich = max(ms, key=lambda m: m["market_fixed_price"])
            if cheap["market_index"] == rich["market_index"]:
                continue
            buy_cost = cheap["market_fixed_price"] * (1 + cheap.get("tax_rate", 0.0))
            sell_ev = expected_sell_net(
                rich["market_fixed_price"], rich.get("tax_rate", 0.0)
            )
            edge = sell_ev - buy_cost * (1 + self.MIN_EDGE)
            spreads.append((edge, prod, cheap, rich))

        spreads.sort(key=lambda x: x[0], reverse=True)
        targets = [t for t in spreads[: self.TOP_N] if t[0] > 0]

        # Sell into the rich market of a targeted product we already hold.
        sell_indices = {t[3]["market_index"] for t in targets if t[1] in owned}

        strategy: List[Tuple[int, str]] = []
        for m in markets:
            idx = m["market_index"]
            prod = m["product"]
            if idx in sell_indices:
                strategy.append((idx, "sell"))
                continue
            # Buy in the cheap market of a targeted product (if not holding).
            target = next((t for t in targets if t[1] == prod), None)
            if (
                target
                and prod not in owned
                and idx == target[2]["market_index"]
                and balance > target[2]["market_fixed_price"]
            ):
                strategy.append((idx, "buy"))
            else:
                strategy.append((idx, "skip"))

        return strategy

    def choose_buy_quantity(self, state: StateDict) -> int:
        max_aff = max(state.get("max_affordable", 1), 1)
        # Load up on the cheap side — the spread is the whole edge.
        return max(1, int(max_aff * random.uniform(0.7, 1.0)))

    def choose_sell_quantity(self, state: StateDict) -> int:
        return max(state.get("seller_qty", 1), 1)


class EndgameTrader(Strategy):
    """EV trading that also understands rounds and its chances of winning.

    Same expected-value logic as ExpectedValueBot, plus:
      - Endgame: in the final rounds it liquidates inventory (holding to the
        end means 100% spoilage), selling into the best exit as long as the
        expected net beats zero — even at a loss versus cost.
      - Win-probability: if it is trailing the field it takes riskier,
        higher-EV trades (lower buy margin, bigger sells); if it is leading
        it protects the lead (requires a clearer margin).
    """

    label = "Endgame"
    description = "EV trading with spoilage + win-probability awareness"

    LIQUIDATION_RADIUS = 2  # start dumping this many rounds before the end
    MARGIN_BASE = 0.10
    SELL_GAIN_BASE = 0.05

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
        round_number = round_number or 1
        total_rounds = total_rounds or round_number

        # Standing vs the rest of the table (net worth = cash + inventory).
        ranked = sorted(
            players,
            key=lambda p: p.get("balance", 0) + self._inventory_value(p),
            reverse=True,
        )
        position = next(
            (i for i, p in enumerate(ranked) if p["username"] == username),
            len(ranked),
        )
        trailing = position > (len(ranked) - 1) // 2
        liquidating = (total_rounds - round_number) < self.LIQUIDATION_RADIUS

        # Chase when behind (riskier), protect when ahead (tighter).
        margin = self.MARGIN_BASE * (0.5 if trailing else 1.5)
        sell_gain = self.SELL_GAIN_BASE * (0.0 if (trailing or liquidating) else 1.5)

        best_exit = best_exit_per_product(markets)

        strategy: List[Tuple[int, str]] = []
        for m in markets:
            idx = m["market_index"]
            prod = m["product"]
            price = m["market_fixed_price"]

            if prod in owned:
                item = owned[prod]
                exit_ev, exit_m = best_exit.get(prod, (0.0, None))
                if exit_m is not None and exit_m["market_index"] == idx:
                    fee = m.get("sell_entry_fee", 0)
                    if liquidating:
                        # Any positive expected net beats spoiling to zero.
                        worth_it = exit_ev > fee / max(item["quantity"], 1)
                    else:
                        worth_it = exit_ev - item["avg_cost"] > (
                            item["avg_cost"] * sell_gain
                            + fee / max(item["quantity"], 1)
                        )
                    strategy.append((idx, "sell" if worth_it else "skip"))
                else:
                    strategy.append((idx, "skip"))
            else:
                exit_ev, _ = best_exit.get(prod, (0.0, None))
                cost = price * (1 + m.get("tax_rate", 0.0))
                # Don't open new positions while liquidating the final stock.
                if not liquidating and exit_ev > cost * (1 + margin) and balance > cost:
                    strategy.append((idx, "buy"))
                else:
                    strategy.append((idx, "skip"))

        return strategy

    def choose_buy_quantity(self, state: StateDict) -> int:
        max_aff = max(state.get("max_affordable", 1), 1)
        rounds_left = max(
            0, state.get("total_rounds", 1) - state.get("round_number", 0)
        )
        # Don't over-commit late — liquidation happens at the strategy level.
        return size_position(0.18, max_aff, rounds_left, selling=False)

    def choose_sell_quantity(self, state: StateDict) -> int:
        # When we decide to sell we dump everything the market will take.
        return max(state.get("seller_qty", 1), 1)
