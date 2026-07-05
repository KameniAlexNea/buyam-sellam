"""Game Page for KSell Entreprise Gradio UI.

Main game interface with dice rolling, market trading, production, and game controls.
"""

import gradio as gr

from services.game_service import GameService
from utils.helpers import format_fortune, format_quantity


def create_game_page(game_service: GameService):
    """Create the main game page with all game controls."""

    def _market_choices():
        return [f"Market {i}: {m.location.name}" for i, m in enumerate(game_service.table.markets)]

    def on_start_game(username: str, player_fortune: float = 10000.0):
        if not username or len(username.strip()) < 3:
            return (gr.update(visible=True, value="❌ Please enter a player name (at least 3 characters)."),) + tuple(gr.update() for _ in range(8))
        username = username.strip()
        result = game_service.start_game(username, player_fortune=player_fortune)
        if result["success"]:
            markets_md = _markets_to_markdown(result["markets"])
            leaderboard_md = _leaderboard_to_markdown(result["leaderboard"])
            dice_md = (
                f"**🎲 {result['dice']['die1']} + {result['dice']['die2']} = {result['dice']['total']}** "
                f"({result['dice'].get('condition', 'normal')}) → "
                f"💵 Your price: **{result['dice']['total'] * 100} FCFA/unit** "
                f"({result['dice']['total']} × 100, range 200–1200)"
            )
            choices = _market_choices()
            status = game_service.get_player_status()
            return (
                gr.update(visible=True, value=f"✅ {result['message']}"),
                gr.update(visible=True, value=dice_md),
                gr.update(visible=True, value=markets_md),
                gr.update(visible=True, value=leaderboard_md),
                gr.update(visible=True, value=_player_status_to_markdown(status, result['player_fortune'])),
                gr.update(visible=True, value=_log_to_markdown(result["log"])),
                gr.update(choices=choices, value=choices[0] if choices else None),
                gr.update(choices=choices, value=choices[0] if choices else None),
                gr.update(choices=choices, value=choices[0] if choices else None),
            )
        else:
            return (gr.update(visible=True, value=f"❌ {result.get('error', 'Failed to start game')}"),) + tuple(gr.update() for _ in range(8))

    def on_roll_dice():
        result = game_service.roll_dice_and_next_round()
        if result["success"]:
            markets_md = _markets_to_markdown(result["markets"])
            leaderboard_md = _leaderboard_to_markdown(result["leaderboard"])
            dice_md = (
                f"**🎲 {result['dice']['die1']} + {result['dice']['die2']} = {result['dice']['total']}** "
                f"({result['condition']}) → "
                f"💵 Your price: **{result.get('dice_price', result['dice']['total'] * 100)} FCFA/unit** "
                f"({result['dice']['total']} × 100, range 200–1200)"
            )

            event_md = ""
            if result.get("event"):
                evt = result["event"]
                emoji = "✨" if evt["effect"] == "gain" else "💔"
                event_md = f"\n\n⚡ **{evt['name']}**\n{evt['description']}\n{emoji} {evt['amount']:,.0f} FCFA"

            choices = _market_choices()
            status = game_service.get_player_status()
            return (
                gr.update(visible=True, value=f"🎲 Tour {result['tour']} - Market condition: {result['condition'].upper()}"),
                gr.update(visible=True, value=dice_md + event_md),
                gr.update(visible=True, value=markets_md),
                gr.update(visible=True, value=leaderboard_md),
                gr.update(visible=True, value=_player_status_to_markdown(status, result['player_fortune'])),
                gr.update(visible=True, value=_log_to_markdown(result["log"])),
                gr.update(choices=choices),
                gr.update(choices=choices),
                gr.update(choices=choices),
            )
        else:
            return (gr.update(visible=True, value=f"❌ {result.get('error', 'Failed to roll dice')}"),) + tuple(gr.update() for _ in range(8))

    def on_post_sell(market_selection: str, quantity: int):
        market_idx = int(market_selection.split(":")[0].replace("Market ", "").strip())
        result = game_service.post_sell_order(market_idx, int(quantity))
        status = game_service.get_player_status()
        return (
            gr.update(visible=True, value=f"{'✅' if result['success'] else '❌'} {result['message']}"),
            gr.update(visible=True, value=_markets_to_markdown(result.get("markets", []))),
            gr.update(visible=True, value=_leaderboard_to_markdown(result.get("leaderboard", []))),
            gr.update(visible=True, value=_player_status_to_markdown(status, result.get("player_fortune"))),
            gr.update(visible=True, value=_log_to_markdown(result.get("log", []))),
        )

    def on_post_buy(market_selection: str, quantity: int):
        market_idx = int(market_selection.split(":")[0].replace("Market ", "").strip())
        result = game_service.post_buy_order(market_idx, int(quantity))
        status = game_service.get_player_status()
        return (
            gr.update(visible=True, value=f"{'✅' if result['success'] else '❌'} {result['message']}"),
            gr.update(visible=True, value=_markets_to_markdown(result.get("markets", []))),
            gr.update(visible=True, value=_leaderboard_to_markdown(result.get("leaderboard", []))),
            gr.update(visible=True, value=_player_status_to_markdown(status, result.get("player_fortune"))),
            gr.update(visible=True, value=_log_to_markdown(result.get("log", []))),
        )

    def on_buy_material(material_idx: int, quantity: int):
        result = game_service.buy_raw_material(material_idx, quantity)
        if result["success"]:
            inv_md = _inventory_to_markdown(result.get("inventory", []))
            return (
                gr.update(visible=True, value=f"✅ {result['message']}"),
                gr.update(visible=True, value=inv_md),
                gr.update(visible=True, value=f"**Fortune:** {format_fortune(result['player_fortune'])} | **Rank:** #{result['player_rank']}"),
                gr.update(visible=True, value=_leaderboard_to_markdown(result.get("leaderboard", []))),
                gr.update(visible=True, value=_log_to_markdown(result.get("log", []))),
            )
        else:
            return gr.update(visible=True, value=f"❌ {result.get('error', 'Purchase failed')}")

    def on_produce(product_idx: int, quantity: int):
        result = game_service.produce_goods(product_idx, quantity)
        if result["success"]:
            inv_md = _inventory_to_markdown(result.get("inventory", []))
            prod_md = _finished_products_to_markdown(result.get("finished_products", []))
            return (
                gr.update(visible=True, value=f"✅ {result['message']}"),
                gr.update(visible=True, value=inv_md),
                gr.update(visible=True, value=prod_md),
                gr.update(visible=True, value=f"**Fortune:** {format_fortune(result['player_fortune'])} | **Rank:** #{result['player_rank']}"),
                gr.update(visible=True, value=_leaderboard_to_markdown(result.get("leaderboard", []))),
                gr.update(visible=True, value=_log_to_markdown(result.get("log", []))),
            )
        else:
            return gr.update(visible=True, value=f"❌ {result.get('error', 'Production failed')}")

    def on_sell_finished(market_selection: str, product_idx: int, quantity: int):
        # Extract market index from dropdown selection
        market_idx = int(market_selection.split(":")[0].replace("Market ", "").strip())
        result = game_service.sell_finished_product(market_idx, product_idx, quantity)
        if result["success"]:
            markets_md = _markets_to_markdown(result.get("markets", []))
            prod_md = _finished_products_to_markdown(result.get("finished_products", []))
            leaderboard_md = _leaderboard_to_markdown(result.get("leaderboard", []))
            sale_detail = ""
            if result.get("sale_result"):
                sr = result["sale_result"]
                sale_detail = f"\n**Sale Details:** Revenue: {sr['revenue']:,.0f} FCFA | Tax: {sr['tax']:,.0f} FCFA | Net: {sr['net_revenue']:,.0f} FCFA"
            return (
                gr.update(visible=True, value=f"✅ {result['message']}{sale_detail}"),
                gr.update(visible=True, value=markets_md),
                gr.update(visible=True, value=prod_md),
                gr.update(visible=True, value=leaderboard_md),
                gr.update(visible=True, value=f"**Fortune:** {format_fortune(result['player_fortune'])} | **Rank:** #{result['player_rank']}"),
                gr.update(visible=True, value=_log_to_markdown(result.get("log", []))),
            )
        else:
            return gr.update(visible=True, value=f"❌ {result.get('error', 'Sale failed')}")

    def on_end_game():
        result = game_service.end_game()
        if result["success"]:
            final_md = _final_results_to_markdown(result["final_results"])
            return (
                gr.update(visible=True, value=f"🏁 {result['message']}"),
                gr.update(visible=True, value=final_md),
                gr.update(visible=True, value=_log_to_markdown(result["log"])),
            )
        else:
            return gr.update(visible=True, value=f"❌ {result.get('error', 'Failed to end game')}")

    with gr.Column(elem_id="game-container"):
        gr.Markdown("## 🎮 KSell Entreprise - Game")
        gr.Markdown("Roll the dice, produce goods, trade in markets, and build your empire!")

        # Game setup
        with gr.Accordion("🎯 Game Setup", open=True):
            with gr.Row():
                game_username = gr.Textbox(
                    label="Your Username",
                    placeholder="Enter your player name",
                    info="Min 3 characters",
                )
                game_fortune = gr.Slider(
                    minimum=1000,
                    maximum=100000,
                    value=10000,
                    step=1000,
                    label="Starting Fortune (FCFA)",
                )
            start_btn = gr.Button("🚀 Start Game", variant="primary", elem_id="start-btn")

        # Game status
        game_status = gr.Markdown(visible=False, elem_id="game-status")

        # Player status panel — always visible after game starts
        with gr.Row():
            with gr.Column(scale=2):
                player_status = gr.Markdown(
                    value="_Start the game to see your status._",
                    label="👤 My Status",
                    elem_id="player-status",
                )
            with gr.Column(scale=1):
                dice_display = gr.Markdown(visible=False, elem_id="dice-display")
                roll_btn = gr.Button("🎲 Roll Dice & Next Round", variant="primary", elem_id="roll-btn")

        # Markets and order book
        with gr.Row():
            with gr.Column():
                markets_display = gr.Markdown(visible=False, elem_id="markets-display")
            with gr.Column():
                leaderboard_display = gr.Markdown(visible=False, elem_id="leaderboard-display")

        # Trading actions
        with gr.Row():
            with gr.Column():
                gr.Markdown("#### 📋 Sell (at your dice price)")
                with gr.Row():
                    sell_market = gr.Dropdown(choices=[], label="Market")
                    sell_qty = gr.Number(label="Qty", value=5, precision=0, minimum=1)
                sell_btn = gr.Button("📋 Post Sell Order", variant="secondary", elem_id="sell-btn")

            with gr.Column():
                gr.Markdown("#### 🛒 Buy (cheapest offers first, up to your dice price)")
                with gr.Row():
                    buy_market = gr.Dropdown(choices=[], label="Market")
                    buy_qty = gr.Number(label="Qty", value=5, precision=0, minimum=1)
                buy_btn = gr.Button("🛒 Buy Now", variant="primary", elem_id="buy-btn")


        # Production section
        with gr.Accordion("🏭 Production", open=False):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📦 Buy Raw Materials")
                    material_choices = [f"{m['name']} - {m['price']:,} FCFA (yields {m['yield']} units)" for m in game_service.get_raw_materials()]
                    buy_material = gr.Dropdown(
                        choices=material_choices,
                        label="Select Material",
                        info="Choose a raw material to purchase",
                    )
                    buy_material_qty = gr.Number(label="Quantity", value=1, precision=0, minimum=1)
                    buy_material_btn = gr.Button("🛒 Buy Materials", variant="secondary", elem_id="buy-material-btn")

                with gr.Column():
                    gr.Markdown("### 🔧 Produce Finished Goods")
                    product_choices = [f"{p['name']} (from {p['raw_material']}) - sells for {p['sell_price']:,} FCFA" for p in game_service.get_finished_products()]
                    produce_product = gr.Dropdown(
                        choices=product_choices,
                        label="Select Product",
                        info="Choose a product to produce",
                    )
                    produce_qty = gr.Number(label="Quantity", value=1, precision=0, minimum=1)
                    produce_btn = gr.Button("🏭 Produce Goods", variant="secondary", elem_id="produce-btn")

            # Inventory displays
            with gr.Row():
                with gr.Column():
                    inventory_display = gr.Markdown(visible=False, elem_id="inventory-display")
                with gr.Column():
                    finished_display = gr.Markdown(visible=False, elem_id="finished-display")

        # Sell finished products
        with gr.Accordion("💰 Sell Finished Products", open=False):
            with gr.Row():
                sell_finished_market = gr.Dropdown(
                    choices=[],
                    label="Select Market",
                    info="Markets appear after starting the game",
                )
                sell_finished_product = gr.Number(label="Product Index (from inventory above)", value=0, precision=0)
                sell_finished_qty = gr.Number(label="Quantity", value=1, precision=0)
                sell_finished_btn = gr.Button("💰 Sell Finished Product", variant="secondary", elem_id="sell-finished-btn")

        # Game log (collapsed)
        with gr.Accordion("📜 Game Log", open=False):
            game_log_display = gr.Markdown(visible=True, value="_No events yet._", elem_id="game-log")

        # End game
        end_btn = gr.Button("🏁 End Game", variant="stop", elem_id="end-btn")
        final_results = gr.Markdown(visible=False, elem_id="final-results")

        # Event handlers
        start_btn.click(
            fn=on_start_game,
            inputs=[game_username, game_fortune],
            outputs=[game_status, dice_display, markets_display, leaderboard_display, player_status, game_log_display, sell_market, buy_market, sell_finished_market],
        )

        roll_btn.click(
            fn=on_roll_dice,
            inputs=[],
            outputs=[game_status, dice_display, markets_display, leaderboard_display, player_status, game_log_display, sell_market, buy_market, sell_finished_market],
        )

        sell_btn.click(
            fn=on_post_sell,
            inputs=[sell_market, sell_qty],
            outputs=[game_status, markets_display, leaderboard_display, player_status, game_log_display],
        )

        buy_btn.click(
            fn=on_post_buy,
            inputs=[buy_market, buy_qty],
            outputs=[game_status, markets_display, leaderboard_display, player_status, game_log_display],
        )

        buy_material_btn.click(
            fn=on_buy_material,
            inputs=[buy_material, buy_material_qty],
            outputs=[game_status, inventory_display, player_status, leaderboard_display, game_log_display],
        )

        produce_btn.click(
            fn=on_produce,
            inputs=[produce_product, produce_qty],
            outputs=[game_status, inventory_display, finished_display, player_status, leaderboard_display, game_log_display],
        )

        sell_finished_btn.click(
            fn=on_sell_finished,
            inputs=[sell_finished_market, sell_finished_product, sell_finished_qty],
            outputs=[game_status, markets_display, finished_display, leaderboard_display, player_status, game_log_display],
        )

        end_btn.click(
            fn=on_end_game,
            inputs=[],
            outputs=[game_status, final_results, game_log_display],
        )

    return game_username, game_fortune, start_btn, roll_btn, sell_btn, end_btn


def _player_status_to_markdown(status: dict, fortune: float = None) -> str:
    if "error" in status:
        return "_Start the game to see your status._"
    f = fortune if fortune is not None else status.get("fortune", 0)
    rank = status.get("rank", "?")
    basic_stock = status.get("basic_stock", 0)
    tools = status.get("tools", [])
    capacity = status.get("total_capacity", 0) or 50
    inventory = status.get("inventory", [])
    finished = status.get("finished_products", [])
    cards = status.get("cards", [])

    lines = [f"**💰 {format_fortune(f)}** | 🏆 Rank #{rank} | 📦 Stock: **{basic_stock} units**"]
    if tools:
        lines.append("🔧 " + ", ".join(t.get("name","?") for t in tools) + f" → restock {capacity}/round")
    else:
        lines.append("🔧 No tools (restock 50/round — buy in Marketplace)")
    if inventory:
        lines.append("📦 Materials: " + ", ".join(f"{i['name']} ×{i['quantity']}" for i in inventory))
    if finished:
        lines.append("🏭 Goods: " + ", ".join(f"{p['name']} ×{p['quantity']}" for p in finished))
    if cards:
        lines.append("🃏 " + ", ".join(cards))
    return "  \n".join(lines)


def _markets_to_markdown(markets: list) -> str:
    if not markets:
        return "No active markets."
    md = ""
    for i, m in enumerate(markets):
        location = m.get("location", {})
        product = m.get("product", location.get("product", "?"))
        fixed = m.get("market_fixed_price", location.get("fixed_price", 0))
        supply = m.get("market_supply", m.get("remaining_qty", 0))
        tax_rate = location.get("tax_rate", 0)

        md += (
            f"**Market {i}: {location.get('name','?')}** "
            f"| 📦 Product: **{product}** "
            f"| 🏷 Fixed price: **{fixed:,} FCFA/unit** "
            f"| Supply: {supply:,} "
            f"| Tax: {tax_rate*100:.0f}%\n\n"
        )
        orders = m.get("sell_orders", [])
        if orders:
            md += "| Seller | Qty | Their price | vs fixed |\n|--------|-----|-------------|----------|\n"
            for o in orders[:6]:
                vs = "✅ sells" if o["price"] <= fixed else "⏳ wait"
                md += f"| {o['username']} | {o['remaining']} | {o['price']:,} | {vs} |\n"
            md += "\n"
        else:
            md += "_No sell orders yet._\n\n"
    return md


def _leaderboard_to_markdown(leaderboard: list) -> str:
    """Convert leaderboard to markdown display."""
    if not leaderboard:
        return "No players yet."

    md = "**🏆 Leaderboard:**\n\n"
    md += "| Rank | Player | Fortune | Stars | Games |\n"
    md += "|------|--------|---------|-------|-------|\n"
    for entry in leaderboard:
        md += f"| #{entry['rank']} | {entry['username']} | {format_fortune(entry['balance'])} | ⭐{entry['stars']} | 🎮{entry['competitions']} |\n"
    return md


def _inventory_to_markdown(inventory: list) -> str:
    if not inventory:
        return "No raw materials in inventory."
    md = "**📦 Raw Materials Inventory:**\n\n"
    for item in inventory:
        md += f"- **{item['name']}**: {item['quantity']} units (yields {item['yield']} finished units each)\n"
    return md


def _finished_products_to_markdown(products: list) -> str:
    if not products:
        return "No finished products."
    md = "**🏭 Finished Products:**\n\n"
    for item in products:
        md += f"- **{item['name']}**: {item['quantity']} units (sells for {item['sell_price']:,} FCFA each)\n"
    return md


def _log_to_markdown(log: list) -> str:
    """Convert game log to markdown display."""
    if not log:
        return "No game events yet."

    md = "**📜 Game Log:**\n\n"
    for entry in log[-15:]:  # Show last 15 entries
        md += f"- {entry}\n"
    return md


def _final_results_to_markdown(results: dict) -> str:
    """Convert final game results to markdown display."""
    md = "**🏁 Final Results:**\n\n"
    winner = results.get("winner")
    if winner:
        md += f"**🥇 Winner: {winner['username']}** with {format_fortune(winner['balance'])}!\n\n"
    md += "**Final Standings:**\n\n"
    md += "| Rank | Player | Balance | Stars |\n"
    md += "|------|--------|---------|-------|\n"
    for entry in results.get("leaderboard", []):
        md += f"| #{entry['rank']} | {entry['username']} | {format_fortune(entry['balance'])} | ⭐{entry['stars']} |\n"
    md += f"\nTotal rounds played: {results.get('total_rounds', 0)}"
    return md
