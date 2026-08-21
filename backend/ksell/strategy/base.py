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
# Shared helpers
# ---------------------------------------------------------------------------


def best_exit_per_product(
    markets: List[MarketDict],
) -> Dict[str, Tuple[float, MarketDict]]:
    """Map product → (expected sell net/unit, best market) for the active markets.

    Shared by the EV-family bots so "which market should I sell into" is
    computed exactly once instead of being copy-pasted.
    """
    by_product: Dict[str, List[MarketDict]] = {}
    for m in markets:
        by_product.setdefault(m["product"], []).append(m)
    best: Dict[str, Tuple[float, MarketDict]] = {}
    for prod, ms in by_product.items():
        top = max(
            ms,
            key=lambda m: expected_sell_net(
                m["market_fixed_price"], m.get("tax_rate", 0.0)
            ),
        )
        best[prod] = (
            expected_sell_net(top["market_fixed_price"], top.get("tax_rate", 0.0)),
            top,
        )
    return best


def size_position(edge_ratio: float, max_qty: int, rounds_left: int, selling: bool) -> int:
    """Size a position: bigger edge + more urgency → more committed.

    ``edge_ratio`` is the fractional expected edge above the trade hurdle
    (e.g. 0.1 = 10%). ``rounds_left`` is the number of rounds remaining
    (0 = final round). ``selling`` flips the urgency: sells get aggressive as
    the end nears (dodge spoilage), buys go calm (don't open positions you
    can't exit).
    """
    if max_qty <= 1:
        return max_qty
    edge = max(0.0, min(0.5, edge_ratio))
    frac = 0.4 + 0.6 * (edge / 0.20)  # 0.4 at the hurdle → 1.0 at 20%+ edge
    if selling:
        time = 1.0 - 0.4 * min(1.0, rounds_left / 4.0)  # urgent near the end
    else:
        time = 0.4 + 0.6 * min(1.0, rounds_left / 4.0)  # calm near the end
    return max(1, min(max_qty, int(max_qty * min(1.0, frac) * time)))
