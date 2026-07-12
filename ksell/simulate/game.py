"""Buyam-Sellam — automated simulation.

Runs a full game with random decisions for testing.
Configure number of players and rounds, then let it run.
"""

import random

from ksell.model.player import Player
from ksell.model.table import Table
from ksell.model.market_board import MarketBoard
from ksell.pojo.user import User
from ksell.utils.random_utils import uniform_int_range

STRATEGY_MAP = {"b": "buy", "s": "sell", "k": "skip"}


def random_strategy(player: Player, markets: list[MarketBoard]) -> list:
    """Generate a random strategy for a player given available markets.

    Returns a list of (market_index_1based, strategy) tuples.
    """
    parsed = []
    for idx, market in enumerate(markets, 1):
        product = market.location.product
        roll = random.random()

        if roll < 0.4:
            # 40% chance to skip
            parsed.append((idx, "skip"))
        elif player.get_inventory_quantity(product) > 0 and roll < 0.7:
            # 30% chance to sell (if player has the product)
            parsed.append((idx, "sell"))
        else:
            # 30% chance to buy
            parsed.append((idx, "buy"))

    return parsed


def simulate_game(num_players: int = 3, num_rounds: int = 5, starting_balance: float = 5000.0) -> None:
    """Run a full game simulation with random decisions."""

    # Setup players
    users = [User(username=f"Player_{i}") for i in range(1, num_players + 1)]
    players = [Player(user=u) for u in users]
    for p in players:
        p.balance = starting_balance

    table = Table(players=players, total_rounds=num_rounds)
    table.generate_markets()
    table.initialize_player_inventory(units_per_player=20)

    print(f"{'=' * 60}")
    print(f"BUYAM-SELLAM SIMULATION")
    print(f"{'=' * 60}")
    print(f"Players: {num_players}, Rounds: {num_rounds}, Starting balance: {starting_balance:.0f} FCFA\n")

    for round_number in range(1, table.total_rounds + 1):
        print(f"{'=' * 60}")
        print(f"--- Round {round_number} ---")
        print(f"{'=' * 60}")

        num_markets = uniform_int_range(1, min(3, len(table.markets)))
        markets = table.start_round(num_markets)

        print(f"\nMarkets ({len(markets)}):")
        for idx, m in enumerate(markets, 1):
            print(f"  {idx}. {m.location.name} - {m.location.product}, "
                  f"Price: {m.market_fixed_price} FCFA, Supply: {m.market_supply}")

        # Strategy phase
        player_strategies: dict[str, list] = {}
        for player in table.players:
            strategies = random_strategy(player, markets)
            player_strategies[player.username] = strategies
            strategies_str = ", ".join(f"M{m}-{s}" for m, s in strategies)
            print(f"  {player.username}: {strategies_str}")

        # Turn order
        turn_order = table.determine_turn_order()

        # Action phase
        for player, initial_dice in turn_order:
            strategies = player_strategies.get(player.username, [])

            for market_num, strategy in strategies:
                market = markets[market_num - 1]

                if strategy == "skip":
                    continue

                dice_total = table.roll_dice_for_player()
                dice_price = dice_total * 100

                if strategy == "buy":
                    result = table.process_market_action_buy(player, market, dice_total)

                    if not result.get("success") or not result.get("can_buy"):
                        continue

                    qty = random.randint(1, result["max_affordable"])
                    exec_result = table.execute_buy_at_market_price(player, market, qty)

                    if exec_result.get("success"):
                        print(f"  {player.username} bought {exec_result['units_bought']} "
                              f"{market.location.product} at {exec_result['avg_price']} FCFA "
                              f"(total: {exec_result['total_with_tax']:.0f} FCFA)")

                elif strategy == "sell":
                    result = table.process_market_action_sell(player, market, dice_total)

                    if not result.get("success") or not result.get("can_sell"):
                        continue

                    qty = random.randint(1, result["seller_qty"])
                    exec_result = table.execute_market_auto_buy(player, market, qty, dice_price)

                    if exec_result.get("success"):
                        print(f"  {player.username} sold {exec_result['quantity_sold']} "
                              f"{market.location.product} at {exec_result['price_per_unit']} FCFA "
                              f"(net: {exec_result['net_revenue']:.0f} FCFA)")

        # End of round
        purchases = table.end_round(markets)
        if purchases:
            for p in purchases:
                print(f"  Market purchased {p['quantity']} units at {p['purchase_price']} FCFA")

        # Round standings
        print(f"\nRound {round_number} standings:")
        for player in table.players:
            inv = ", ".join(f"{i.product.name}: {i.quantity}" for i in player.inventory) if player.inventory else "None"
            print(f"  {player.username}: {player.balance:.0f} FCFA [{inv}]")

    # Final results
    print(f"\n{'=' * 60}")
    print(f"FINAL RESULTS")
    print(f"{'=' * 60}")

    final_standings = sorted(table.players, key=lambda p: p.balance, reverse=True)
    for idx, player in enumerate(final_standings, 1):
        profit_loss = player.balance - starting_balance
        status = "+" if profit_loss >= 0 else ""
        inventory_str = (
            ", ".join(f"{item.product.name}: {item.quantity}" for item in player.inventory)
            if player.inventory
            else "None"
        )
        print(f"{idx}. {player.username:<15} Balance: {player.balance:>10,.0f} FCFA ({status}{profit_loss:>10,.0f})")
        print(f"   Inventory: [{inventory_str}]")

    print(f"\nWinner: {final_standings[0].username}!")


if __name__ == "__main__":
    import sys

    try:
        n_players = int(input("Enter number of players (default 3): ").strip() or "3")
    except ValueError:
        n_players = 3

    try:
        n_rounds = int(input("Enter number of rounds (default 5): ").strip() or "5")
    except ValueError:
        n_rounds = 5

    simulate_game(num_players=n_players, num_rounds=n_rounds)
