"""Random number utilities for KSell Entreprise."""

import random
from typing import List, Optional


def uniform_int(n: int) -> int:
    """Return a random integer in [0, n)."""
    return random.randint(0, n - 1)


def uniform_int_range(a: int, b: int) -> int:
    """Return a random integer in [a, b]."""
    return random.randint(a, b)


def uniform_float(a: float, b: float) -> float:
    """Return a random float in [a, b]."""
    return random.uniform(a, b)


def bernoulli(p: float) -> bool:
    """Return True with probability p."""
    return random.random() < p


def gaussian(mu: float = 0.0, sigma: float = 1.0) -> float:
    """Return a random float from normal distribution."""
    return random.gauss(mu, sigma)


def shuffle_list(lst: list) -> list:
    """Return a shuffled copy of the list."""
    result = lst.copy()
    random.shuffle(result)
    return result


def weighted_choice(options: List, weights: Optional[List[float]] = None):
    """Return a randomly chosen option, optionally weighted."""
    if weights:
        return random.choices(options, weights=weights, k=1)[0]
    return random.choice(options)
