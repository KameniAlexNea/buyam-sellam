"""Help / Documentation Page for KSell Entreprise Gradio UI."""

import gradio as gr


def create_help_page():
    """Create the help/documentation page explaining how to play."""

    with gr.Column(elem_id="help-container"):
        gr.Markdown("## 📖 How to Play KSell Entreprise")
        gr.Markdown(
            """
            <div style="background: #07649d; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea;">
            <strong>Welcome!</strong> KSell Entreprise is a business simulation game where you manage a trading
            empire — buying raw materials, producing goods, selling in dynamic markets, and competing with
            other players to build the most prosperous business.
            </div>
            """
        )

        # --- Getting Started ---
        with gr.Accordion("🚀 Getting Started", open=True):
            gr.Markdown(
                """
                ### Step 1: Enter Your Name
                - Go to the **🏠 Home** tab.
                - Type your player name (minimum 3 characters).
                - Click **🚀 Start Game**.
                - The game initializes with 5 markets, a leaderboard, and your starting fortune (default: 10,000 FCFA).

                ### Step 2: Understand the Game Loop
                Each round follows this cycle:
                1. **Roll the dice** (2d6) → determines market conditions for the round.
                2. **Check the markets** → see demand, tax rates, and competition at each location.
                3. **Buy materials or produce goods** → invest in raw materials or finished products.
                4. **Sell at markets** → choose a market and quantity to sell your goods.
                5. **End the round** → advance to the next turn.

                Repeat until you decide to end the game!
                """
            )

        # --- Dice & Market Conditions ---
        with gr.Accordion("🎲 Dice & Market Conditions", open=False):
            gr.Markdown(
                """
                At the start of each round, you roll **2 six-sided dice**. The total determines market conditions:

                | Dice Total | Condition | Effect |
                |------------|-----------|--------|
                | 2 – 6 | 📉 **Low** | Reduced demand, lower prices — tough market |
                | 7 – 8 | ➡️ **Normal** | Standard demand and pricing |
                | 9 – 12 | 📈 **High** | Increased demand, higher prices — great market |

                **Random Events** may also trigger each round (10–15% chance):
                - 🌧️ *Heavy rain* — transportation disrupted, lose 500–2,000 FCFA
                - 🎉 *Local festival* — demand surges, gain 1,000–5,000 FCFA
                - 🚛 *Truck breakdown* — delivery delayed, lose 1,000–3,000 FCFA
                - 💰 *Government subsidy* — small business grant, gain 2,000–8,000 FCFA
                - 📦 *Supply shortage* — material prices spike temporarily
                - 🏪 *New customer* — unexpected demand boost

                These events add unpredictability and can make or break your business!
                """
            )

        # --- Markets ---
        with gr.Accordion("🏪 Markets & Trading", open=False):
            gr.Markdown(
                """
                ### How Markets Work
                The game features **5 market locations**, each with:
                - **Demand** — how many units buyers want (shown as remaining / total)
                - **Tax Rate** — percentage taken from your revenue
                - **Competition** — other players selling at the same location

                ### Selling Goods
                1. Go to the **🎮 Game** tab.
                2. In the **Markets & Trading** section, enter the **Market number** (0–4) and **Quantity** to sell.
                3. Click **💰 Sell Raw Goods at Market**.
                4. You'll see: Revenue, Tax deducted, and Net profit.

                ### Tips
                - **High-demand markets** (low remaining demand) = better prices.
                - **Low-tax markets** keep more of your profit.
                - **Avoid crowded markets** — too many sellers drive prices down.
                - Balance between selling raw goods (faster, less profit) vs. producing finished goods (slower, more profit).
                """
            )

        # --- Production ---
        with gr.Accordion("🏭 Production", open=False):
            gr.Markdown(
                """
                ### Raw Materials
                Buy raw materials to produce finished goods. Each material has a cost and yield:

                | Material | Cost (FCFA) | Yield (units) | Best For |
                |----------|-------------|---------------|----------|
                | Manioc (Cassava) | 500 | 10 | Fufu |
                | Riz brut (Raw rice) | 800 | 15 | Cooked rice |
                | Maïs (Corn) | 400 | 12 | Corn flour |
                | Arachide (Peanuts) | 600 | 8 | Peanut butter |
                | Poisson sec (Dried fish) | 1,500 | 5 | Smoked fish |
                | Huile de palme (Palm oil) | 1,000 | 20 | Refined oil |
                | Lait en poudre (Powdered milk) | 1,200 | 15 | Reconstituted milk |
                | Sucre (Sugar) | 300 | 25 | Sugar syrup |

                ### Finished Products
                Transform raw materials into higher-value products:

                | Product | From | Sell Price (FCFA) |
                |---------|------|-------------------|
                | Fufu | Manioc | 1,500 |
                | Riz cuit (Cooked rice) | Riz brut | 2,000 |
                | Farine de maïs (Corn flour) | Maïs | 1,200 |
                | Beurre de cacahuète (Peanut butter) | Arachide | 2,500 |
                | Poisson fumé (Smoked fish) | Poisson sec | 3,000 |
                | Huile raffinée (Refined oil) | Huile de palme | 1,800 |
                | Lait reconstitué (Reconstituted milk) | Lait en poudre | 1,500 |
                | Sirop de sucre (Sugar syrup) | Sucre | 800 |

                ### Production Strategy
                - **Buy materials** → they go into your inventory.
                - **Produce goods** → materials are consumed, finished products are created.
                - **Sell finished products** at markets for higher profit margins.
                - Always check your **inventory** and **capacity** before over-producing!
                """
            )

        # --- Marketplace ---
        with gr.Accordion("🛒 Marketplace (Shop)", open=False):
            gr.Markdown(
                """
                The **🏪 Marketplace** tab is your one-stop shop for everything:

                ### 🔧 Tools (Outils)
                Tools increase your **transport capacity** — the maximum units you can carry/sell per round.
                - Browse available tools and their costs.
                - Select a tool and click **🛒 Buy Tool**.
                - More capacity = sell more per round = more revenue potential.

                ### 🃏 Cards (Cartes)
                Collect special cards that grant unique abilities or bonuses.
                - Browse the card catalog.
                - Select a card and click **🛒 Buy Card**.
                - Cards can give you competitive advantages!

                ### 📍 Sales Locations
                View all available sales locations with their tax rates and characteristics.
                Choose locations with lower taxes to maximize profit.

                ### 💡 Tip
                Click **🔄 Refresh Marketplace** to see the latest catalog — inventory changes each round!
                """
            )

        # --- Profile ---
        with gr.Accordion("👤 Profile", open=False):
            gr.Markdown(
                """
                Track your progress and manage your player identity:

                ### Stats Tracked
                | Stat | Description |
                |------|-------------|
                | 💰 Fortune | Total wealth in FCFA |
                | ⭐ Stars | Performance rating |
                | 🎮 Competitions | Number of rounds played |
                | 👥 Subscribers | Followers / reputation |
                | 🃏 Cards | Cards in your collection |
                | 🔧 Tools | Tools owned |
                | 📦 Total Capacity | Combined transport capacity |
                | 🏆 Rank | Your position on the leaderboard |

                ### Profile Types
                Choose your business role:
                - **Entrepreneur** — balanced all-rounder
                - **Investisseur** — focused on high-value trades
                - **Spéculateur** — risk-taker, big wins/losses
                - **Négociant** — volume trader, steady income
                """
            )

        # --- Scoring & Winning ---
        with gr.Accordion("🏆 Scoring & Winning", open=False):
            gr.Markdown(
                """
                ### How to Win
                There is no fixed end to the game — play as many rounds as you like! The goal is to:

                1. **Maximize your fortune** — accumulate as much wealth as possible.
                2. **Climb the leaderboard** — rank #1 among all players.
                3. **Build a diversified business** — tools, cards, production, and smart trading.

                ### Ending the Game
                - Click **⏹️ End Game** in the Game tab to see final results.
                - The final report shows your fortune, rank, and key statistics.

                ### Key Strategies
                - 📈 **Buy low, sell high** — watch market conditions (dice rolls) before selling.
                - 🏭 **Produce finished goods** — higher margins than raw materials.
                - 🔧 **Invest in tools** — more capacity means more sales per round.
                - 🃏 **Collect cards** — special abilities can give you an edge.
                - 📍 **Choose markets wisely** — balance demand, tax, and competition.
                - ⚠️ **Manage risk** — random events can hurt; keep some reserves!
                """
            )

        # --- Quick Reference ---
        with gr.Accordion("⚡ Quick Reference", open=False):
            gr.Markdown(
                """
                ### Tab Overview
                | Tab | Purpose |
                |-----|---------|
                | 🏠 Home | Enter name and start the game |
                | 🎮 Game | Roll dice, sell goods, produce, manage rounds |
                | 🏪 Marketplace | Buy tools, cards, materials, view locations |
                | 👤 Profile | View stats, update profile |
                | 📖 Help | You are here! |

                ### Keyboard Shortcuts
                - **Enter** — submit text inputs
                - **Tab** — navigate between fields

                ### Currency
                All values are in **FCFA** (West African CFA Franc).

                ### Need Help?
                If something seems unclear, revisit this page or check each accordion section for detailed explanations.
                Happy trading! 🎲💰🏆
                """
            )

    return gr.Markdown()  # placeholder return
