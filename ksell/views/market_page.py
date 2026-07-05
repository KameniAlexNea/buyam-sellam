"""Market Page for KSell Entreprise Gradio UI.

Detailed market view with tools, cards, locations, and production supplies.
"""

import gradio as gr

from ksell.services.game_service import GameService
from ksell.utils.helpers import (
    format_fortune,
    get_card_options,
    get_tool_options,
)


def create_market_page(game_service: GameService):
    """Create the market/trading page with tools, cards, locations, and supplies."""

    def on_buy_tool(tool_idx: int):
        result = game_service.buy_tool(tool_idx)
        if result["success"]:
            tools_md = _tools_to_markdown(result.get("player_tools", []))
            return (
                gr.update(visible=True, value=f"✅ {result['message']}"),
                gr.update(visible=True, value=tools_md),
                gr.update(
                    visible=True,
                    value=f"**Fortune:** {format_fortune(result['player_fortune'])} | **Rank:** #{result['player_rank']}",
                ),
                gr.update(
                    visible=True,
                    value=_leaderboard_to_markdown(result.get("leaderboard", [])),
                ),
                gr.update(visible=True, value=_log_to_markdown(result.get("log", []))),
            )
        else:
            return gr.update(
                visible=True, value=f"❌ {result.get('error', 'Purchase failed')}"
            )

    def on_buy_card(card_idx: int):
        result = game_service.buy_card(card_idx)
        if result["success"]:
            cards_md = f"**Your Cards:** {', '.join(result.get('player_cards', ['None'])) or 'None'}"
            return (
                gr.update(visible=True, value=f"✅ {result['message']}"),
                gr.update(visible=True, value=cards_md),
                gr.update(
                    visible=True,
                    value=f"**Fortune:** {format_fortune(result['player_fortune'])} | **Rank:** #{result['player_rank']}",
                ),
                gr.update(
                    visible=True,
                    value=_leaderboard_to_markdown(result.get("leaderboard", [])),
                ),
                gr.update(visible=True, value=_log_to_markdown(result.get("log", []))),
            )
        else:
            return gr.update(
                visible=True, value=f"❌ {result.get('error', 'Purchase failed')}"
            )

    def on_refresh_marketplace():
        tools = game_service.get_available_tools()
        cards = game_service.get_available_cards()
        locations = game_service.get_available_locations()
        materials = game_service.get_raw_materials()
        products = game_service.get_finished_products()

        tools_md = _tools_catalog_to_markdown(tools)
        cards_md = _cards_catalog_to_markdown(cards)
        locations_md = _locations_to_markdown(locations)
        materials_md = _materials_catalog_to_markdown(materials)
        products_md = _products_catalog_to_markdown(products)

        return (
            gr.update(visible=True, value=tools_md),
            gr.update(visible=True, value=cards_md),
            gr.update(visible=True, value=locations_md),
            gr.update(visible=True, value=materials_md),
            gr.update(visible=True, value=products_md),
        )

    # Available tools catalog
    tools_options = get_tool_options()
    tools_choices = [
        f"{t['name']} (Cost: {t['cost']:,} FCFA, Capacity: {t['capacity']})"
        for t in tools_options
    ]

    # Available cards catalog
    cards_options = get_card_options()
    cards_choices = [
        f"{c['name']} - {c['description']} (Cost: {c['price']:,} FCFA, Value: {c['value']})"
        for c in cards_options
    ]

    # Raw materials catalog
    materials = game_service.get_raw_materials()
    materials_choices = [
        f"{m['name']} - {m['price']:,} FCFA (yields {m['yield']} units)"
        for m in materials
    ]

    # Finished products catalog
    products = game_service.get_finished_products()
    products_choices = [
        f"{p['name']} (from {p['raw_material']}) - sells for {p['sell_price']:,} FCFA"
        for p in products
    ]

    with gr.Column(elem_id="market-container"):
        gr.Markdown("## 🏪 KSell Entreprise - Marketplace")
        gr.Markdown(
            "Buy tools, cards, raw materials, and explore sales locations to grow your business."
        )

        refresh_btn = gr.Button(
            "🔄 Refresh Marketplace", variant="primary", elem_id="refresh-btn"
        )

        # Tools section
        with gr.Accordion("🔧 Tools (Outils)", open=True):
            with gr.Row():
                with gr.Column():
                    tools_catalog = gr.Markdown(visible=False, elem_id="tools-catalog")
                with gr.Column():
                    buy_tool_idx = gr.Dropdown(
                        choices=tools_choices,
                        label="Select Tool to Buy",
                        info="Choose a tool to enhance your transport capacity",
                    )
                    buy_tool_btn = gr.Button(
                        "🛒 Buy Tool", variant="secondary", elem_id="buy-tool-btn"
                    )

        # Cards section
        with gr.Accordion("🃏 Cards (Cartes)", open=True):
            with gr.Row():
                with gr.Column():
                    cards_catalog = gr.Markdown(visible=False, elem_id="cards-catalog")
                with gr.Column():
                    buy_card_idx = gr.Dropdown(
                        choices=cards_choices,
                        label="Select Card to Buy",
                        info="Collect cards for special abilities",
                    )
                    buy_card_btn = gr.Button(
                        "🛒 Buy Card", variant="secondary", elem_id="buy-card-btn"
                    )

        # Raw materials section
        with gr.Accordion("📦 Raw Materials", open=True):
            with gr.Row():
                with gr.Column():
                    materials_catalog = gr.Markdown(
                        visible=False, elem_id="materials-catalog"
                    )
                with gr.Column():
                    buy_material_idx = gr.Dropdown(
                        choices=materials_choices,
                        label="Select Material to Buy",
                        info="Purchase raw materials for production",
                    )
                    buy_material_qty = gr.Number(
                        label="Quantity", value=1, precision=0, minimum=1
                    )
                    buy_material_btn = gr.Button(
                        "🛒 Buy Materials",
                        variant="secondary",
                        elem_id="buy-material-btn",
                    )

        # Finished products reference
        with gr.Accordion("🏭 Finished Products Reference", open=True):
            products_catalog = gr.Markdown(visible=False, elem_id="products-catalog")

        # Locations section
        with gr.Accordion("📍 Sales Locations", open=True):
            locations_display = gr.Markdown(visible=False, elem_id="locations-display")

        # Purchase status
        purchase_status = gr.Markdown(visible=False, elem_id="purchase-status")

        # Player inventory
        player_inventory = gr.Markdown(visible=False, elem_id="player-inventory")
        player_status_market = gr.Markdown(
            visible=False, elem_id="player-status-market"
        )
        market_leaderboard = gr.Markdown(visible=False, elem_id="market-leaderboard")
        market_log = gr.Markdown(visible=False, elem_id="market-log")

        # Event handlers
        refresh_btn.click(
            fn=on_refresh_marketplace,
            inputs=[],
            outputs=[
                tools_catalog,
                cards_catalog,
                locations_display,
                materials_catalog,
                products_catalog,
            ],
        )

        buy_tool_btn.click(
            fn=on_buy_tool,
            inputs=[buy_tool_idx],
            outputs=[
                purchase_status,
                player_inventory,
                player_status_market,
                market_leaderboard,
                market_log,
            ],
        )

        buy_card_btn.click(
            fn=on_buy_card,
            inputs=[buy_card_idx],
            outputs=[
                purchase_status,
                player_inventory,
                player_status_market,
                market_leaderboard,
                market_log,
            ],
        )

        buy_material_btn.click(
            fn=on_buy_tool,  # Reuse tool purchase logic for materials
            inputs=[buy_material_idx],
            outputs=[
                purchase_status,
                player_inventory,
                player_status_market,
                market_leaderboard,
                market_log,
            ],
        )

    return buy_tool_idx, buy_card_idx, refresh_btn, buy_tool_btn, buy_card_btn


def _tools_to_markdown(tools: list) -> str:
    """Convert player's tools to markdown."""
    if not tools:
        return "You don't own any tools yet."

    md = "**🔧 Your Tools:**\n\n"
    total_cap = sum(t.get("capacity", 0) for t in tools)
    md += f"Total Capacity: {total_cap:,} units\n\n"
    for t in tools:
        md += f"- **{t.get('name', 'Unknown')}**: Capacity {t.get('capacity', 0):,} units\n"
    return md


def _tools_catalog_to_markdown(tools: list) -> str:
    """Convert tools catalog to markdown."""
    if not tools:
        return "No tools available."

    md = "**🔧 Available Tools:**\n\n"
    md += "| Tool | Cost (FCFA) | Capacity |\n"
    md += "|------|-------------|----------|\n"
    for t in tools:
        md += f"| {t['name']} | {t['cost']:,} | {t['capacity']:,} units |\n"
    return md


def _cards_to_markdown(cards: list) -> str:
    """Convert player's cards to markdown."""
    if not cards:
        return "You don't own any cards yet."

    md = "**🃏 Your Cards:**\n\n"
    for card_id in cards:
        md += f"- {card_id}\n"
    return md


def _cards_catalog_to_markdown(cards: list) -> str:
    """Convert cards catalog to markdown."""
    if not cards:
        return "No cards available."

    md = "**🃏 Available Cards:**\n\n"
    md += "| Card | Description | Value | Cost (FCFA) |\n"
    md += "|------|-------------|-------|-------------|\n"
    for c in cards:
        md += f"| {c['nom']} | {c['description']} | {c['valeur']} | {c['prix']:,} |\n"
    return md


def _materials_catalog_to_markdown(materials: list) -> str:
    """Convert raw materials catalog to markdown."""
    if not materials:
        return "No materials available."

    md = "**📦 Raw Materials:**\n\n"
    md += "| Material | Cost (FCFA) | Yield (units) | Description |\n"
    md += "|----------|-------------|---------------|-------------|\n"
    for m in materials:
        md += (
            f"| {m['nom']} | {m['prix']:,} | {m['rendement']} | {m['description']} |\n"
        )
    return md


def _products_catalog_to_markdown(products: list) -> str:
    """Convert finished products catalog to markdown."""
    if not products:
        return "No products available."

    md = "**🏭 Finished Products:**\n\n"
    md += "| Product | Raw Material | Sell Price (FCFA) | Description |\n"
    md += "|---------|--------------|-------------------|-------------|\n"
    for p in products:
        md += f"| {p['nom']} | {p['matiere_premiere']} | {p['prix_vente']:,} | {p['description']} |\n"
    return md


def _locations_to_markdown(locations: list) -> str:
    """Convert sales locations to markdown."""
    if not locations:
        return "No locations available."

    md = "**📍 Sales Locations:**\n\n"
    md += "| Location | Min Qty | Max Qty | Tax Rate |\n"
    md += "|----------|---------|---------|----------|\n"
    for l in locations:
        md += f"| {l['nom']} | {l['plage_min']} | {l['plage_max']} | {l['taux'] * 100:.1f}% |\n"
    return md


def _leaderboard_to_markdown(leaderboard: list) -> str:
    """Convert leaderboard to markdown."""
    if not leaderboard:
        return "No players yet."

    md = "**🏆 Leaderboard:**\n\n"
    md += "| Rank | Player | Balance |\n"
    md += "|------|--------|---------|\n"
    for entry in leaderboard:
        md += f"| #{entry['rank']} | {entry['username']} | {entry['balance']:,.0f} FCFA |\n"
    return md


def _log_to_markdown(log: list) -> str:
    """Convert game log to markdown."""
    if not log:
        return "No events yet."

    md = "**📜 Recent Events:**\n\n"
    for entry in log[-10:]:
        md += f"- {entry}\n"
    return md
