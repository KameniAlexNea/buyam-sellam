"""Table model for KSell Entreprise.

Represents the game table that holds all active players and markets.
"""

import random
from typing import Any, Dict, List, Optional

from ksell.model.dice import Dice
from ksell.model.player import Player
from ksell.model.market_board import MarketBoard
from ksell.pojo.market import Market
from ksell.pojo.tool import Tool
from ksell.pojo.user import User


class Table:
    """The game table containing all players and active markets."""

    def __init__(self):
        self.players: List[Player] = []
        self.markets: List[MarketBoard] = []
        self.dice: Dice = Dice()
        self.current_round: int = 0
        self.total_rounds: int = 10

    def add_player(self, player: Player) -> bool:
        for p in self.players:
            if p.username == player.username:
                return False
        self.players.append(player)
        return True

    def remove_player(self, username: str) -> bool:
        for i, p in enumerate(self.players):
            if p.username == username:
                self.players.pop(i)
                return True
        return False

    def get_player(self, username: str) -> Optional[Player]:
        for p in self.players:
            if p.username == username:
                return p
        return None

    def generate_markets(self) -> List[MarketBoard]:
        self.dice.shake()
        self.markets.clear()

        num_markets = min(3, max(1, (self.dice.total() - 4) // 3))

        market_options = [
            Market(id="lieu_1", name="Central Market",    min_qty=50,  max_qty=200,  tax_rate=0.05, product="Cooked Rice",     fixed_price=800),
            Market(id="lieu_2", name="North Market",      min_qty=30,  max_qty=150,  tax_rate=0.08, product="Fufu",            fixed_price=600),
            Market(id="lieu_3", name="South Market",      min_qty=40,  max_qty=180,  tax_rate=0.06, product="Corn Flour",      fixed_price=500),
            Market(id="lieu_4", name="Commercial Zone",   min_qty=100, max_qty=500,  tax_rate=0.03, product="Peanut Butter",   fixed_price=1000),
            Market(id="lieu_5", name="Free Port",         min_qty=200, max_qty=1000, tax_rate=0.02, product="Smoked Fish",     fixed_price=1200),
        ]

        selected = random.sample(market_options, min(num_markets, len(market_options)))

        for loc in selected:
            market = MarketBoard(location=loc, dice=self.dice)
            self.markets.append(market)

        return self.markets

    def next_round(self) -> Dict[str, Any]:
        self.current_round += 1
        if self.current_round > self.total_rounds:
            return {"error": "Game over", "round": self.current_round}

        for market in self.markets:
            market.refresh()

        for player in self.players:
            for market in self.markets:
                market.add_passing_player(player.username)

        return {
            "round": self.current_round,
            "dice": self.dice.to_dict(),
            "markets": [m.to_dict() for m in self.markets],
            "condition": self.dice.market_condition(),
        }

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        sorted_players = sorted(self.players, key=lambda p: p.balance, reverse=True)
        return [
            {
                "rank": i + 1,
                "username": p.username,
                "balance": p.balance,
                "stars": p.star_count,
                "competitions": p.competition_count,
            }
            for i, p in enumerate(sorted_players)
        ]

    def end_game(self) -> Dict[str, Any]:
        leaderboard = self.get_leaderboard()
        winner = leaderboard[0] if leaderboard else None
        return {
            "winner": winner,
            "leaderboard": leaderboard,
            "total_rounds": self.current_round,
        }

    def __repr__(self) -> str:
        return f"Table(players={len(self.players)}, markets={len(self.markets)}, round={self.current_round})"
