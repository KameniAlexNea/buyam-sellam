from ksell.model.dice import Dice
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
    while True:
        name = input(f"Enter name for player {i + 1}: ").strip()
        if not name:
            print("Player name cannot be empty. Please enter a valid name.")
            continue
        if any(user.username == name for user in users):
            print(f"Username '{name}' already taken. Please choose a different name.")
            continue
        users.append(User(username=name))
        break

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
    
    # Update market prices if they made purchases last round, then clear order books for this round
    for market in choose_markets:
        # Update market price from last round's purchase (if any)
        if market.last_purchase_price is not None:
            market.market_fixed_price = market.last_purchase_price
            market.last_purchase_price = None
        
        market.sell_orders = []
        market.completed_trades = []
        market.total_qty = market.remaining_qty  # Capture round start quantity
    
    print("Available Markets and Products for this round:")
    for choose_market in choose_markets:
        print(f"Market: {choose_market.location.name}, Product: {choose_market.location.product}, Price: {choose_market.market_fixed_price}, Qty: {choose_market.total_qty}")

    decision_player = {
        "buy": [],
        "sell": [],
        "skip": []
    }
    player_dice: dict[str, Dice] = {}  # Store dice values for each player
    
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
    
    # Track total sold per market to enforce capacity limits
    market_total_sold = {market.location.name: 0 for market in choose_markets}
    
    # SELLING PHASE: Process sellers sorted by dice value (ascending)
    sellers = decision_player["sell"]
    if sellers:
        print("\n" + "="*60)
        print("SELLING PHASE")
        print("="*60)
        
        # Sort sellers by dice value (ascending - lowest dice goes first)
        sellers_sorted = sorted(sellers, key=lambda p: player_dice[p.username].total())
        
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
                status = "(FULL)" if remaining <= 0 else ""
                print(f"  {idx}. {market.location.name} - {market.location.product}")
                print(f"     Market Price: {market.market_fixed_price} FCFA, Tax Rate: {market.location.tax_rate*100:.1f}%")
                print(f"     Capacity: {remaining}/{initial_capacity} units available {status}")
            
            try:
                market_choice = int(input(f"Choose a market (1-{len(choose_markets)}): "))
                
                if market_choice < 1 or market_choice > len(choose_markets):
                    print("Invalid market choice. Skipping.")
                    continue
                
                chosen_market = choose_markets[market_choice - 1]
                
                # Check seller has product
                seller_qty = seller.get_inventory_quantity(chosen_market.location.product)
                if seller_qty <= 0:
                    print(f"✗ You don't have any {chosen_market.location.product} to sell.")
                    continue
                
                quantity = int(input(f"How many units of {chosen_market.location.product} do you want to sell? (max {seller_qty}): "))
                
                if quantity <= 0:
                    print("Invalid quantity. Skipping.")
                    continue
                
                if quantity > seller_qty:
                    print(f"Reducing to your inventory: {seller_qty}")
                    quantity = seller_qty
                
                # Process sell order (handles both normal posting and market-full)
                result = chosen_market.handle_sell_order(seller.username, quantity, selling_price)
                
                if not result["success"]:
                    print(f"✗ {result.get('error', 'Sale failed')}")
                    continue
                
                # Apply tax (must be paid upfront for listing)
                tax_amount = result["tax_amount"]
                if seller.balance < tax_amount:
                    print(f"✗ Insufficient balance to pay tax ({tax_amount:.2f} FCFA). Skipping.")
                    continue
                
                seller.balance -= tax_amount
                seller.remove_from_inventory(chosen_market.location.product, quantity)
                
                if result["mode"] == "market_purchase":
                    qty_purchased = result["quantity_purchased"]
                    purchase_price = result["purchase_price"]
                    
                    # Market purchase is PENDING - will execute at END OF ROUND
                    # Seller receives payment now for units that will be bought at end of round
                    revenue = qty_purchased * purchase_price
                    seller.balance += revenue
                    
                    print(f"✓ {chosen_market.location.name} will purchase {qty_purchased} units from {seller.username} at end of round (market was full)")
                    print(f"  Purchase price: {purchase_price} FCFA/unit")
                    print(f"  Tax paid by seller: {tax_amount:.2f} FCFA (on {quantity} units listed)")
                    print(f"  Revenue received: {revenue:.2f} FCFA")
                    print(f"  New balance: {seller.balance:.2f} FCFA")
                    print(f"  ℹ Market will receive inventory at end of round")
                    print(f"  ℹ Market price next round: {purchase_price} FCFA/unit")
                elif result["mode"] == "order_book":
                    market_total_sold[chosen_market.location.name] += quantity
                    print(f"✓ {seller.username} listed {quantity} units at {result['listing_price']} FCFA/unit on {result['market_name']}")
                    print(f"  Tax paid: {tax_amount:.2f} FCFA (rate: {chosen_market.location.tax_rate*100:.1f}%)")
                    print(f"  New balance: {seller.balance:.2f} FCFA")
                    
            except ValueError:
                print("Invalid input. Skipping this seller.")
                continue
    
    # BUYING PHASE: Process buyers
    buyers = decision_player["buy"]
    if buyers:
        print("\n" + "="*60)
        print("BUYING PHASE")
        print("="*60)
        
        # Sort buyers by dice value (descending - highest dice goes first)
        buyers_sorted = sorted(buyers, key=lambda p: player_dice[p.username].total(), reverse=True)
        
        for buyer in buyers_sorted:
            dice_value = player_dice[buyer.username]
            max_buying_price = dice_value.total() * 100
            
            inventory_str = ", ".join([f"{item.product.name}: {item.quantity}" for item in buyer.inventory]) if buyer.inventory else "None"
            print(f"\n{buyer.username} (Dice: {dice_value.total()}, Max Buying Price: {max_buying_price} FCFA/unit)")
            print(f"  Balance: {buyer.balance:.2f} FCFA")
            print(f"  Inventory: {inventory_str}")
            print("\nAvailable Markets:")
            
            # Display market info for each market
            market_info_list = []
            for idx, market in enumerate(choose_markets, 1):
                info = market.get_market_display_info(max_buying_price)
                market_info_list.append(info)
                print(f"  {idx}. {info['market_name']} - {info['product']}")
                print(f"     Market Price: {info['market_price']} FCFA, Tax Rate: {info['tax_rate']*100:.1f}%")
                print(f"     Capacity: {info['capacity']}/{info['total_qty']} units available")
                print(f"     {info['sell_orders_info']}")
                if info['market_supply_info']:
                    print(f"     {info['market_supply_info']}")
            
            # Check if any market has affordable products
            has_affordable = any(info['has_affordable'] for info in market_info_list)
            if not has_affordable:
                print(f"✗ No products available at your max price ({max_buying_price} FCFA) in any market. Skipping.")
                continue
            
            try:
                market_choice = int(input(f"Choose a market (1-{len(choose_markets)}): "))
                
                if market_choice < 1 or market_choice > len(choose_markets):
                    print("Invalid market choice. Skipping.")
                    continue
                
                chosen_market = choose_markets[market_choice - 1]
                chosen_info = market_info_list[market_choice - 1]
                
                if not chosen_info['has_affordable']:
                    print(f"✗ No products available at your max price ({max_buying_price} FCFA). Skipping.")
                    continue
                
                # Determine max affordable quantity
                cheapest = chosen_info['cheapest_available']
                max_affordable = min(
                    int(buyer.balance // cheapest) if cheapest else 0,
                    chosen_market.remaining_qty
                )
                
                quantity = int(input(f"How many units do you want to buy? (max affordable: {max_affordable}): "))
                
                if quantity <= 0:
                    print("Invalid quantity. Skipping.")
                    continue
                
                # Execute buy order
                result = chosen_market.execute_buy(buyer.username, quantity, max_buying_price)
                
                if not result["success"]:
                    print(f"✗ {result.get('error', 'Purchase failed')}")
                    continue
                
                units_bought = result["units_bought"]
                total_cost = result["total_cost"]
                avg_price = result["avg_price"]
                
                # Update buyer
                buyer.balance -= total_cost
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
                    
            except ValueError:
                print("Invalid input. Skipping this buyer.")
                continue
    
    # EXECUTE PENDING MARKET PURCHASES (at end of round)
    print(f"\n{'='*50}")
    print(f"END OF ROUND {round_number} - MARKET PURCHASES")
    print(f"{'='*50}")
    for market in choose_markets:
        purchase = market.execute_pending_market_purchase()
        if purchase:
            seller = next((p for p in table.players if p.username == purchase["seller_username"]), None)
            if seller:
                print(f"✓ {market.location.name} purchases {purchase['quantity']} units of {market.product} at {purchase['purchase_price']} FCFA/unit")
                print(f"  Seller: {seller.username}")
                print(f"  Note: Units will be available for buyers in next round")
    
    # End of round summary
    print(f"\n{'='*50}")
    print(f"END OF ROUND {round_number} - FINAL STANDINGS")
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
