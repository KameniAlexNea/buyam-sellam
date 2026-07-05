"""Constraint POJO for KSell Entreprise."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Constraint:
    """Constraint that can be applied to a market location."""

    id: str = ""
    name: str = ""
    description: str = ""

    def test(self, player_data: Dict[str, Any]) -> bool:
        """Test if a player meets this constraint. Default always passes."""
        return True
