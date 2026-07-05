from ksell.model.player import Player
from ksell.model.table import Table
from ksell.utils.random_utils import uniform_int_range
from ksell.pojo.user import User
from ksell.pojo.product import Product
import random

print("""
Welcome to Buyam-Sellam App
      
Configure players and start the game!
""")

n_payers = int(input("Enter number of players: "))
if n_payers < 2:
    print("At least 2 players are required to start the game.")
    exit()

users = []
for i in range(n_payers):
    name = input(f"Enter name for player {i + 1}: ")
    if not name:
        print("Player name cannot be empty. Please enter a valid name.")
        exit()
    users.append(User(username=name))

starting_balance = float(input("Enter starting balance for each player: "))
players = [Player(user=user) for user in users]
for player in players:
    player.balance = starting_balance

n_rounds = int(input("Enter number of rounds for the game: "))

table = Table(players=players, total_rounds=n_rounds)
player_decision = {
        1: "buy",
        2: "sell",
        3: "skip"
    }

table.generate_markets()

# Initialize players with random starting products (20 units total per player)
print("\nInitializing starting inventory for each player...")
player_inventory_info = table.initialize_player_inventory(units_per_player=20)
for username, inventory_str in player_inventory_info.items():
    print(f"  {username}: {inventory_str}")

print()

for round_number in range(1, table.total_rounds + 1):
    print(f"\n--- Round {round_number} ---")

    n_round_markets = uniform_int_range(1, min(3, len(table.markets)))

    choose_markets = random.sample(table.markets, n_round_markets)
    print("Available Markets and Products for this round:")
    for choose_market in choose_markets:
        print(f"Market: {choose_market.location.name}, Product: {choose_market.location.product}, Price: {choose_market.location.fixed_price}, Qty: {choose_market.total_qty}")

    decision_player = {
        "buy": [],
        "sell": [],
        "skip": []
    }
    player_dice = {}  # Store dice values for each player
    
    for player in table.players:
        inventory_str = ", ".join([f"{item.product.name}: {item.quantity}" for item in player.inventory]) if player.inventory else "None"
        print(f"\nPlayer: {player.username}")
        print(f"  Balance: {player.balance:.2f} FCFA")
        print(f"  Products: {inventory_str}")
        dice = table.dice.shake()
        player_dice[player.username] = dice
        print(f"  You rolled: {dice.die1} + {dice.die2} = {dice.total()}")
        buy_sell_skip = int(input("Do you want to buy or sell? (1. buy/ 2. sell/3. skip)"))
        decision_player[player_decision[buy_sell_skip]].append(player)
    
    # Initialize all markets for this round
    for market in choose_markets:
        market._init_round()
    
    # Track total sold per market to enforce capacity limits
    market_total_sold = {market.location.name: 0 for market in choose_markets}
    
    # SELLING PHASE: Process sellers sorted by dice value (ascending)
    sellers = decision_player["sell"]
    if sellers:
        print("\n" + "="*60)
        print("SELLING PHASE")
        print("="*60)
        
        # Sort sellers by dice value (ascending - lowest dice goes first)
        sellers_sorted = sorted(sellers, key=lambda p: player_dice[p.username])
        
        for seller in sellers_sorted:
            dice_value = player_dice[seller.username]
            selling_price = dice_value.total() * 100
            
            inventory_str = ", ".join([f"{item.product.name}: {item.quantity}" for item in seller.inventory]) if seller.inventory else "None"
            print(f"\n{seller.username} (Dice: {dice_value.total()}, Selling Price: {selling_price} FCFA/unit)")
            print(f"  Balance: {seller.balance:.2f} FCFA")
            print(f"  Inventory: {inventory_str}")
            print("\nAvailable Markets:")
            for idx, market in enumerate(choose_markets, 1):
                remaining = market.remaining_qty - market_total_sold[market.location.name]
                initial_capacity = market.remaining_qty
                print(f"  {idx}. {market.location.name} - {market.location.product}")
                print(f"     Market Price: {market.market_fixed_price} FCFA, Tax Rate: {market.location.tax_rate*100:.1f}%")
                print(f"     Capacity: {remaining}/{initial_capacity} units available")
            
            try:
                market_choice = int(input(f"Choose a market (1-{len(choose_markets)}): "))
                
                if market_choice < 1 or market_choice > len(choose_markets):
                    print("Invalid market choice. Skipping.")
                    continue
                
                chosen_market = choose_markets[market_choice - 1]
                remaining_capacity = chosen_market.remaining_qty - market_total_sold[chosen_market.location.name]
                
                if remaining_capacity <= 0:
                    print(f"✗ {chosen_market.location.name} is full. Cannot sell.")
                    continue
                
                # Check how many units seller has of this product
                seller_qty = seller.get_inventory_quantity(chosen_market.location.product)
                if seller_qty <= 0:
                    print(f"✗ You don't have any {chosen_market.location.product} to sell.")
                    continue
                
                # Max sellable is the minimum of seller's inventory and market capacity
                max_sellable = min(seller_qty, remaining_capacity)
                quantity = int(input(f"How many units of {chosen_market.location.product} do you want to sell? (max {max_sellable}): "))
                
                if quantity <= 0:
                    print("Invalid quantity. Skipping.")
                    continue
                
                if quantity > remaining_capacity:
                    print(f"Reducing quantity to market capacity: {remaining_capacity}")
                    quantity = remaining_capacity
                
                # Calculate tax for listing the product
                tax_amount = quantity * selling_price * chosen_market.location.tax_rate
                
                if seller.balance < tax_amount:
                    print(f"✗ Insufficient balance to pay listing tax ({tax_amount:.2f} FCFA). Skipping.")
                    continue
                
                # Post sell order to the market
                result = chosen_market.post_sell_order(seller.username, quantity, selling_price)
                
                if result["success"]:
                    # Deduct tax from seller's balance
                    seller.balance -= tax_amount
                    market_total_sold[chosen_market.location.name] += quantity
                    print(f"✓ {seller.username} listed {quantity} units at {selling_price} FCFA/unit on {chosen_market.location.name}")
                    print(f"  Tax paid: {tax_amount:.2f} FCFA (rate: {chosen_market.location.tax_rate*100:.1f}%)")
                    print(f"  New balance: {seller.balance:.2f} FCFA")
                else:
                    print(f"✗ Error: {result.get('error', 'Unknown error')}")
                    
            except ValueError:
                print("Invalid input. Skipping this seller.")
                continue
    
    # BUYING PHASE: Process buyers
    buyers = decision_player["buy"]
    if buyers:
        print("\n" + "="*60)
        print("BUYING PHASE")
        print("="*60)
        
        for buyer in buyers:
            dice_value = player_dice[buyer.username]
            max_buying_price = dice_value.total() * 100
            
            inventory_str = ", ".join([f"{item.product.name}: {item.quantity}" for item in buyer.inventory]) if buyer.inventory else "None"
            print(f"\n{buyer.username} (Dice: {dice_value.total()}, Max Buying Price: {max_buying_price} FCFA/unit)")
            print(f"  Balance: {buyer.balance:.2f} FCFA")
            print(f"  Inventory: {inventory_str}")
            print("\nAvailable Markets:")
            for idx, market in enumerate(choose_markets, 1):
                total_sell_order_qty = sum(order['remaining'] for order in market.sell_orders if order['price'] <= max_buying_price)
                lowest_price = min([order['price'] for order in market.sell_orders], default=market.market_fixed_price)
                
                print(f"  {idx}. {market.location.name} - {market.location.product}")
                print(f"     Market Price: {market.market_fixed_price} FCFA, Tax Rate: {market.location.tax_rate*100:.1f}%")
                print(f"     Capacity: {market.remaining_qty}/{market.total_qty} units available")
                
                # Show available sell orders at or below buyer's max price
                affordable_orders = [o for o in market.sell_orders if o['price'] <= max_buying_price]
                if affordable_orders:
                    print(f"     Sell Orders (within your budget): {len(affordable_orders)} orders ({sum(o['remaining'] for o in affordable_orders)} units total)")
                    print(f"     Cheapest available: {min(o['price'] for o in affordable_orders)} FCFA/unit")
                else:
                    cheapest_in_market = min([o['price'] for o in market.sell_orders], default=None)
                    if cheapest_in_market and cheapest_in_market > max_buying_price:
                        print(f"     ✗ Sell Orders: {len(market.sell_orders)} orders but cheapest is {cheapest_in_market} FCFA (exceeds your limit of {max_buying_price})")
                    else:
                        print(f"     Sell Orders: {len(market.sell_orders)} orders ({sum(o['remaining'] for o in market.sell_orders)} units total)")
                
                if market.market_supply > 0:
                    print(f"     Market Supply: {market.market_supply} units at {market.market_fixed_price} FCFA/unit")
            
            # Check if there are ANY markets with affordable products before asking
            has_affordable_market = False
            for market in choose_markets:
                affordable_sell_orders = [o for o in market.sell_orders if o['price'] <= max_buying_price]
                market_can_supply = market.market_supply > 0 and market.market_fixed_price <= max_buying_price
                if affordable_sell_orders or market_can_supply:
                    has_affordable_market = True
                    break
            
            if not has_affordable_market:
                print(f"✗ No products available at your max price ({max_buying_price} FCFA) in any market. Skipping.")
                continue
            
            try:
                market_choice = int(input(f"Choose a market (1-{len(choose_markets)}): "))
                
                if market_choice < 1 or market_choice > len(choose_markets):
                    print("Invalid market choice. Skipping.")
                    continue
                
                chosen_market = choose_markets[market_choice - 1]
                
                # Check if there are affordable products
                affordable_sell_orders = [o for o in chosen_market.sell_orders if o['price'] <= max_buying_price]
                market_can_supply = chosen_market.market_supply > 0 and chosen_market.market_fixed_price <= max_buying_price
                
                if not affordable_sell_orders and not market_can_supply:
                    print(f"✗ No products available at your max price ({max_buying_price} FCFA). Skipping.")
                    continue
                
                # Show what's available
                cheapest_available = min(
                    [o['price'] for o in affordable_sell_orders] + 
                    ([chosen_market.market_fixed_price] if market_can_supply else []),
                    default=None
                )
                max_affordable = min(
                    int(buyer.balance // cheapest_available) if cheapest_available else 0,
                    chosen_market.remaining_qty  # Cap by market capacity
                )
                
                quantity = int(input(f"How many units do you want to buy? (max affordable: {max_affordable}): "))
                
                if quantity <= 0:
                    print("Invalid quantity. Skipping.")
                    continue
                
                # Execute buy order with price limit
                result = chosen_market.execute_buy(buyer.username, quantity, max_buying_price)
                
                if result["success"]:
                    units_bought = result["units_bought"]
                    total_cost = result["total_cost"]
                    avg_price = result["avg_price"]
                    
                    # Deduct from buyer's balance
                    buyer.balance -= total_cost
                    
                    # Add products to buyer's inventory
                    product_name = chosen_market.location.product
                    product = Product(name=product_name, price=avg_price)
                    buyer.add_to_inventory(product, units_bought)
                    
                    print(f"✓ {buyer.username} bought {units_bought} units of {product_name} from {chosen_market.location.name}")
                    print(f"  Average price: {avg_price} FCFA/unit")
                    print(f"  Total cost: {total_cost:.2f} FCFA")
                    print(f"  New balance: {buyer.balance:.2f} FCFA")
                    
                    # Pay sellers
                    for trade in result["trades"]:
                        if trade["seller"] != "market":
                            seller_player = next((p for p in table.players if p.username == trade["seller"]), None)
                            if seller_player:
                                seller_player.balance += trade["total"]
                                print(f"  → Paid {trade['seller']}: {trade['total']:.2f} FCFA for {trade['quantity']} units at {trade['price']} FCFA/unit")
                    
                    if result["unfilled"] > 0:
                        print(f"  ⚠ {result['unfilled']} units could not be purchased (insufficient supply or exceeded price limit)")
                else:
                    print(f"✗ {result.get('error', 'Purchase failed')}")
                    
            except ValueError:
                print("Invalid input. Skipping this buyer.")
                continue
    
    # End of round summary
    print(f"\n{'='*50}")
    print(f"END OF ROUND {round_number}")
    print(f"{'='*50}")
    for player in table.players:
        inventory_str = ", ".join([f"{item.product.name}: {item.quantity}" for item in player.inventory]) if player.inventory else "None"
        print(f"{player.username}: Balance = {player.balance:.2f} FCFA, Inventory = [{inventory_str}]")

# GAME OVER - Final Results
print(f"\n{'='*60}")
print(f"{'GAME OVER - FINAL RESULTS':^60}")
print(f"{'='*60}")

# Sort players by balance (descending)
final_standings = sorted(table.players, key=lambda p: p.balance, reverse=True)

for idx, player in enumerate(final_standings, 1):
    profit_loss = player.balance - starting_balance
    status = "+" if profit_loss >= 0 else ""
    inventory_str = ", ".join([f"{item.product.name}: {item.quantity}" for item in player.inventory]) if player.inventory else "None"
    print(f"{idx}. {player.username:<20} Final Balance: {player.balance:>10,.0f} FCFA ({status}{profit_loss:>10,.0f})")
    print(f"   Inventory: [{inventory_str}]")

print(f"\n{'🏆 ' + final_standings[0].username + ' WINS! 🏆':^60}")
print(f"{'='*60}")
