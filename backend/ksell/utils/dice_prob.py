"""2d6 probability helpers for AI strategies.

Every trade is gated by a dice roll:
  - a BUY  succeeds iff dice_price = total*100 >= market_price
  - a SELL succeeds iff dice_price = total*100 <= market_price

This module is the single source of truth for those probabilities so the
strategies can reason about expected value instead of guessing.

dice_price = total * 100, total in 2..12  →  dice_price in 200..1200 FCFA.
"""

import math

# counts[total] = number of ways to roll `total` with 2d6 (out of 36)
DICE_COUNTS: dict[int, int] = {
    2: 1,
    3: 2,
    4: 3,
    5: 4,
    6: 5,
    7: 6,
    8: 5,
    9: 4,
    10: 3,
    11: 2,
    12: 1,
}
DICE_TOTAL = 36

# Precompute cumulative / conditional tables once.
_P_AT_MOST: dict[int, float] = {}  # P(total <= s)   for s in 2..12
_P_AT_LEAST: dict[int, float] = {}  # P(total >= t)   for t in 2..12
_E_LE: dict[int, float] = {}  # E[total | total <= s] for s in 2..12

_cum = 0.0
for t in range(2, 13):
    _cum += DICE_COUNTS[t]
    _P_AT_MOST[t] = _cum / DICE_TOTAL
for t in range(2, 13):
    _P_AT_LEAST[t] = 1.0 - _P_AT_MOST.get(t - 1, 0.0)
for s in range(2, 13):
    numer = sum(v * DICE_COUNTS[v] for v in range(2, s + 1))
    denom = sum(DICE_COUNTS[v] for v in range(2, s + 1))
    _E_LE[s] = numer / denom if denom else 0.0


def p_buy_success(market_price: float) -> float:
    """Probability a BUY attempt succeeds: P(2d6*100 >= market_price)."""
    t = int(math.ceil(market_price / 100.0))
    if t <= 2:
        return 1.0
    if t > 12:
        return 0.0
    return _P_AT_LEAST[t]


def p_sell_success(market_price: float) -> float:
    """Probability a SELL attempt succeeds: P(2d6*100 <= market_price)."""
    s = int(math.floor(market_price / 100.0))
    if s < 2:
        return 0.0
    if s >= 12:
        return 1.0
    return _P_AT_MOST[s]


def expected_sell_price(market_price: float) -> float:
    """Expected dice price per unit WHEN a sell succeeds (FCFA).

    Sell revenue = dice_price = total*100, conditioned on total <= price/100.
    """
    s = int(math.floor(market_price / 100.0))
    if s < 2:
        return 0.0
    if s >= 12:
        return 7.0 * 100.0  # unconditional mean of 2d6
    return _E_LE[s] * 100.0


def expected_sell_net(market_price: float, tax_rate: float) -> float:
    """Expected net revenue per unit of an attempted sell (includes failure).

    = P(sell works) * E[dice price | works] * (1 - tax_rate)
    """
    return (
        p_sell_success(market_price)
        * expected_sell_price(market_price)
        * (1.0 - tax_rate)
    )
