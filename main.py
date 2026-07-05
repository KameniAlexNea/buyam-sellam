"""KSell Entreprise - Gradio Edition

A business simulation / marketplace game built with Gradio (Python).
This is the main entry point for the application.

Game Overview:
- Enter your name to start playing (local app, no real auth)
- Roll dice (2d6) to determine market conditions
- Trade products in dynamic markets with taxes and quantities
- Manage tools, cards, and fortune
- Compete with other players in a simulated economy
- Produce goods, buy supplies, and grow your business empire
"""

import gradio as gr

from services.game_service import GameService
from services.user_service import UserService
from views.game_page import create_game_page
from views.help_page import create_help_page
from views.login_page import create_login_page
from views.market_page import create_market_page
from views.profile_page import create_profile_page


def main():
    """Initialize and launch the KSell Entreprise Gradio application."""

    # Initialize services
    game_service = GameService()
    user_service = UserService()

    # Create the Gradio interface
    with gr.Blocks(
        title="KSell Entreprise",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
            margin: auto;
        }
        #login-container {
            max-width: 600px;
            margin: auto;
            padding: 20px;
        }
        #game-container, #market-container, #profile-container {
            max-width: 1200px;
            margin: auto;
        }
        .game-header {
            text-align: center;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .game-header h1 {
            margin: 0;
            font-size: 2em;
        }
        .game-header p {
            margin: 5px 0 0 0;
            opacity: 0.9;
        }
        """,
    ) as app:

        # Application header
        gr.Markdown(
            """
            <div class="game-header">
                <h1>🎲 KSell Entreprise</h1>
                <p>Business Simulation & Marketplace Game</p>
            </div>
            """,
            elem_id="app-header",
        )

        # Navigation tabs
        with gr.Tabs():
            # Tab 1: Home
            with gr.TabItem("🏠 Home"):
                create_login_page(game_service)

            # Tab 2: Game
            with gr.TabItem("🎮 Game"):
                (
                    game_username,
                    game_fortune,
                    start_btn,
                    roll_btn,
                    sell_btn,
                    end_btn,
                ) = create_game_page(game_service)

            # Tab 3: Marketplace
            with gr.TabItem("🏪 Marketplace"):
                (
                    buy_tool_idx,
                    buy_card_idx,
                    refresh_btn,
                    buy_tool_btn,
                    buy_card_btn,
                ) = create_market_page(game_service)

            # Tab 4: Profile
            with gr.TabItem("👤 Profile"):
                view_btn, update_btn = create_profile_page(game_service, user_service)

            # Tab 5: Help / Documentation
            with gr.TabItem("📖 Help"):
                create_help_page()

        # Footer
        gr.Markdown(
            """
            ---
            <div style="text-align: center; color: #666; padding: 10px;">
                <p>KSell Entreprise - Gradio Edition | Business Simulation Game</p>
                <p>Roll dice, trade in markets, produce goods, build your empire! 🎲💰🏆</p>
            </div>
            """,
            elem_id="app-footer",
        )

    # Launch the application
    print("🚀 Starting KSell Entreprise Gradio application...")
    print("📍 Open your browser and navigate to the URL shown below.")
    print("💡 Just enter your name and start playing!")
    print()

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        debug=True,
    )


if __name__ == "__main__":
    main()
