"""Login Page for KSell Entreprise Gradio UI.

Simplified for local app - no real authentication needed.
Player just enters their name and starts playing.
"""

import gradio as gr

from services.game_service import GameService


def create_login_page(game_service: GameService):
    """Create the simplified login page for local app.

    Since this is a local Gradio app, we skip real authentication.
    Player just enters their name and can start playing immediately.
    """

    with gr.Column(elem_id="login-container"):
        gr.Markdown("## 🎲 KSell Entreprise")
        gr.Markdown("### Business Simulation & Marketplace Game")
        gr.Markdown("Go to the **🎮 Game** tab to start playing!")

    return gr.Markdown()


def _markets_to_markdown(markets: list) -> str:
    """Convert markets list to markdown display."""
    if not markets:
        return "No active markets."

    md = "**📊 Active Markets:**\n\n"
    for i, m in enumerate(markets):
        location = m.get("location", {})
        md += f"**Market {i}: {location.get('name', 'Unknown')}**\n"
        md += f"  📦 Demand: {m.get('remaining_qty', 0):,} / {m.get('total_qty', 0):,} units\n"
        md += f"  💸 Tax Rate: {location.get('tax_rate', 0) * 100:.1f}%\n"
        md += f"  👥 Sellers: {', '.join(m.get('selling_players', [])) or 'None'}\n\n"
    return md


def _leaderboard_to_markdown(leaderboard: list) -> str:
    """Convert leaderboard to markdown display."""
    if not leaderboard:
        return "No players yet."

    md = "**🏆 Leaderboard:**\n\n"
    md += "| Rank | Player | Fortune | Stars | Games |\n"
    md += "|------|--------|---------|-------|-------|\n"
    for entry in leaderboard:
        md += f"| #{entry['rank']} | {entry['username']} | {entry['balance']:,.0f} FCFA | ⭐{entry['stars']} | 🎮{entry['competitions']} |\n"
    return md


def _log_to_markdown(log: list) -> str:
    """Convert game log to markdown display."""
    if not log:
        return "No game events yet."

    md = "**📜 Game Log:**\n\n"
    for entry in log[-15:]:
        md += f"- {entry}\n"
    return md
