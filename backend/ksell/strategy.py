"""AI strategy classes for Buyam-Sellam simulation.

Each strategy implements two decisions:
  1. **Strategy phase** — which action (buy/sell/skip) per market.
  2. **Action phase** — what quantity to buy/sell when prompted.

Strategies receive the same data that the REST API returns, so they
work identically whether driven by `game_sim_api.py` or `batch_sim.py`.
"""

import abc
import random
from typing import Any, Dict, List, Tuple

from ksell.utils.dice_prob import expected_sell_net


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
        round_number: int | None = None,
        total_rounds: int | None = None,
    ) -> List[Tuple[int, str]]:
        """Return a list of (market_index, action) tuples.

        Actions are 'buy', 'sell', or 'skip'.
        Only return 'sell' if the player owns the market's product.

        ``round_number``/``total_rounds`` let endgame-aware strategies plan
        for inventory spoilage and adjust risk by their position in the
        standings. Older strategies simply ignore them.
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

        # Group the active markets by product.
        by_product: Dict[str, List[MarketDict]] = {}
        for m in markets:
            by_product.setdefault(m["product"], []).append(m)

        # Best sell exit per product: highest expected net per unit.
        best_exit: Dict[str, Tuple[float, MarketDict]] = {}
        for prod, ms in by_product.items():
            best = max(
                ms,
                key=lambda m: expected_sell_net(
                    m["market_fixed_price"], m.get("tax_rate", 0.0)
                ),
            )
            best_exit[prod] = (
                expected_sell_net(
                    best["market_fixed_price"], best.get("tax_rate", 0.0)
                ),
                best,
            )

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
        return max(1, int(max_aff * random.uniform(0.5, 0.85)))

    def choose_sell_quantity(self, state: StateDict) -> int:
        # Selling only at the best exit — offload as much as the market takes.
        return max(state.get("seller_qty", 1), 1)


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

        by_product: Dict[str, List[MarketDict]] = {}
        for m in markets:
            by_product.setdefault(m["product"], []).append(m)

        best_exit: Dict[str, Tuple[float, MarketDict]] = {}
        for prod, ms in by_product.items():
            best = max(
                ms,
                key=lambda m: expected_sell_net(
                    m["market_fixed_price"], m.get("tax_rate", 0.0)
                ),
            )
            best_exit[prod] = (
                expected_sell_net(
                    best["market_fixed_price"], best.get("tax_rate", 0.0)
                ),
                best,
            )

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
        return max(1, int(max_aff * random.uniform(0.6, 0.95)))

    def choose_sell_quantity(self, state: StateDict) -> int:
        return max(state.get("seller_qty", 1), 1)


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
        ExpectedValueBot,
        Arbitrageur,
        EndgameTrader,
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
