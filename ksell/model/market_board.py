"""MarketBoard model for KSell Entreprise.

Each market:
- Buys ONE specific product (e.g. Central Market buys Cooked Rice)
- Has a FIXED price it pays per unit (e.g. 2,000 FCFA for Cooked Rice)

Each round, dice determines the PLAYER'S price:
  dice_price = dice_total × DICE_BASE  (e.g. dice 7 → 1,400 FCFA)

SELL: player lists at dice_price.
  Market auto-buys if dice_price ≤ market_fixed_price.
  Other players can buy if their dice_price ≥ this order's price.

BUY: player buys at dice_price.
  Cheapest sell orders first; then from market supply if market_fixed_price ≤ dice_price.
"""

import random
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from ksell.model.dice import Dice
from ksell.pojo.market import Market

DICE_BASE = (
    100  # FCFA per dice point  (dice range 2-12 → price range 200-1200 FCFA/unit)
)

ENTRY_FEE_DIVISOR = 10  # entry fee = floor(total_qty / 10) * 10


class MarketBoard:
    """A market location with a fixed product price and an order book."""

    def __init__(
        self,
        location: Optional[Market] = None,
        dice: Optional[Dice] = None,
    ):
        self.location = location or Market()
        self.dice = dice or Dice.shake()

        self.market_fixed_price: int = self.location.fixed_price
        self.product: str = self.location.product
        self.last_purchase_price: Optional[int] = (
            None  # Price market paid when buying full capacity
        )
        self.pending_market_purchase: Optional[Dict[str, Any]] = (
            None  # Purchase to execute at end of round
        )

        self._init_round()
        self.passing_players: List[str] = []

    @property
    def sell_entry_fee(self) -> int:
        """Fixed entry fee for selling in this market, based on market potential (size).

        Independent of tax rate, market price, or quantity sold.
        Larger markets charge more to enter.
        """
        return (self.total_qty // ENTRY_FEE_DIVISOR) * 10

    def _init_round(self) -> None:
        self.market_supply: int = random.randint(
            self.location.min_qty, self.location.max_qty
        )
        self.sell_orders: List[Dict[str, Any]] = []
        self.completed_trades: List[Dict[str, Any]] = []
        self.selling_players: List[str] = []
        self.total_qty = self.market_supply
        self.remaining_qty = self.market_supply
        self.pending_market_purchase = None  # Clear pending purchase

        # Update market's fixed price if market made a purchase last round
        if self.last_purchase_price is not None:
            self.market_fixed_price = self.last_purchase_price
            self.last_purchase_price = None

    # ------------------------------------------------------------------
    # Order book
    # ------------------------------------------------------------------

    def post_sell_order(
        self, username: str, quantity: int, dice_price: int
    ) -> Dict[str, Any]:
        if quantity <= 0:
            return {"success": False, "error": "Quantity must be positive"}
        self.sell_orders.append(
            {
                "username": username,
                "quantity": quantity,
                "remaining": quantity,
                "price": dice_price,
            }
        )
        self.sell_orders.sort(key=lambda x: x["price"])
        return {"success": True}

    def execute_buy(
        self, username: str, quantity: int, dice_price: int
    ) -> Dict[str, Any]:
        if quantity <= 0:
            return {"success": False, "error": "Quantity must be positive"}

        remaining = quantity
        total_cost = 0
        units_bought = 0
        trades: List[Dict[str, Any]] = []

        for order in self.sell_orders:
            if remaining <= 0:
                break
            if order["price"] > dice_price:
                break
            if order["username"] == username:
                continue
            buy_qty = min(remaining, order["remaining"])
            cost = buy_qty * order["price"]
            order["remaining"] -= buy_qty
            remaining -= buy_qty
            total_cost += cost
            units_bought += buy_qty
            trades.append(
                {
                    "buyer": username,
                    "seller": order["username"],
                    "quantity": buy_qty,
                    "price": order["price"],
                    "total": cost,
                }
            )

        if (
            remaining > 0
            and self.market_supply > 0
            and self.market_fixed_price <= dice_price
        ):
            buy_qty = min(remaining, self.market_supply)
            cost = buy_qty * self.market_fixed_price
            self.market_supply -= buy_qty
            self.remaining_qty = self.market_supply
            remaining -= buy_qty
            total_cost += cost
            units_bought += buy_qty
            trades.append(
                {
                    "buyer": username,
                    "seller": "market",
                    "quantity": buy_qty,
                    "price": self.market_fixed_price,
                    "total": cost,
                }
            )

        self.sell_orders = [o for o in self.sell_orders if o["remaining"] > 0]
        self.completed_trades.extend(trades)

        if units_bought == 0:
            return {
                "success": False,
                "error": f"No stock available at your dice price ({dice_price:,} FCFA)",
            }

        avg = round(total_cost / units_bought)

        # Calculate buy tax
        buy_tax = round(total_cost * self.location.tax_rate, 2)
        total_with_tax = total_cost + buy_tax

        return {
            "success": True,
            "units_bought": units_bought,
            "unfilled": remaining,
            "total_cost": total_cost,
            "buy_tax": buy_tax,
            "total_with_tax": total_with_tax,
            "tax_rate": self.location.tax_rate,
            "avg_price": avg,
            "trades": trades,
            "product": self.product,
        }

    def handle_sell_order(
        self, seller_username: str, quantity: int, dice_price: int
    ) -> Dict[str, Any]:
        """Handle sell order placement.

        When market is full: Store purchase as PENDING (will execute at end of round).
          - Market buys at SELLER'S dice price (not market's fixed price)
          - Limited to market's base capacity (max_qty)
          - Seller's dice price becomes market's new fixed_price for next round
          - Seller gets paid and removes inventory immediately

        When market has capacity: Add to order book at seller's dice price.

        Returns dict with tax amount and transaction details.
        """
        remaining_capacity = self.remaining_qty

        # Market is full: STORE purchase as pending (execute at end of round)
        if remaining_capacity <= 0:
            # Market will buy from this seller only, up to its max capacity
            buy_qty = min(quantity, self.location.max_qty)
            listing_price = (
                dice_price  # Seller's dice price (market buys at seller's price)
            )

            # Tax on the amount seller listed (not what market bought, what seller offered)
            tax_amount = quantity * listing_price * self.location.tax_rate

            # Store as pending purchase (will be executed at end of round)
            self.pending_market_purchase = {
                "seller_username": seller_username,
                "quantity": buy_qty,
                "purchase_price": listing_price,
                "quantity_listed": quantity,  # For tax calculation
            }

            return {
                "success": True,
                "mode": "market_purchase",
                "quantity_purchased": buy_qty,
                "purchase_price": listing_price,
                "tax_amount": tax_amount,
                "product": self.product,
                "market_name": self.location.name,
            }

        # Market has capacity: List to order book at seller's dice price
        listing_price = dice_price
        tax_amount = quantity * listing_price * self.location.tax_rate

        result = self.post_sell_order(seller_username, quantity, listing_price)

        if result["success"]:
            return {
                "success": True,
                "mode": "order_book",
                "quantity_listed": quantity,
                "listing_price": listing_price,
                "tax_amount": tax_amount,
                "product": self.product,
                "market_name": self.location.name,
            }

        return {
            "success": False,
            "error": "Failed to post sell order",
        }

    def settle_remaining_sells(self) -> List[Dict[str, Any]]:
        settled = []
        for order in self.sell_orders:
            if order["price"] <= self.market_fixed_price and order["remaining"] > 0:
                qty = order["remaining"]
                revenue = qty * order["price"]
                tax = int(revenue * self.location.tax_rate)
                settled.append(
                    {
                        "seller": order["username"],
                        "quantity": qty,
                        "price": order["price"],
                        "revenue": revenue,
                        "tax": tax,
                        "net_revenue": revenue - tax,
                        "product": self.product,
                    }
                )
                order["remaining"] = 0
        self.sell_orders = [o for o in self.sell_orders if o["remaining"] > 0]
        return settled

    def execute_pending_market_purchase(self) -> Optional[Dict[str, Any]]:
        """Execute pending market purchase at END OF ROUND.

        Market takes the products and adds them to inventory for next round.
        Returns purchase details for confirmation message, or None if no pending purchase.
        """
        if not self.pending_market_purchase:
            return None

        purchase = self.pending_market_purchase

        # Add purchased units to market inventory
        self.market_supply += purchase["quantity"]
        self.remaining_qty = self.market_supply

        # Store new price for next round
        self.last_purchase_price = purchase["purchase_price"]

        return purchase

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def add_passing_player(self, username: str) -> bool:
        if username not in self.passing_players:
            self.passing_players.append(username)
            return True
        return False

    def get_market_display_info(self, buyer_max_price: int) -> Dict[str, Any]:
        """Get formatted market info for buyer display."""
        affordable_orders = [
            o for o in self.sell_orders if o["price"] <= buyer_max_price
        ]
        market_can_supply = (
            self.market_supply > 0 and self.market_fixed_price <= buyer_max_price
        )

        cheapest_seller_price = (
            min([o["price"] for o in affordable_orders], default=None)
            if affordable_orders
            else None
        )
        cheapest_market_price = self.market_fixed_price if market_can_supply else None
        cheapest_available = min(
            filter(None, [cheapest_seller_price, cheapest_market_price]), default=None
        )

        sell_orders_info = ""
        if affordable_orders:
            total_units = sum(o["remaining"] for o in affordable_orders)
            sell_orders_info = f"Sell Orders (within budget): {len(affordable_orders)} orders ({total_units} units) - cheapest: {cheapest_seller_price} FCFA/unit"
        else:
            cheapest_in_market = (
                min([o["price"] for o in self.sell_orders], default=None)
                if self.sell_orders
                else None
            )
            if cheapest_in_market and cheapest_in_market > buyer_max_price:
                sell_orders_info = f"✗ Sell Orders: {len(self.sell_orders)} orders but cheapest is {cheapest_in_market} FCFA (exceeds your limit of {buyer_max_price})"
            else:
                total_units = sum(o["remaining"] for o in self.sell_orders)
                sell_orders_info = f"Sell Orders: {len(self.sell_orders)} orders ({total_units} units total)"

        market_supply_info = ""
        if market_can_supply:
            market_supply_info = f"Market Supply: {self.market_supply} units at {self.market_fixed_price} FCFA/unit"

        return {
            "market_name": self.location.name,
            "product": self.location.product,
            "market_price": self.market_fixed_price,
            "tax_rate": self.location.tax_rate,
            "capacity": self.remaining_qty,
            "total_qty": self.total_qty,
            "sell_orders_info": sell_orders_info,
            "market_supply_info": market_supply_info,
            "cheapest_available": cheapest_available,
            "has_affordable": bool(affordable_orders or market_can_supply),
        }

    def refresh(self, dice: Optional[Dice] = None) -> None:
        self.dice = dice or Dice.shake()
        self._init_round()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product": self.product,
            "market_fixed_price": self.market_fixed_price,
            "market_supply": self.market_supply,
            "total_qty": self.total_qty,
            "remaining_qty": self.market_supply,
            "location": asdict(self.location),
            "sell_orders": [
                {
                    "username": o["username"],
                    "quantity": o["quantity"],
                    "remaining": o["remaining"],
                    "price": o["price"],
                }
                for o in self.sell_orders
            ],
            "passing_players": self.passing_players,
            "selling_players": self.selling_players,
            "last_purchase_price": self.last_purchase_price,
            "pending_market_purchase": self.pending_market_purchase,
            "completed_trades": self.completed_trades,
            "dice": self.dice.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketBoard":
        """Deserialize market board from dictionary."""
        from ksell.model.dice import Dice
        from ksell.pojo.market import Market

        location = Market.from_dict(data["location"])
        dice = Dice.from_dict(data["dice"])
        mb = cls(location=location, dice=dice)
        mb.market_fixed_price = data["market_fixed_price"]
        mb.product = data["product"]
        mb.market_supply = data["market_supply"]
        mb.total_qty = data["total_qty"]
        mb.remaining_qty = data.get("remaining_qty", data["market_supply"])
        mb.passing_players = data.get("passing_players", [])
        mb.selling_players = data.get("selling_players", [])
        mb.last_purchase_price = data.get("last_purchase_price")
        mb.pending_market_purchase = data.get("pending_market_purchase")
        mb.sell_orders = data.get("sell_orders", [])
        mb.completed_trades = data.get("completed_trades", [])
        return mb

    def __repr__(self) -> str:
        return f"MarketBoard({self.location.name!r}, product={self.product!r}, fixed={self.market_fixed_price})"
