"""Buyam-Sellam — automated simulation.

Identical to game.py but with random decisions instead of user input.
Use this to test the full game flow without manual interaction.
"""

import random

from ksell.model.player import Player
from ksell.model.table import Table
from ksell.utils.random_utils import uniform_int_range
from ksell.pojo.user import User

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

print("""
Welcome to Buyam-Sellam App

Configure players and start the game!
""")

n_players = int(input("Enter number of players: ").strip() or "3")
if n_players < 2:
    print("At least 2 players are required to start the game.")
    exit()

users = []
for i in range(n_players):
    users.append(User(username=f"Player_{i + 1}"))

starting_balance = float(input("Enter starting balance for each player: ").strip() or "5000")
players = [Player(user=u) for u in users]
for p in players:
    p.balance = starting_balance

n_rounds = int(input("Enter number of rounds for the game: ").strip() or "5")

table = Table(players=players, total_rounds=n_rounds)
table.generate_markets()

print("\nInitializing starting inventory for each player...")
for username, inv_str in table.initialize_player_inventory(units_per_player=20).items():
    print(f"  {username}: {inv_str}")

STRATEGY_MAP = {"b": "buy", "s": "sell", "k": "skip"}

# ---------------------------------------------------------------------------
# Helpers — random replacements for user input
# ---------------------------------------------------------------------------


def random_strategy_input(markets: list) -> str:
    """Generate a random strategy string like '1-b,2-s,3-k'."""
    parts = []
    for idx in range(1, len(markets) + 1):
        parts.append(f"{idx}-{random.choice('bsk')}")
    return ",".join(parts)


# ---------------------------------------------------------------------------
# Game loop
# ---------------------------------------------------------------------------

for round_number in range(1, table.total_rounds + 1):
    print(f"\n{'=' * 60}")
    print(f"--- Round {round_number} ---")
    print(f"{'=' * 60}")

    num_markets = uniform_int_range(1, min(3, len(table.markets)))
    markets = table.start_round(num_markets)

    print("\nAvailable Markets this round:")
    for idx, m in enumerate(markets, 1):
        print(
            f"  {idx}. {m.location.name} - {m.location.product}, "
            f"Price: {m.market_fixed_price} FCFA, Supply: {m.market_supply}"
        )

    # ---- Strategy phase: each player orders markets + announces strategy ----
    print(f"\n{'=' * 60}")
    print("STRATEGY PHASE")
    print(f"{'=' * 60}")
    print("Order your markets and announce your strategy for each.")
    print("  b = buy, s = sell, k = skip")
    print(
        "  Example: '1-b, 2-s, 3-k' means market 1 buy, market 2 sell, market 3 skip\n"
    )

    player_strategies: dict[str, list] = {}  # username -> [(market_idx, strategy), ...]

    for player in table.players:
        inv = (
            ", ".join(
                f"{i.product.name}: {i.quantity} (avg {i.avg_cost:.0f} FCFA)"
                for i in player.inventory
            )
            if player.inventory
            else "None"
        )
        print(f"--- {player.username}'s strategy ---")
        print(f"  Balance: {player.balance:.2f} FCFA")
        print(f"  Inventory: {inv}")

        while True:
            raw = random_strategy_input(markets)

            # Parse strategy
            parsed: list = []
            valid = True
            for part in raw.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    market_num, strat = part.split("-", 1)
                    market_num = int(market_num.strip())
                    strat = strat.strip().lower()
                    if not (1 <= market_num <= len(markets)):
                        print(
                            f"    ✗ Market {market_num} is invalid (1-{len(markets)})"
                        )
                        valid = False
                        break
                    if strat not in STRATEGY_MAP:
                        print(f"    ✗ Strategy '{strat}' is invalid (b/s/k)")
                        valid = False
                        break
                    parsed.append((market_num, STRATEGY_MAP[strat]))
                except ValueError:
                    print(
                        f"    ✗ Invalid format '{part}'. Use 'number-strategy' (e.g. '1-b')"
                    )
                    valid = False
                    break

            if not valid:
                continue

            if not parsed:
                print("    ✗ Empty strategy. Enter at least one market-strategy pair.")
                continue

            # Validate sell strategies - check player has the product
            sell_valid = True
            for market_num, strat in parsed:
                if strat == "sell":
                    market = markets[market_num - 1]
                    qty = player.get_inventory_quantity(market.location.product)
                    if qty <= 0:
                        print(
                            f"    ✗ You don't have {market.location.product} to sell in market {market_num}"
                        )
                        sell_valid = False
                        break

            if not sell_valid:
                continue

            player_strategies[player.username] = parsed
            strategies_str = ", ".join(f"M{m}-{s}" for m, s in parsed)
            print(f"  ✓ Strategy set: {strategies_str}")
            break

    # ---- Turn order: initial dice roll, highest first ----
    print(f"\n{'=' * 60}")
    print("TURN ORDER")
    print(f"{'=' * 60}")

    turn_order = table.determine_turn_order()
    print("\nTurn order (by dice roll, highest first):")
    for rank, (player, dice_total) in enumerate(turn_order, 1):
        print(f"  {rank}. {player.username} - Dice: {dice_total}")

    # ---- Action phase: each player goes through their market order ----
    print(f"\n{'=' * 60}")
    print("ACTION PHASE")
    print(f"{'=' * 60}")

    for player, initial_dice in turn_order:
        inv = (
            ", ".join(
                f"{i.product.name}: {i.quantity} (avg {i.avg_cost:.0f} FCFA)"
                for i in player.inventory
            )
            if player.inventory
            else "None"
        )
        print(f"\n{'─' * 50}")
        print(f"▶ {player.username}'s turn (initial dice: {initial_dice})")
        print(f"  Balance: {player.balance:.2f} FCFA")
        print(f"  Inventory: {inv}")

        strategies = player_strategies.get(player.username, [])

        for market_num, strategy in strategies:
            market = markets[market_num - 1]
            print(
                f"\n  --- Entering {market.location.name} ({market.location.product}) ---"
            )
            print(
                f"      Market price: {market.market_fixed_price} FCFA, Supply: {market.market_supply}"
            )

            if strategy == "skip":
                print("      ⏭ Skipping this market")
                continue

            # Roll dice for this market
            dice_total = table.roll_dice_for_player()
            dice_price = dice_total * 100
            print(
                f"      Rolled: {table.dice.die1} + {table.dice.die2} = {dice_total} (dice price: {dice_price} FCFA)"
            )

            if strategy == "buy":
                result = table.process_market_action_buy(player, market, dice_total)

                if not result["success"]:
                    print(f"      ✗ {result['error']}")
                    continue

                if not result["can_buy"]:
                    print("      ✗ Buy condition not met")
                    continue

                print(
                    f"      ✓ Buy condition met! (dice {dice_price} >= market {result['market_price']})"
                )
                print(
                    f"      Buying at market price: {result['market_price']} FCFA/unit"
                )
                print(f"      Max affordable: {result['max_affordable']} units")

                # Random quantity instead of user input
                quantity = random.randint(1, max(result["max_affordable"], 1))

                # Execute buy
                exec_result = table.execute_buy_at_market_price(
                    player, market, quantity
                )

                if not exec_result["success"]:
                    print(f"      ✗ {exec_result.get('error', 'Purchase failed')}")
                    continue

                print(
                    f"      ✓ Bought {exec_result['units_bought']} units at {exec_result['avg_price']} FCFA/unit"
                )
                print(f"        Cost: {exec_result['total_cost']:.2f} FCFA")
                print(f"        Buy tax: {exec_result['buy_tax']:.2f} FCFA")
                print(f"        Total paid: {exec_result['total_with_tax']:.2f} FCFA")
                print(f"        New balance: {exec_result['buyer_balance']:.2f} FCFA")

                for trade in exec_result["trades"]:
                    if trade["seller"] != "market":
                        print(
                            f"        → Paid {trade['seller']}: {trade['total']:.2f} FCFA for {trade['quantity']} units"
                        )

                if exec_result["unfilled"] > 0:
                    print(
                        f"        ⚠ {exec_result['unfilled']} units unfilled (insufficient supply)"
                    )

            elif strategy == "sell":
                # Pay fixed entry fee before rolling
                entry_fee_result = table.pay_sell_entry_fee(player, market)
                if not entry_fee_result["success"]:
                    print(f"      ✗ {entry_fee_result['error']}")
                    continue
                print(
                    f"      💰 Entry fee: {entry_fee_result['fee']} FCFA "
                    f"(balance: {entry_fee_result['seller_balance']:.2f} FCFA)"
                )

                result = table.process_market_action_sell(player, market, dice_total)

                if not result["success"]:
                    print(f"      ✗ {result['error']}")
                    continue

                if not result["can_sell"]:
                    print("      ✗ Sell condition not met")
                    continue

                print(
                    f"      ✓ Sell condition met! (dice {dice_price} <= market {result['market_price']})"
                )
                print(
                    f"      Market will auto-buy at dice price: {dice_price} FCFA/unit"
                )
                print(
                    f"      You have {result['seller_qty']} units of {result['product_name']}"
                )

                # Random quantity instead of user input
                quantity = random.randint(1, max(result["seller_qty"], 1))

                # Execute market auto-buy
                exec_result = table.execute_market_auto_buy(
                    player, market, quantity, dice_price
                )

                if not exec_result["success"]:
                    print(f"      ✗ {exec_result.get('error', 'Sale failed')}")
                    continue

                print(
                    f"      ✓ Sold {exec_result['quantity_sold']} units at {exec_result['price_per_unit']} FCFA/unit"
                )
                print(f"        Revenue: {exec_result['revenue']:.2f} FCFA")
                print(f"        Tax: {exec_result['tax_amount']:.2f} FCFA")
                print(f"        Net revenue: {exec_result['net_revenue']:.2f} FCFA")
                print(f"        New balance: {exec_result['seller_balance']:.2f} FCFA")

    # ---- End of round ----
    purchases = table.end_round(markets)
    if purchases:
        print(f"\n{'=' * 50}")
        print(f"END OF ROUND {round_number} - MARKET PURCHASES")
        print(f"{'=' * 50}")
        for p in purchases:
            seller = table.get_player(p["seller_username"])
            seller_name = seller.username if seller else "unknown"
            print(
                f"✓ Market purchases {p['quantity']} units at {p['purchase_price']} FCFA/unit"
            )
            print(f"  Seller: {seller_name}")

    print(f"\n{'=' * 50}")
    print(f"END OF ROUND {round_number} - STANDINGS")
    print(f"{'=' * 50}")
    for player in table.players:
        inv = (
            ", ".join(
                f"{i.product.name}: {i.quantity} (avg {i.avg_cost:.0f} FCFA)"
                for i in player.inventory
            )
            if player.inventory
            else "None"
        )
        print(
            f"  {player.username}: Balance = {player.balance:.2f} FCFA, Inventory = [{inv}]"
        )

# GAME OVER - Final Results
print(f"\n{'=' * 60}")
print(f"{'GAME OVER - FINAL RESULTS':^60}")
print(f"{'=' * 60}")

# Sort players by balance (descending)
final_standings = sorted(table.players, key=lambda p: p.balance, reverse=True)

for idx, player in enumerate(final_standings, 1):
    profit_loss = player.balance - starting_balance
    status = "+" if profit_loss >= 0 else ""
    inventory_str = (
        ", ".join(
            [
                f"{item.product.name}: {item.quantity} (avg {item.avg_cost:.0f} FCFA)"
                for item in player.inventory
            ]
        )
        if player.inventory
        else "None"
    )
    print(
        f"{idx}. {player.username:<20} Final Balance: {player.balance:>10,.0f} FCFA ({status}{profit_loss:>10,.0f})"
    )
    print(f"   Inventory: [{inventory_str}]")

print(f"\n{'🏆 ' + final_standings[0].username + ' WINS! 🏆':^60}")
print(f"{'=' * 60}")
