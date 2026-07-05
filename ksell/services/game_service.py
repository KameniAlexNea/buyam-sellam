"""Game Service for KSell Entreprise.

Manages the complete game state including the table, players, markets,
dice rolling, trading, production, events, and game progression.
"""

import random
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from ksell.model.dice import Dice
from ksell.model.player import Player
from ksell.model.market_board import MarketBoard
from ksell.model.table import Table
from ksell.pojo.card import Card
from ksell.pojo.market import Market
from ksell.pojo.tool import Tool
from ksell.pojo.product import Product
from ksell.pojo.user import User
from ksell.utils.helpers import (
    get_card_options,
    get_market_location_options,
    get_tool_options,
    get_penalty_options,
)


# Raw materials that can be purchased for production
RAW_MATERIALS = [
    {"id": "mat_1", "name": "Cassava",      "price": 500,  "yield": 10, "description": "Raw cassava for fufu production"},
    {"id": "mat_2", "name": "Raw Rice",     "price": 800,  "yield": 15, "description": "Raw rice for cooking"},
    {"id": "mat_3", "name": "Corn",         "price": 400,  "yield": 12, "description": "Raw corn for various dishes"},
    {"id": "mat_4", "name": "Peanuts",      "price": 600,  "yield": 8,  "description": "Raw peanuts for oil and sauce"},
    {"id": "mat_5", "name": "Dried Fish",   "price": 1500, "yield": 5,  "description": "Dried fish for protein"},
    {"id": "mat_6", "name": "Palm Oil",     "price": 1000, "yield": 20, "description": "Palm oil for cooking"},
    {"id": "mat_7", "name": "Milk Powder",  "price": 1200, "yield": 15, "description": "Powdered milk"},
    {"id": "mat_8", "name": "Sugar",        "price": 300,  "yield": 25, "description": "Sugar for sweet dishes"},
]

# Finished products that can be sold
FINISHED_PRODUCTS = [
    {"id": "prod_1", "name": "Fufu",            "sell_price": 1500, "raw_material": "Cassava",    "description": "Traditional fufu"},
    {"id": "prod_2", "name": "Cooked Rice",     "sell_price": 2000, "raw_material": "Raw Rice",   "description": "Cooked rice"},
    {"id": "prod_3", "name": "Corn Flour",      "sell_price": 1200, "raw_material": "Corn",       "description": "Corn flour"},
    {"id": "prod_4", "name": "Peanut Butter",   "sell_price": 2500, "raw_material": "Peanuts",    "description": "Peanut butter"},
    {"id": "prod_5", "name": "Smoked Fish",     "sell_price": 3000, "raw_material": "Dried Fish", "description": "Smoked fish"},
    {"id": "prod_6", "name": "Refined Oil",     "sell_price": 1800, "raw_material": "Palm Oil",   "description": "Refined palm oil"},
    {"id": "prod_7", "name": "Reconstituted Milk", "sell_price": 1500, "raw_material": "Milk Powder", "description": "Reconstituted milk"},
    {"id": "prod_8", "name": "Sugar Syrup",     "sell_price": 800,  "raw_material": "Sugar",      "description": "Sugar syrup"},
]

# Random events that can happen during the game
RANDOM_EVENTS = [
    {"name": "🌧️ Heavy Rain",            "description": "Heavy rain disrupts transportation",     "effect": "loss", "min": 500,  "max": 2000,  "probability": 0.15},
    {"name": "🎉 Local Festival",         "description": "Local festival increases demand",          "effect": "gain", "min": 1000, "max": 5000,  "probability": 0.10},
    {"name": "🚛 Truck Breakdown",        "description": "Truck breakdown delays delivery",           "effect": "loss", "min": 1000, "max": 3000,  "probability": 0.12},
    {"name": "💰 Government Subsidy",     "description": "Government subsidy for small businesses",   "effect": "gain", "min": 2000, "max": 8000,  "probability": 0.08},
    {"name": "🔥 Market Fire",            "description": "Fire in the market damages inventory",      "effect": "loss", "min": 2000, "max": 5000,  "probability": 0.07},
    {"name": "🤝 Successful Partnership", "description": "Successful partnership brings new customers","effect": "gain", "min": 3000, "max": 10000, "probability": 0.06},
    {"name": "📈 Price Surge",            "description": "Prices go up, your inventory gains value",  "effect": "gain", "min": 1500, "max": 6000,  "probability": 0.10},
    {"name": "📉 Price Crash",            "description": "Market crash, prices drop significantly",    "effect": "loss", "min": 1000, "max": 4000,  "probability": 0.10},
    {"name": "🎁 Patron Donation",        "description": "A benefactor donates to your business",     "effect": "gain", "min": 5000, "max": 15000, "probability": 0.04},
    {"name": "⚠️ Health Inspection",      "description": "Health inspection finds violations",        "effect": "loss", "min": 500,  "max": 2000,  "probability": 0.13},
]


class GameService:
    """Manages the KSell game state and logic."""

    DICE_BASE = 100  # FCFA per dice point; range: dice 2 → 200 FCFA, dice 12 → 1,200 FCFA

    def __init__(self):
        self.table = Table()
        self.current_player: Optional[Player] = None
        self.game_log: List[str] = []
        self.is_game_active = False
        self.events_log: List[Dict[str, Any]] = []
        self.current_dice_price: int = 0  # player's price this round

    def start_game(self, player_username: str, player_fortune: float = 10000.0) -> Dict[str, Any]:
        """Start a new game with the given player.

        Args:
            player_username: Player's username
            player_fortune: Starting fortune

        Returns:
            Dict with game start info
        """
        # Create or update current player
        user = User(
            username=player_username,
            balance=player_fortune,
            is_verified=True,
        )
        self.current_player = Player(user=user)
        # Starting inventory: a mix of products found in the available markets
        self.current_player.basic_stock = 0  # legacy field (unused now)
        self.current_player.inventory = []
        self.current_player.finished_products = [
            {"id": "prod_1", "name": "Fufu",       "quantity": 20, "sell_price": 600},
            {"id": "prod_2", "name": "Cooked Rice", "quantity": 20, "sell_price": 800},
            {"id": "prod_3", "name": "Corn Flour",  "quantity": 20, "sell_price": 500},
        ]

        # Add player to table
        self.table.add_player(self.current_player)

        # Add some AI opponents for demo
        ai_names = ["Amina", "Jean", "Fatou", "Paul", "Aïssatou"]
        for name in ai_names:
            ai_user = User(username=name, balance=random.uniform(5000, 20000))
            ai_player = Player(user=ai_user)
            # Give AI players some random tools
            tool_opts = get_tool_options()
            nb_tools = random.randint(0, 2)
            for _ in range(nb_tools):
                d = random.choice(tool_opts)
                tool = Tool(id=d["id"], name=d["name"], cost=d["cost"], capacity=d["capacity"])
                ai_player.add_tool(tool)
            self.table.add_player(ai_player)

        # Generate initial markets
        markets = self.table.generate_markets()

        self.is_game_active = True
        self.current_dice_price = self.table.dice.total() * self.DICE_BASE

        # AI players immediately post orders for round 0
        self._ai_turn()
        self.game_log.append(f"🎮 Game started with {len(self.table.players)} players!")
        self.game_log.append(f"👤 {player_username} | 💰 {player_fortune:,.0f} FCFA | 🎲 Your price: {self.current_dice_price:,} FCFA/unit")
        self.game_log.append(f"📊 Markets: {len(markets)}")

        return {
            "success": True,
            "message": f"Game started! {len(self.table.players)} players, {len(markets)} markets.",
            "tour": self.table.current_round,
            "player_fortune": self.current_player.balance,
            "player_rank": self._get_player_rank(),
            "markets": [m.to_dict() for m in markets],
            "dice": self.table.dice.to_dict(),
            "leaderboard": self.table.get_leaderboard(),
            "log": self._get_recent_log(10),
        }

    def roll_dice_and_next_round(self) -> Dict[str, Any]:
        """Settle previous round sells, roll dice, start new round."""
        if not self.is_game_active:
            return {"success": False, "error": "Game not started."}

        # Settle remaining sell orders from last round before advancing
        self._settle_round_sells()

        result = self.table.next_round()

        # AI players post buy/sell orders for the new round
        self._ai_turn()

        # Random events
        event_result = self._check_random_event()

        self.game_log.append(
            f"--- Round {result['round']} | 🎲 Dice: {result['dice']['die1']}+{result['dice']['die2']}={result['dice']['total']} ({result['condition']}) ---"
        )
        if event_result:
            self.game_log.append(f"⚡ Event: {event_result['name']} - {event_result['description']}")

        # Update dice price for this round
        if self.current_player:
            dice_total = result["dice"]["total"]
            self.current_dice_price = dice_total * self.DICE_BASE
            self.game_log.append(f"🎲 Dice: {result['dice']['die1']}+{result['dice']['die2']}={dice_total} → Your price: {self.current_dice_price:,} FCFA/unit")

        return {
            "success": True,
            "tour": result["round"],
            "dice": result["dice"],
            "dice_price": self.current_dice_price,
            "condition": result["condition"],
            "markets": [m.to_dict() for m in self.table.markets],
            "player_fortune": self.current_player.balance if self.current_player else 0,
            "player_rank": self._get_player_rank(),
            "event": event_result,
            "leaderboard": self.table.get_leaderboard(),
            "log": self._get_recent_log(10),
        }

    def post_sell_order(self, market_index: int, quantity: int) -> Dict[str, Any]:
        """Sell at your current dice price. Market auto-buys if dice_price ≤ market fixed price."""
        if not self.is_game_active:
            return {"success": False, "error": "Game not started."}
        if not self.current_player:
            return {"success": False, "error": "No active player."}
        if market_index < 0 or market_index >= len(self.table.markets):
            return {"success": False, "error": "Invalid market index."}
        if self.current_dice_price == 0:
            return {"success": False, "error": "Roll the dice first to get your price."}

        market_board = self.table.markets[market_index]
        product = market_board.product

        finished = getattr(self.current_player, 'finished_products', [])
        product_entry = next((p for p in finished if p["name"] == product), None)
        if not product_entry or product_entry["quantity"] < quantity:
            have = product_entry["quantity"] if product_entry else 0
            return {
                "success": False,
                "error": f"Not enough {product}. You have {have} units, need {quantity}.",
            }

        product_entry["quantity"] -= quantity
        if product_entry["quantity"] == 0:
            self.current_player.finished_products.remove(product_entry)

        market_board.post_sell_order(self.current_player.username, quantity, self.current_dice_price)

        fixed = market_board.market_fixed_price
        if self.current_dice_price <= fixed:
            note = f"✅ Your price ({self.current_dice_price:,}) ≤ market fixed ({fixed:,}) → will auto-sell at round end"
        else:
            note = f"⏳ Your price ({self.current_dice_price:,}) > market fixed ({fixed:,}) → only other buyers can take it"

        self.game_log.append(f"📋 Sell {quantity}x {product} @ {self.current_dice_price:,} at {market_board.location.name}. {note}")

        return {
            "success": True,
            "message": f"Listed {quantity}x {product} @ {self.current_dice_price:,} FCFA/unit. {note}",
            "player_fortune": self.current_player.balance,
            "finished_products": getattr(self.current_player, 'finished_products', []),
            "markets": [m.to_dict() for m in self.table.markets],
            "player_rank": self._get_player_rank(),
            "leaderboard": self.table.get_leaderboard(),
            "log": self._get_recent_log(10),
        }

    def post_buy_order(self, market_index: int, quantity: int) -> Dict[str, Any]:
        if not self.is_game_active:
            return {"success": False, "error": "Game not started."}
        if not self.current_player:
            return {"success": False, "error": "No active player."}
        if market_index < 0 or market_index >= len(self.table.markets):
            return {"success": False, "error": "Invalid market index."}
        if self.current_dice_price == 0:
            return {"success": False, "error": "Roll the dice first to get your price."}

        market_board = self.table.markets[market_index]
        result = market_board.execute_buy(self.current_player.username, quantity, self.current_dice_price)

        if result["success"]:
            total_cost = result["total_cost"]
            if not self.current_player.can_afford(total_cost):
                return {"success": False, "error": f"Not enough fortune. Need {total_cost:,} FCFA."}

            self.current_player.subtract_fortune(total_cost)

            # Add product to finished_products inventory
            product = market_board.product
            sell_price = market_board.market_fixed_price
            fp = getattr(self.current_player, 'finished_products', [])
            entry = next((p for p in fp if p["name"] == product), None)
            if entry:
                entry["quantity"] += result["units_bought"]
            else:
                fp.append({"id": f"bought_{product}", "name": product,
                           "quantity": result["units_bought"], "sell_price": sell_price})
            self.current_player.finished_products = fp

            # Pay sellers
            for trade in result["trades"]:
                if trade["seller"] != "market":
                    seller = self.table.get_player(trade["seller"])
                    if seller:
                        seller.add_fortune(trade["total"])

            self.game_log.append(
                f"🛍 Bought {result['units_bought']}x {product} at avg {result['avg_price']:,} FCFA "
                f"(total {total_cost:,}) at {market_board.location.name}"
            )
            msg = (f"Bought {result['units_bought']}x {product} for {total_cost:,} FCFA "
                   f"(avg {result['avg_price']:,}/unit).")
            if result["unfilled"] > 0:
                msg += f" {result['unfilled']} units unfilled."
        else:
            msg = result.get("error", "Buy failed")

        return {
            "success": result["success"],
            "message": msg,
            "player_fortune": self.current_player.balance,
            "finished_products": getattr(self.current_player, 'finished_products', []),
            "markets": [m.to_dict() for m in self.table.markets],
            "player_rank": self._get_player_rank(),
            "leaderboard": self.table.get_leaderboard(),
            "log": self._get_recent_log(10),
        }

    def _settle_round_sells(self) -> None:
        """Pay sellers whose orders were filled by market at round end."""
        for market_board in self.table.markets:
            settled = market_board.settle_remaining_sells()
            for s in settled:
                seller = self.table.get_player(s["seller"])
                if seller:
                    seller.add_fortune(s["net_revenue"])
                    self.game_log.append(
                        f"✅ Market bought {s['quantity']} units from {s['seller']} "
                        f"@ {s['price']:,} FCFA → net {s['net_revenue']:,} FCFA"
                    )
                elif s["seller"] == self.current_player.username if self.current_player else False:
                    self.current_player.add_fortune(s["net_revenue"])

    def buy_tool(self, tool_index: int) -> Dict[str, Any]:
        if not self.is_game_active:
            return {"success": False, "error": "Game not started."}
        if not self.current_player:
            return {"success": False, "error": "No active player."}

        tool_opts = get_tool_options()
        if tool_index < 0 or tool_index >= len(tool_opts):
            return {"success": False, "error": "Invalid tool index."}

        d = tool_opts[tool_index]
        tool = Tool(id=d["id"], name=d["name"], cost=d["cost"], capacity=d["capacity"])

        if not self.current_player.can_afford(tool.cost):
            return {
                "success": False,
                "error": f"Not enough balance. Need {tool.cost:,} FCFA, have {self.current_player.balance:,.0f} FCFA.",
            }

        self.current_player.subtract_fortune(tool.cost)
        self.current_player.add_tool(tool)

        self.game_log.append(f"🔧 Bought {tool.name} for {tool.cost:,} FCFA")

        return {
            "success": True,
            "message": f"Purchased {tool.name}!",
            "player_fortune": self.current_player.balance,
            "player_tools": [asdict(t) for t in self.current_player.tools],
            "player_rank": self._get_player_rank(),
            "leaderboard": self.table.get_leaderboard(),
            "log": self._get_recent_log(10),
        }

    def buy_card(self, card_index: int) -> Dict[str, Any]:
        if not self.is_game_active:
            return {"success": False, "error": "Game not started."}
        if not self.current_player:
            return {"success": False, "error": "No active player."}

        card_opts = get_card_options()
        if card_index < 0 or card_index >= len(card_opts):
            return {"success": False, "error": "Invalid card index."}

        d = card_opts[card_index]
        card = Card(id=d["id"], name=d["name"], description=d.get("description", ""), value=d["value"], price=d["price"])

        if not self.current_player.can_afford(card.price):
            return {
                "success": False,
                "error": f"Not enough balance. Need {card.price:,} FCFA, have {self.current_player.balance:,.0f} FCFA.",
            }

        self.current_player.subtract_fortune(card.price)
        self.current_player.add_card(card)

        self.game_log.append(f"🃏 Bought card {card.name} for {card.price:,} FCFA")

        return {
            "success": True,
            "message": f"Purchased card {card.name}!",
            "player_fortune": self.current_player.balance,
            "player_cards": self.current_player.cards,
            "player_rank": self._get_player_rank(),
            "leaderboard": self.table.get_leaderboard(),
            "log": self._get_recent_log(10),
        }

    def buy_raw_material(self, material_index: int, quantity: int = 1) -> Dict[str, Any]:
        """Buy raw materials for production.

        Args:
            material_index: Index of the raw material
            quantity: Number of units to buy

        Returns:
            Dict with purchase results
        """
        if not self.is_game_active:
            return {"success": False, "error": "Game not started."}
        if not self.current_player:
            return {"success": False, "error": "No active player."}
        if quantity <= 0:
            return {"success": False, "error": "Quantity must be positive."}

        if material_index < 0 or material_index >= len(RAW_MATERIALS):
            return {"success": False, "error": "Invalid material index."}

        material = RAW_MATERIALS[material_index]
        total_cost = material["price"] * quantity

        if not self.current_player.can_afford(total_cost):
            return {
                "success": False,
                "error": f"Not enough balance. Need {total_cost:,} FCFA, have {self.current_player.balance:,.0f} FCFA.",
            }

        self.current_player.subtract_fortune(total_cost)

        if not hasattr(self.current_player, 'inventory'):
            self.current_player.inventory = []

        found = False
        for item in self.current_player.inventory:
            if item["id"] == material["id"]:
                item["quantity"] += quantity
                found = True
                break

        if not found:
            self.current_player.inventory.append({
                "id": material["id"],
                "name": material["name"],
                "quantity": quantity,
                "yield": material["yield"],
            })

        self.game_log.append(f"📦 Bought {quantity}x {material['name']} for {total_cost:,} FCFA")

        return {
            "success": True,
            "message": f"Purchased {quantity}x {material['name']}!",
            "player_fortune": self.current_player.balance,
            "inventory": self.current_player.inventory,
            "player_rank": self._get_player_rank(),
            "leaderboard": self.table.get_leaderboard(),
            "log": self._get_recent_log(10),
        }

    def produce_goods(self, product_index: int, quantity: int = 1) -> Dict[str, Any]:
        """Produce finished goods from raw materials.

        Args:
            product_index: Index of the finished product
            quantity: Number of units to produce

        Returns:
            Dict with production results
        """
        if not self.is_game_active:
            return {"success": False, "error": "Game not started."}
        if not self.current_player:
            return {"success": False, "error": "No active player."}
        if quantity <= 0:
            return {"success": False, "error": "Quantity must be positive."}

        if product_index < 0 or product_index >= len(FINISHED_PRODUCTS):
            return {"success": False, "error": "Invalid product index."}

        product = FINISHED_PRODUCTS[product_index]
        required_material = product["raw_material"]
        product_yield = None

        for mat in RAW_MATERIALS:
            if mat["name"] == required_material:
                product_yield = mat["yield"]
                break

        if product_yield is None:
            return {"success": False, "error": f"Could not find raw material for {product['name']}."}

        if not hasattr(self.current_player, 'inventory'):
            self.current_player.inventory = []

        material_qty = 0
        for item in self.current_player.inventory:
            if item["name"] == required_material:
                material_qty = item["quantity"]
                break

        if material_qty < quantity:
            return {
                "success": False,
                "error": f"Not enough {required_material}. Have {material_qty}, need {quantity}.",
            }

        for item in self.current_player.inventory:
            if item["name"] == required_material:
                item["quantity"] -= quantity
                if item["quantity"] <= 0:
                    self.current_player.inventory.remove(item)
                break

        if not hasattr(self.current_player, 'finished_products'):
            self.current_player.finished_products = []

        found = False
        for item in self.current_player.finished_products:
            if item["id"] == product["id"]:
                item["quantity"] += quantity
                found = True
                break

        if not found:
            self.current_player.finished_products.append({
                "id": product["id"],
                "name": product["name"],
                "quantity": quantity,
                "sell_price": product["sell_price"],
            })

        self.game_log.append(f"🏭 Produced {quantity}x {product['name']} from {quantity}x {required_material}")

        return {
            "success": True,
            "message": f"Produced {quantity}x {product['name']}!",
            "player_fortune": self.current_player.balance,
            "inventory": self.current_player.inventory,
            "finished_products": self.current_player.finished_products,
            "player_rank": self._get_player_rank(),
            "leaderboard": self.table.get_leaderboard(),
            "log": self._get_recent_log(10),
        }

    def sell_finished_product(self, market_index: int, product_index: int, quantity: int) -> Dict[str, Any]:
        """Sell finished products at a market.

        Args:
            market_index: Index of the market (0-based)
            product_index: Index of the finished product in player's inventory
            quantity: Number of units to sell

        Returns:
            Dict with sale results
        """
        if not self.is_game_active:
            return {"success": False, "error": "Game not started."}
        if not self.current_player:
            return {"success": False, "error": "No active player."}
        if market_index < 0 or market_index >= len(self.table.markets):
            return {"success": False, "error": "Invalid market index."}
        if product_index < 0 or product_index >= len(self.current_player.finished_products):
            return {"success": False, "error": "Invalid product index."}

        market_board = self.table.markets[market_index]
        product = self.current_player.finished_products[product_index]

        if quantity > product["quantity"]:
            return {"success": False, "error": f"Not enough {product['name']}. Have {product['quantity']}, want to sell {quantity}."}

        base_price = product["sell_price"]
        revenue = base_price * quantity
        tax = int(revenue * market_board.location.tax_rate)
        net_revenue = revenue - tax

        # Update market demand
        sale_result = market_board.sell(quantity, self.current_player.username)
        if not sale_result["success"]:
            return {"success": False, "error": sale_result["error"]}

        self.current_player.add_fortune(net_revenue)

        product["quantity"] -= quantity
        if product["quantity"] <= 0:
            self.current_player.finished_products.remove(product)

        self.game_log.append(
            f"💰 Sold {quantity}x {product['name']} at {market_board.location.name} for {net_revenue:,.0f} FCFA (tax: {tax:,})"
        )

        return {
            "success": True,
            "message": f"Sold {quantity}x {product['name']} for {net_revenue:,.0f} FCFA!",
            "sale_result": {**sale_result, "revenue": revenue, "tax": tax, "net_revenue": net_revenue},
            "player_fortune": self.current_player.balance,
            "finished_products": self.current_player.finished_products,
            "markets": [m.to_dict() for m in self.table.markets],
            "leaderboard": self.table.get_leaderboard(),
            "log": self._get_recent_log(10),
        }

    def end_game(self) -> Dict[str, Any]:
        """End the current game.

        Returns:
            Dict with final results
        """
        if not self.is_game_active:
            return {"success": False, "error": "Game not started."}

        result = self.table.end_game()
        self.is_game_active = False

        if result["winner"]:
            self.game_log.append(f"🏆 Game over! Winner: {result['winner']['username']} with {result['winner']['balance']:,.0f} FCFA!")
        else:
            self.game_log.append("Game over! No players remaining.")

        return {
            "success": True,
            "message": "Game over!",
            "final_results": result,
            "log": self._get_recent_log(20),
        }

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools for purchase."""
        return get_tool_options()

    def get_available_cards(self) -> List[Dict[str, Any]]:
        """Get list of available cards for purchase."""
        return get_card_options()

    def get_available_locations(self) -> List[Dict[str, Any]]:
        """Get list of available sales locations."""
        return get_market_location_options()

    def get_raw_materials(self) -> List[Dict[str, Any]]:
        """Get list of available raw materials."""
        return RAW_MATERIALS

    def get_finished_products(self) -> List[Dict[str, Any]]:
        """Get list of available finished products."""
        return FINISHED_PRODUCTS

    def get_player_status(self) -> Dict[str, Any]:
        """Get current player status."""
        if not self.current_player:
            return {"error": "No active player."}

        inventory = getattr(self.current_player, 'inventory', [])
        finished = getattr(self.current_player, 'finished_products', [])

        return {
            "username": self.current_player.username,
            "balance": self.current_player.balance,
            "basic_stock": getattr(self.current_player, 'basic_stock', 0),
            "stars": self.current_player.star_count,
            "competitions": self.current_player.competition_count,
            "followers": self.current_player.follower_count,
            "cards": self.current_player.cards,
            "tools": [asdict(t) for t in self.current_player.tools],
            "total_capacity": self.current_player.get_total_capacity(),
            "rank": self._get_player_rank(),
            "inventory": getattr(self.current_player, 'inventory', []),
            "finished_products": getattr(self.current_player, 'finished_products', []),
        }

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Get current leaderboard."""
        return self.table.get_leaderboard()

    def get_game_log(self) -> List[str]:
        """Get full game log."""
        return self.game_log.copy()

    def get_events_log(self) -> List[Dict[str, Any]]:
        """Get events log."""
        return self.events_log.copy()

    def _get_player_rank(self) -> int:
        """Get current player's rank."""
        if not self.current_player:
            return -1
        leaderboard = self.table.get_leaderboard()
        for i, entry in enumerate(leaderboard):
            if entry["username"] == self.current_player.username:
                return i + 1
        return -1

    def _ai_turn(self) -> None:
        """Simulate AI players posting buy or sell orders for their products."""
        for player in self.table.players:
            if player.username == (self.current_player.username if self.current_player else ""):
                continue
            if not self.table.markets:
                continue
            ai_dice = random.randint(2, 12)
            ai_price = ai_dice * self.DICE_BASE

            if not hasattr(player, 'finished_products'):
                player.finished_products = []
            if not player.finished_products:
                products = ["Fufu", "Cooked Rice", "Corn Flour", "Peanut Butter", "Smoked Fish"]
                player.finished_products = [
                    {"id": f"ai_{p}", "name": p, "quantity": random.randint(5, 30), "sell_price": 1000}
                    for p in random.sample(products, k=random.randint(1, 3))
                ]

            action = random.choice(["sell", "sell", "buy", "nothing"])

            if action == "sell":
                for market_board in random.sample(self.table.markets, len(self.table.markets)):
                    prod_entry = next((p for p in player.finished_products if p["name"] == market_board.product), None)
                    if prod_entry and prod_entry["quantity"] > 0:
                        qty = random.randint(1, min(15, prod_entry["quantity"]))
                        market_board.post_sell_order(player.username, qty, ai_price)
                        prod_entry["quantity"] -= qty
                        self.game_log.append(
                            f"  🤖 {player.username} lists {qty}x {market_board.product} @ {ai_price:,} at {market_board.location.name}"
                        )
                        break
            elif action == "buy" and player.balance >= 1000:
                market_board = random.choice(self.table.markets)
                qty = random.randint(1, 10)
                result = market_board.execute_buy(player.username, qty, ai_price)
                if result["success"]:
                    player.subtract_fortune(result["total_cost"])
                    prod_entry = next((p for p in player.finished_products if p["name"] == market_board.product), None)
                    if prod_entry:
                        prod_entry["quantity"] += result["units_bought"]
                    else:
                        player.finished_products.append({
                            "id": f"ai_{market_board.product}", "name": market_board.product,
                            "quantity": result["units_bought"], "sell_price": market_board.market_fixed_price
                        })

    def _check_random_event(self) -> Optional[Dict[str, Any]]:
        """Check for random events that can affect the player.

        Returns:
            Event dict if an event occurred, None otherwise
        """
        if not self.current_player or not self.is_game_active:
            return None

        # Weighted random selection of events
        events = RANDOM_EVENTS
        weights = [e["probability"] for e in events]

        # Check if any event triggers
        triggered_events = []
        for event in events:
            if random.random() < event["probability"]:
                triggered_events.append(event)

        if not triggered_events:
            return None

        event = random.choice(triggered_events)
        amount = random.randint(event["min"], event["max"])

        if event["effect"] == "gain":
            self.current_player.add_fortune(amount)
            self.game_log.append(f"  ✨ +{amount:,} FCFA from {event['name']}")
        else:
            self.current_player.subtract_fortune(amount)
            self.game_log.append(f"  💔 -{amount:,} FCFA from {event['name']}")

        self.events_log.append({
            "round": self.table.current_round,
            "event": event,
            "amount": amount,
            "effect": event["effect"],
        })

        return {
            "name": event["name"],
            "description": event["description"],
            "effect": event["effect"],
            "amount": amount,
        }

    def _get_recent_log(self, n: int) -> List[str]:
        """Get the last n log entries."""
        return self.game_log[-n:]
