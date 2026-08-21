"""AI bot strategies, organised by difficulty tier.

- beginner/  → Easy roster:  Random, ConservativeTrader
- medium/    → Medium roster: BuyLowSellHigh, AggressiveBuyer, MarketSniper
- advanced/  → Hard roster:  ExpectedValue, Arbitrageur, Endgame

``ALL_STRATEGIES`` / ``get_strategy()`` / ``list_strategies()`` keep the flat
registry that the API and the difficulty pools (`ksell.model.difficulty`)
rely on, so importing stays unchanged after the split.
"""

from ksell.strategy.base import (
    MarketDict,
    PlayerDict,
    StateDict,
    Strategy,
    best_exit_per_product,
    size_position,
)
from ksell.strategy.beginner import ConservativeTrader, RandomStrategy
from ksell.strategy.medium import AggressiveBuyer, BuyLowSellHigh, MarketSniper
from ksell.strategy.advanced import Arbitrageur, EndgameTrader, ExpectedValueBot

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


__all__ = [
    "ALL_STRATEGIES",
    "get_strategy",
    "list_strategies",
    "Strategy",
    "MarketDict",
    "PlayerDict",
    "StateDict",
    "best_exit_per_product",
    "size_position",
    "RandomStrategy",
    "ConservativeTrader",
    "BuyLowSellHigh",
    "AggressiveBuyer",
    "MarketSniper",
    "ExpectedValueBot",
    "Arbitrageur",
    "EndgameTrader",
]
