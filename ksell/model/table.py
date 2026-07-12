"""Table model for KSell Entreprise.

Represents the game table that holds all active players and markets.
"""

import random
from typing import Any, Dict, List, Optional

from ksell.model.dice import Dice
from ksell.model.player import Player
from ksell.model.market_board import MarketBoard, DICE_BASE
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
        """Generate random markets with random products and specifications.

        Each product can appear in multiple markets at different prices,
        enabling buy-low-sell-high strategies.
        """
        self.dice.shake()
        self.markets.clear()

        # Available products for the game
        product_names = [
            "Cooked Rice",
            "Fufu",
            "Corn Flour",
            "Peanut Butter",
            "Smoked Fish",
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

        # Shuffle market names
        shuffled_names = market_names.copy()
        random.shuffle(shuffled_names)

        # Each product appears in 1-3 markets (at different prices)
        markets_per_product = random.randint(1, 3)
        market_idx = 0

        for product_name in product_names:
            num_appearances = random.randint(1, markets_per_product)

            for _ in range(num_appearances):
                if market_idx >= len(shuffled_names):
                    break

                max_qty = random.randint(50, 150)
                min_qty = random.randint(10, max_qty)

                market = Market(
                    id=f"market_{market_idx}",
                    name=shuffled_names[market_idx],
                    min_qty=min_qty,
                    max_qty=max_qty,
                    tax_rate=round(random.uniform(0.01, 0.10), 2),
                    product=product_name,
                    fixed_price=(random.randint(1, 6) + random.randint(1, 6)) * 100,  # 200-1200 FCFA
                )
                market_board = MarketBoard(location=market, dice=self.dice)
                self.markets.append(market_board)
                market_idx += 1

        return self.markets

    def initialize_player_inventory(
        self, units_per_player: int = 20
    ) -> Dict[str, List[str]]:
        """Initialize each player with random starting products.

        Args:
            units_per_player: Total units to distribute per player (default 20)

        Returns:
            Dictionary mapping player username to their starting inventory strings
        """
        available_products = list(
            set([market.location.product for market in self.markets])
        )
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

            inventory_str = ", ".join(
                [f"{item.product.name}: {item.quantity}" for item in player.inventory]
            )
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

    def max_buyable_qty(self, dice_total: int, market: MarketBoard) -> int:
        """Calculate the maximum quantity a player can buy based on dice roll.

        Uses dice_total / 12 as the ratio of the market's **initial size**
        (total_qty), not the remaining stock. This ensures players can always
        finish off a depleted market rather than being locked out.

        Args:
            dice_total: The player's dice roll total (2-12).
            market: The market board to calculate against.

        Returns:
            Maximum units allowed by the dice roll (caller should cap
            against actual available stock and player balance).
        """
        dice_ratio = dice_total / 12
        return max(0, int(market.total_qty * dice_ratio))

    def force_sell_for_tax(
        self, player: Player, market: MarketBoard, tax_needed: float
    ) -> Optional[Dict[str, Any]]:
        """Force the market to buy player's inventory at half price to cover tax costs.

        When a player has insufficient balance to pay market tax but owns the
        market's product, the market forcibly purchases enough units at half
        the fixed price to cover the tax amount. This keeps the player in the game.

        Args:
            player: The player who needs cash to pay tax.
            market: The market the player wants to sell in.
            tax_needed: The tax amount the player cannot cover.

        Returns:
            Dict with force sale details if successful, None if not possible.
        """
        product_name = market.location.product
        player_qty = player.get_inventory_quantity(product_name)

        if player_qty <= 0:
            return None

        half_price = market.market_fixed_price / 2
        units_needed = int(-(-tax_needed // half_price))  # ceiling division
        units_to_sell = min(units_needed, player_qty)
        cash_generated = units_to_sell * half_price

        # Execute the force sale
        player.remove_from_inventory(product_name, units_to_sell)
        player.balance += cash_generated

        return {
            "units_sold": units_to_sell,
            "price_per_unit": half_price,
            "cash_generated": cash_generated,
            "product": product_name,
            "market_name": market.location.name,
        }

    # ------------------------------------------------------------------
    # Round orchestration
    # ------------------------------------------------------------------

    def start_round(self, num_markets: int) -> List[MarketBoard]:
        """Start a new round: select random markets and initialize their state.

        Args:
            num_markets: Number of markets to activate this round.

        Returns:
            List of active MarketBoard instances for this round.
        """
        import random as _random

        self.current_round += 1
        chosen = _random.sample(self.markets, num_markets)

        for market in chosen:
            if market.last_purchase_price is not None:
                market.market_fixed_price = market.last_purchase_price
                market.last_purchase_price = None
            market.sell_orders = []
            market.completed_trades = []
            market.total_qty = market.remaining_qty

        return chosen

    def end_round(self, markets: List[MarketBoard]) -> List[Dict[str, Any]]:
        """Execute pending market purchases at end of round.

        Args:
            markets: Active markets for this round.

        Returns:
            List of purchase detail dicts for display.
        """
        purchases = []
        for market in markets:
            purchase = market.execute_pending_market_purchase()
            if purchase:
                purchases.append(purchase)
        return purchases

    # ------------------------------------------------------------------
    # Decision helpers
    # ------------------------------------------------------------------

    def roll_dice_for_player(self) -> int:
        """Roll dice and return the total (2-12)."""
        self.dice.shake()
        return self.dice.total()

    def determine_forced_decision(
        self, player: Player, markets: List[MarketBoard]
    ) -> str:
        """Determine forced action for a zero-balance player.

        Returns:
            'sell' if player has matching products, 'skip' otherwise.
        """
        available_products = [m.location.product for m in markets]
        has_matching = any(
            player.get_inventory_quantity(prod) > 0 for prod in available_products
        )
        return "sell" if has_matching else "skip"

    def get_forced_sell_market(
        self, player: Player, markets: List[MarketBoard]
    ) -> Optional[MarketBoard]:
        """Find the market where the player has the MOST matching inventory.

        Returns:
            The best MarketBoard, or None if no matching product found.
        """
        best_market = None
        best_qty = 0
        for market in markets:
            qty = player.get_inventory_quantity(market.location.product)
            if qty > best_qty:
                best_qty = qty
                best_market = market
        return best_market if best_market and best_qty > 0 else None

    # ------------------------------------------------------------------
    # New game mechanics - per-market strategy
    # ------------------------------------------------------------------

    def determine_turn_order(self) -> List[Player]:
        """Roll dice for each player and return players sorted by dice (highest first).

        Returns:
            List of (player, dice_total) tuples sorted by dice descending.
        """
        rolls: List[tuple] = []
        for player in self.players:
            dice_total = self.roll_dice_for_player()
            rolls.append((player, dice_total))
        return sorted(rolls, key=lambda x: x[1], reverse=True)

    def process_market_action_buy(
        self, buyer: Player, market: MarketBoard, dice_total: int
    ) -> Dict[str, Any]:
        """Process a buy action with new mechanics.

        Buy condition: dice_price > market_price → buy at market price.
        Quantity: ask player how many (capped by balance, dice ratio, available supply).

        Args:
            buyer: The player buying.
            market: The target market.
            dice_total: Player's dice roll for this market.

        Returns:
            Dict with result details for display.
        """
        dice_price = dice_total * DICE_BASE
        market_price = market.market_fixed_price

        if dice_price <= market_price:
            return {
                "success": False,
                "error": f"Your dice price ({dice_price} FCFA) is not greater than market price ({market_price} FCFA). Buy failed.",
                "dice_price": dice_price,
                "market_price": market_price,
            }

        # Calculate max buyable quantity
        max_by_dice = self.max_buyable_qty(dice_total, market)

        # Available supply at market price
        available_supply = market.market_supply
        affordable_sell_orders = [
            o for o in market.sell_orders if o["price"] <= market_price
        ]
        available_from_orders = sum(o["remaining"] for o in affordable_sell_orders)
        total_available = available_supply + available_from_orders

        if total_available <= 0:
            return {
                "success": False,
                "error": f"No supply available at market price ({market_price} FCFA).",
                "dice_price": dice_price,
                "market_price": market_price,
            }

        # Max affordable by balance (buy at market price + tax)
        tax_rate = market.location.tax_rate
        effective_price = market_price * (1 + tax_rate)
        max_by_balance = int(buyer.balance // effective_price) if effective_price > 0 else 0

        max_affordable = min(max_by_dice, total_available, max_by_balance)

        if max_affordable <= 0:
            return {
                "success": False,
                "error": f"Cannot buy (balance or dice limit). Max affordable: {max_affordable}.",
                "dice_price": dice_price,
                "market_price": market_price,
            }

        return {
            "success": True,
            "can_buy": True,
            "dice_price": dice_price,
            "market_price": market_price,
            "max_affordable": max_affordable,
            "total_available": total_available,
            "buyer": buyer,
            "market": market,
            "dice_total": dice_total,
        }

    def execute_buy_at_market_price(
        self, buyer: Player, market: MarketBoard, quantity: int
    ) -> Dict[str, Any]:
        """Execute a buy at the market's fixed price (not dice price).

        Buys from sell orders first (cheapest first, up to market price),
        then from market supply at market price.

        Args:
            buyer: The player buying.
            market: The target market.
            quantity: Units to buy.

        Returns:
            Dict with result details for display.
        """
        market_price = market.market_fixed_price
        tax_rate = market.location.tax_rate

        remaining = quantity
        total_cost = 0
        units_bought = 0
        trades: List[Dict[str, Any]] = []

        # Buy from sell orders first (cheapest, up to market price)
        for order in market.sell_orders:
            if remaining <= 0:
                break
            if order["price"] > market_price:
                break
            if order["username"] == buyer.username:
                continue
            buy_qty = min(remaining, order["remaining"])
            cost = buy_qty * order["price"]
            order["remaining"] -= buy_qty
            remaining -= buy_qty
            total_cost += cost
            units_bought += buy_qty
            trades.append({
                "buyer": buyer.username,
                "seller": order["username"],
                "quantity": buy_qty,
                "price": order["price"],
                "total": cost,
            })

        # Then from market supply
        if remaining > 0 and market.market_supply > 0:
            buy_qty = min(remaining, market.market_supply)
            cost = buy_qty * market_price
            market.market_supply -= buy_qty
            market.remaining_qty = market.market_supply
            remaining -= buy_qty
            total_cost += cost
            units_bought += buy_qty
            trades.append({
                "buyer": buyer.username,
                "seller": "market",
                "quantity": buy_qty,
                "price": market_price,
                "total": cost,
            })

        market.sell_orders = [o for o in market.sell_orders if o["remaining"] > 0]
        market.completed_trades.extend(trades)

        if units_bought == 0:
            return {"success": False, "error": "No stock available at market price"}

        avg = round(total_cost / units_bought)

        # Calculate buy tax
        buy_tax = round(total_cost * tax_rate, 2)
        total_with_tax = total_cost + buy_tax

        # Deduct from buyer
        buyer.balance -= total_with_tax

        # Add to inventory
        product = Product(name=market.location.product, price=avg)
        buyer.add_to_inventory(product, units_bought)

        # Pay sellers (not market)
        for trade in trades:
            if trade["seller"] != "market":
                seller_player = self.get_player(trade["seller"])
                if seller_player:
                    seller_player.balance += trade["total"]

        return {
            "success": True,
            "units_bought": units_bought,
            "unfilled": remaining,
            "total_cost": total_cost,
            "buy_tax": buy_tax,
            "total_with_tax": total_with_tax,
            "tax_rate": tax_rate,
            "avg_price": avg,
            "trades": trades,
            "product": market.location.product,
            "buyer_balance": buyer.balance,
        }

    def process_market_action_sell(
        self, seller: Player, market: MarketBoard, dice_total: int
    ) -> Dict[str, Any]:
        """Process a sell action with new mechanics.

        Sell condition: dice_price < market_price → market auto-buys at dice price.
        No capacity check needed - market buys immediately.

        Args:
            seller: The player selling.
            market: The target market.
            dice_total: Player's dice roll for this market.

        Returns:
            Dict with result details for display.
        """
        dice_price = dice_total * DICE_BASE
        market_price = market.market_fixed_price

        if dice_price >= market_price:
            return {
                "success": False,
                "error": f"Your dice price ({dice_price} FCFA) is not lower than market price ({market_price} FCFA). Sell failed.",
                "dice_price": dice_price,
                "market_price": market_price,
            }

        product_name = market.location.product
        seller_qty = seller.get_inventory_quantity(product_name)

        if seller_qty <= 0:
            return {
                "success": False,
                "error": f"You don't have any {product_name} to sell.",
                "dice_price": dice_price,
                "market_price": market_price,
            }

        return {
            "success": True,
            "can_sell": True,
            "dice_price": dice_price,
            "market_price": market_price,
            "seller_qty": seller_qty,
            "seller": seller,
            "market": market,
            "product_name": product_name,
        }

    def execute_market_auto_buy(
        self, seller: Player, market: MarketBoard, quantity: int, dice_price: int
    ) -> Dict[str, Any]:
        """Execute market auto-buy at dice price (sell condition met).

        The market immediately buys the player's products at the dice price.
        No order book, no capacity check - direct transaction.

        Args:
            seller: The player selling.
            market: The target market.
            quantity: Units to sell.
            dice_price: The price per unit (dice_total * DICE_BASE).

        Returns:
            Dict with result details for display.
        """
        product_name = market.location.product
        tax_rate = market.location.tax_rate

        # Revenue for seller (before tax)
        revenue = quantity * dice_price
        tax_amount = round(revenue * tax_rate, 2)
        net_revenue = revenue - tax_amount

        # Execute transaction
        seller.balance -= tax_amount
        seller.balance += net_revenue
        seller.remove_from_inventory(product_name, quantity)

        # Market absorbs the products (adds to supply for next round)
        market.market_supply += quantity
        market.remaining_qty = market.market_supply

        # Record trade
        trade = {
            "buyer": "market",
            "seller": seller.username,
            "quantity": quantity,
            "price": dice_price,
            "total": revenue,
        }
        market.completed_trades.append(trade)

        return {
            "success": True,
            "quantity_sold": quantity,
            "price_per_unit": dice_price,
            "revenue": revenue,
            "tax_amount": tax_amount,
            "net_revenue": net_revenue,
            "product": product_name,
            "seller_balance": seller.balance,
            "market_name": market.location.name,
        }
