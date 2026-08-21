"""Difficulty configuration for KSell Entreprise.

Defines difficulty presets that control market generation parameters
and player starting conditions.

=== Preset Overview ===

+---------------------------+--------+--------+------+
| Parameter                 | Easy   | Medium | Hard |
+---------------------------+--------+--------+------+
| starting_balance          | 80,000 | 50,000 | 30,000
| units_per_player          | 30     | 20     | 10
| min_qty range             | 30-60  | 10-50  | 5-30
| max_qty range             | 100-200| 50-150 | 20-80
| tax_rate range            | 1-4%   | 1-10%  | 5-15%
| fixed_price range         | 200-800| 200-1200| 600-1200|
| markets_per_product range | 1-2    | 1-3    | 2-4
| num_markets_per_round     | 2-4    | 1-3    | 1-2
+---------------------------+--------+--------+------+
"""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Tuple


# ---------------------------------------------------------------------------
# Difficulty enum
# ---------------------------------------------------------------------------


class Difficulty(str, Enum):
    """Game difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ---------------------------------------------------------------------------
# DifficultyConfig dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DifficultyConfig:
    """Immutable configuration for a difficulty level.

    All *range* attributes are (min, max) tuples.  Concrete values are
    sampled uniformly from these ranges at game start.

    Attributes:
        name: Human-readable label (e.g. "Easy").
        description: One-line description shown to players.
        starting_balance: Initial cash for each player.
        units_per_player: Total inventory units distributed at start.
        min_qty_range: (min, max) for the *lower bound* of market quantity.
        max_qty_range: (min, max) for the *upper bound* of market quantity.
        tax_rate_range: (min, max) tax rate as a fraction (e.g. 0.05 = 5%).
        fixed_price_range: (min, max) for the market fixed price in FCFA.
        markets_per_product_range: (min, max) how many markets a product appears in.
        num_markets_per_round_range: (min, max) active markets per round.
    """

    name: str
    description: str

    # Player starting conditions
    starting_balance: float
    units_per_player: int

    # Market generation ranges
    min_qty_range: Tuple[int, int]
    max_qty_range: Tuple[int, int]
    tax_rate_range: Tuple[float, float]
    fixed_price_range: Tuple[int, int]
    markets_per_product_range: Tuple[int, int]

    # Round configuration
    num_markets_per_round_range: Tuple[int, int]

    # ------------------------------------------------------------------
    # Sampling helpers — pick concrete values from the ranges
    # ------------------------------------------------------------------

    def sample_min_qty(self) -> int:
        """Return a random min_qty within the configured range."""
        return random.randint(*self.min_qty_range)

    def sample_max_qty(self) -> int:
        """Return a random max_qty within the configured range."""
        return random.randint(*self.max_qty_range)

    def sample_tax_rate(self) -> float:
        """Return a random tax rate within the configured range."""
        return round(random.uniform(*self.tax_rate_range), 2)

    def sample_fixed_price(self) -> int:
        """Return a random fixed price within the configured range."""
        return random.randint(*self.fixed_price_range)

    def sample_markets_per_product(self) -> int:
        """Return a random number of markets per product."""
        return random.randint(*self.markets_per_product_range)

    def sample_num_markets_per_round(self, total_markets: int) -> int:
        """Return a random number of active markets per round, capped by total."""
        max_val = min(self.num_markets_per_round_range[1], total_markets)
        return random.randint(self.num_markets_per_round_range[0], max_val)

    # ------------------------------------------------------------------
    # Preset factory
    # ------------------------------------------------------------------

    @classmethod
    def from_difficulty(cls, difficulty: Difficulty) -> "DifficultyConfig":
        """Return the preset config for the given difficulty level."""
        return _PRESETS[difficulty]


# ---------------------------------------------------------------------------
# Preset definitions
# ---------------------------------------------------------------------------

_PRESETS: dict[Difficulty, DifficultyConfig] = {
    Difficulty.EASY: DifficultyConfig(
        name="Easy",
        description="Generous starting resources, low taxes, fewer competitors per product.",
        starting_balance=80_000,
        units_per_player=30,
        min_qty_range=(30, 60),
        max_qty_range=(100, 200),
        tax_rate_range=(0.01, 0.04),
        fixed_price_range=(200, 800),
        markets_per_product_range=(1, 2),
        num_markets_per_round_range=(2, 4),
    ),
    Difficulty.MEDIUM: DifficultyConfig(
        name="Medium",
        description="Balanced challenge — the standard KSell experience.",
        starting_balance=50_000,
        units_per_player=20,
        min_qty_range=(10, 50),
        max_qty_range=(50, 150),
        tax_rate_range=(0.01, 0.10),
        fixed_price_range=(200, 1200),
        markets_per_product_range=(1, 3),
        num_markets_per_round_range=(1, 3),
    ),
    Difficulty.HARD: DifficultyConfig(
        name="Hard",
        description="Tight budget, high taxes, more competition — for seasoned traders.",
        starting_balance=30_000,
        units_per_player=10,
        min_qty_range=(5, 30),
        max_qty_range=(20, 80),
        tax_rate_range=(0.05, 0.15),
        fixed_price_range=(600, 1200),
        markets_per_product_range=(2, 4),
        num_markets_per_round_range=(1, 2),
    ),
}


# ---------------------------------------------------------------------------
# Bot strategy pools per difficulty level
# ---------------------------------------------------------------------------
# The difficulty doesn't just tune the markets — it decides WHICH bot brains
# are allowed at the table. Easy only gets weak bots (fixed roster), Medium the
# classic heuristics, Hard only the probability-aware traders.

BOT_POOLS: dict[Difficulty, list[str]] = {
    Difficulty.EASY: ["random", "conservativetrader"],
    Difficulty.MEDIUM: [
        "buylowsellhigh",
        "marketsniper",
        "aggressivebuyer",
        "conservativetrader",
    ],
    Difficulty.HARD: ["expectedvalue", "arbitrageur", "endgame"],
}


def allowed_bot_strategies(difficulty: Difficulty) -> list[str]:
    """Return the strategy keys allowed for a difficulty level."""
    return list(BOT_POOLS.get(difficulty, BOT_POOLS[Difficulty.MEDIUM]))


def pick_bot_strategy(difficulty: Difficulty) -> str:
    """Pick a random strategy from the level's allowed pool."""
    return random.choice(allowed_bot_strategies(difficulty))
