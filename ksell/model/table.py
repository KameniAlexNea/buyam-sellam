"""Table model for KSell Entreprise.

Represents the game table that holds all active players and markets.
"""

import random
from typing import Any, Dict, List, Optional

from ksell.model.dice import Dice
from ksell.model.player import Player
from ksell.model.market_board import MarketBoard
from ksell.model.product import ProductModel
from ksell.pojo.market import Market
from ksell.pojo.product import Product


class Table:
    """The game table containing all players and active markets."""

    def __init__(self, players: Optional[List[Player]] = None, total_rounds: int = 10):
        self.players: List[Player] = players if players is not None else []
        self.markets: List[MarketBoard] = []
        self.dice: Dice = Dice()
        self.current_round: int = 0
        self.total_rounds: int = total_rounds

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

    def generate_markets(self, num_products: int = 5) -> List[MarketBoard]:
        """Generate random markets with random products and specifications."""
        self.dice.shake()
        self.markets.clear()

        # Available products for the game
        available_products = [
            Product(name="Cooked Rice", price=0),
            Product(name="Fufu", price=0),
            Product(name="Corn Flour", price=0),
            Product(name="Peanut Butter", price=0),
            Product(name="Smoked Fish", price=0),
        ]
        
        # Available market names
        market_names = [
            "Central Market",
            "North Market",
            "South Market",
            "Commercial Zone",
            "Free Port",
            "Harbor Market",
            "Village Market",
            "City Center",
        ]
        
        # Shuffle and select products for this game
        random.shuffle(available_products)
        selected_products = available_products[:min(num_products, len(available_products))]
        
        # Shuffle market names
        shuffled_names = market_names.copy()
        random.shuffle(shuffled_names)
        
        # Generate random markets
        for idx, product in enumerate(selected_products):
            max_qty = random.randint(50, 150)
            min_qty = random.randint(10, max_qty)
            
            market = Market(
                id=f"market_{idx}",
                name=shuffled_names[idx % len(shuffled_names)],
                min_qty=min_qty,
                max_qty=max_qty,
                tax_rate=round(random.uniform(0.01, 0.10), 2),
                product=product.name,
                fixed_price=random.randint(1, 4) * 100,  # 100-400 FCFA (dice 1-4)
            )
            market_board = MarketBoard(location=market, dice=self.dice)
            self.markets.append(market_board)

        return self.markets

    def initialize_player_inventory(self, units_per_player: int = 20) -> Dict[str, List[str]]:
        """Initialize each player with random starting products.
        
        Args:
            units_per_player: Total units to distribute per player (default 20)
            
        Returns:
            Dictionary mapping player username to their starting inventory strings
        """
        available_products = list(set([market.location.product for market in self.markets]))
        player_inventory_info = {}

        for player in self.players:
            # Randomly distribute units across available products
            remaining_units = units_per_player
            shuffled_products = available_products.copy()
            random.shuffle(shuffled_products)

            for idx, product_name in enumerate(shuffled_products):
                if remaining_units <= 0:
                    break
                # For the last product, give all remaining units
                if idx == len(shuffled_products) - 1:
                    quantity = remaining_units
                else:
                    # Random quantity between 1 and remaining units
                    quantity = random.randint(1, min(remaining_units, 10))

                product = Product(name=product_name, price=0)
                player.add_to_inventory(product, quantity)
                remaining_units -= quantity

            inventory_str = ", ".join([f"{item.product.name}: {item.quantity}" for item in player.inventory])
            player_inventory_info[player.username] = inventory_str

        return player_inventory_info

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
