"""Minimal Gradio UI for Buyam-Sellam.

Play as one player against AI opponents in the browser.

Usage:
    python -m app.gradio_ui
"""

from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from ksell.model.difficulty import Difficulty, DifficultyConfig
from ksell.model.market_board import MarketBoard, DICE_BASE
from ksell.model.player import Player
from ksell.model.table import Table
from ksell.pojo.user import User
from ksell.strategy import get_strategy, list_strategies, Strategy
from app.ui.styles import CSS, COLOR
from app.ui.components.game_components import (
    render_action_prompt,
    render_error,
    render_log,
    render_markets,
    render_round_summary,
    render_standings,
    render_status_bar,
    render_strategy_help,
    render_turn_rolls,
    render_world_panel,
)


# ---------------------------------------------------------------------------
# Game state container
# ---------------------------------------------------------------------------

MAX_MARKET_CONTROLS = 4
ACTION_CHOICES = ["Skip", "Buy", "Sell"]
ACTION_MAP = {choice: choice.lower() for choice in ACTION_CHOICES}


class GameState:
    """Mutable game state passed through Gradio callbacks via gr.State."""

    def __init__(self):
        self.table: Optional[Table] = None
        self.phase: str = "setup"  # setup | strategy | action | round_end | game_over
        self.round_number: int = 0
        self.total_rounds: int = 5
        self.difficulty: Optional[DifficultyConfig] = None
        self.markets: List[MarketBoard] = []
        self.player_strategies: Dict[str, List[Tuple[int, str]]] = {}
        self.turn_order: List[Tuple[Player, int]] = []
        self.turn_rolls: List[Tuple[str, int, Tuple[int, int]]] = []
        self.action_queue: List[Tuple[Player, int, str, MarketBoard]] = []
        self.current_action: Optional[Dict[str, Any]] = None
        self.ai_strategy: Optional[Strategy] = None
        self.human_username: str = "You"
        self.log: List[str] = []
        self.starting_balance: float = 0

    def add_log(self, msg: str):
        self.log.append(msg)


# ---------------------------------------------------------------------------
# Output tuple: 12 elements
# (state, status, content, info, log, 4 market choices, strategy_btn, qty_input, action_btn)
# ---------------------------------------------------------------------------

OUTPUTS_COUNT = 12


def _market_control_updates(state: GameState, show_strategy: bool) -> List[Any]:
    updates = []
    for idx in range(MAX_MARKET_CONTROLS):
        if show_strategy and idx < len(state.markets):
            market = state.markets[idx]
            label = f"M{idx + 1} · {market.location.name} · {market.location.product}"
            updates.append(
                gr.update(
                    visible=True,
                    interactive=True,
                    label=label,
                    value="Skip",
                    choices=ACTION_CHOICES,
                )
            )
        else:
            updates.append(gr.update(visible=False, interactive=False, value="Skip"))
    return updates


def _make_output(
    state: GameState,
    status: str,
    content: str,
    info: str,
    log_text: str,
    show_strategy: bool = False,
    show_action: bool = False,
) -> tuple:
    return (
        state,
        status,
        content,
        info,
        log_text,
        *_market_control_updates(state, show_strategy),
        gr.update(visible=show_strategy),
        gr.update(visible=show_action),
        gr.update(visible=show_action),
    )


def _determine_turn_order_with_dice(state: GameState) -> List[Tuple[Player, int]]:
    rolls: List[Tuple[Player, int, Tuple[int, int]]] = []
    for player in state.table.players:
        dice_total = state.table.roll_dice_for_player()
        dice_values = (state.table.dice.die1, state.table.dice.die2)
        rolls.append((player, dice_total, dice_values))
    rolls.sort(key=lambda item: item[1], reverse=True)
    state.turn_rolls = [
        (player.username, total, values) for player, total, values in rolls
    ]
    return [(player, total) for player, total, _ in rolls]


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


def start_game(
    n_players: int, n_rounds: int, difficulty: str, ai_strat_name: str, state: GameState
):
    """Initialize the game and advance to round 1 strategy phase."""
    state = GameState()

    diff_enum = Difficulty(difficulty)
    state.difficulty = DifficultyConfig.from_difficulty(diff_enum)
    state.total_rounds = n_rounds
    state.ai_strategy = get_strategy(ai_strat_name)
    state.starting_balance = state.difficulty.starting_balance

    # Create players
    users = [User(username="You")]
    for i in range(n_players - 1):
        users.append(User(username=f"Bot_{i + 1}"))

    players = [Player(user=u) for u in users]
    for p in players:
        p.balance = state.difficulty.starting_balance

    state.table = Table(
        players=players, total_rounds=n_rounds, difficulty=state.difficulty
    )
    state.table.generate_markets()
    state.table.initialize_player_inventory()
    state.human_username = "You"

    state.add_log(f"Game started: {n_players} players, {n_rounds} rounds, {difficulty}")
    state.add_log(f"AI: {state.ai_strategy.label}")

    return _start_round(state)


def _start_round(state: GameState):
    """Begin a new round — pick markets, show strategy UI."""
    num_markets = state.difficulty.sample_num_markets_per_round(
        len(state.table.markets)
    )
    state.markets = state.table.start_round(num_markets)
    state.round_number = state.table.current_round
    state.phase = "strategy"
    state.player_strategies = {}
    state.action_queue = []
    state.current_action = None
    state.turn_rolls = []

    state.add_log(f"\n— Round {state.round_number}/{state.total_rounds} —")

    human = state.table.get_player(state.human_username)
    status = render_status_bar(
        state.phase,
        state.round_number,
        state.total_rounds,
        human,
        state.difficulty.name,
    )
    markets_md = render_markets(state.markets)
    info = render_world_panel(
        state.table.players,
        state.human_username,
        state.starting_balance,
        render_strategy_help(),
    )
    log_text = render_log(state.log)

    return _make_output(state, status, markets_md, info, log_text, show_strategy=True)


def submit_strategy(
    market_1: str, market_2: str, market_3: str, market_4: str, state: GameState
):
    """Parse human strategy, generate AI strategies, run action phase."""
    if state.phase != "strategy":
        return _current_view(state, "Not in strategy phase.")

    human = state.table.get_player(state.human_username)
    parsed: List[Tuple[int, str]] = []
    selected_actions = [market_1, market_2, market_3, market_4]
    for idx, selected in enumerate(selected_actions[: len(state.markets)], 1):
        action = ACTION_MAP.get(selected or "Skip")
        if action == "skip":
            continue
        if action is None:
            return _current_view(
                state, "Choose Buy, Sell, or Skip for each open market."
            )
        if action == "sell":
            market = state.markets[idx - 1]
            qty = human.get_inventory_quantity(market.location.product)
            if qty <= 0:
                return _current_view(
                    state,
                    f"No {market.location.product} to sell at {market.location.name}.",
                )
        parsed.append((idx, action))

    state.player_strategies[state.human_username] = parsed
    if parsed:
        state.add_log("You: " + ", ".join(f"M{m} {a}" for m, a in parsed))
    else:
        state.add_log("You: skipped every open market")

    # AI strategies
    for player in state.table.players:
        if player.username == state.human_username:
            continue
        markets_data = [
            {
                "market_index": i + 1,
                "product": m.location.product,
                "market_fixed_price": m.market_fixed_price,
                "market_supply": m.market_supply,
                "name": m.location.name,
            }
            for i, m in enumerate(state.markets)
        ]
        players_data = [
            {
                "username": p.username,
                "balance": p.balance,
                "inventory": [
                    {
                        "product": {"name": it.product.name, "price": it.product.price},
                        "quantity": it.quantity,
                        "avg_cost": it.avg_cost,
                    }
                    for it in p.inventory
                ],
            }
            for p in state.table.players
        ]
        ai_strat = state.ai_strategy.choose_strategy(
            markets_data, players_data, player.username
        )
        state.player_strategies[player.username] = ai_strat
        state.add_log(
            f"{player.username}: " + ", ".join(f"M{m}-{a}" for m, a in ai_strat)
        )

    # Turn order
    state.turn_order = _determine_turn_order_with_dice(state)
    state.add_log(
        "Order: " + ", ".join(f"{p.username}({d})" for p, d in state.turn_order)
    )

    # Build action queue
    state.action_queue = []
    for player, _ in state.turn_order:
        strategies = state.player_strategies.get(player.username, [])
        for market_num, action in strategies:
            if action == "skip":
                continue
            market = state.markets[market_num - 1]
            state.action_queue.append((player, market_num, action, market))

    return _process_next_action(state)


def _process_next_action(state: GameState):
    """Process actions in queue. Pause when human needs to input quantity."""
    while state.action_queue:
        player, market_num, action, market = state.action_queue[0]

        dice_total = state.table.roll_dice_for_player()
        dice_values = (state.table.dice.die1, state.table.dice.die2)
        dice_price = dice_total * DICE_BASE

        if action == "buy":
            result = state.table.process_market_action_buy(player, market, dice_total)
            if not result["success"] or not result.get("can_buy"):
                name = (
                    "You"
                    if player.username == state.human_username
                    else player.username
                )
                market_price = result.get("market_price", market.market_fixed_price)
                state.add_log(
                    f"✗ {name} @ {market.location.name}: rolled {dice_total} "
                    f"(={dice_price}) < market price {market_price} — buy blocked"
                )
                state.action_queue.pop(0)
                continue

            if player.username == state.human_username:
                state.phase = "action"
                state.current_action = {
                    "type": "buy",
                    "player": player,
                    "market": market,
                    "dice_total": dice_total,
                    "dice_price": dice_price,
                    "dice_values": dice_values,
                    "max_affordable": result["max_affordable"],
                    "market_price": result["market_price"],
                }
                return _show_action_prompt(state)

            # AI
            ai_state = {"max_affordable": result["max_affordable"], "seller_qty": 0}
            qty = state.ai_strategy.choose_buy_quantity(ai_state)
            exec_result = state.table.execute_buy_at_market_price(player, market, qty)
            if exec_result["success"]:
                state.add_log(
                    f"{player.username} bought {exec_result['units_bought']} "
                    f"{market.location.product} @{exec_result['avg_price']}"
                )
            else:
                state.add_log(
                    f"{player.username} @ {market.location.name}: buy exec failed"
                )
            state.action_queue.pop(0)

        elif action == "sell":
            fee_result = state.table.pay_sell_entry_fee(player, market)
            if not fee_result["success"]:
                state.add_log(f"{player.username}: can't pay entry fee")
                state.action_queue.pop(0)
                continue

            result = state.table.process_market_action_sell(player, market, dice_total)
            if not result["success"] or not result.get("can_sell"):
                name = (
                    "You"
                    if player.username == state.human_username
                    else player.username
                )
                market_price = result.get("market_price", market.market_fixed_price)
                if "don't have" in result.get("error", ""):
                    state.add_log(
                        f"✗ {name} @ {market.location.name}: no stock to sell"
                    )
                else:
                    state.add_log(
                        f"✗ {name} @ {market.location.name}: rolled {dice_total} "
                        f"(={dice_price}) > market price {market_price} — sell blocked"
                    )
                state.action_queue.pop(0)
                continue

            if player.username == state.human_username:
                state.phase = "action"
                state.current_action = {
                    "type": "sell",
                    "player": player,
                    "market": market,
                    "dice_total": dice_total,
                    "dice_price": dice_price,
                    "dice_values": dice_values,
                    "seller_qty": result["seller_qty"],
                    "market_price": result["market_price"],
                    "product_name": result["product_name"],
                    "entry_fee": fee_result["fee"],
                }
                return _show_action_prompt(state)

            # AI
            ai_state = {"seller_qty": result["seller_qty"], "max_affordable": 0}
            qty = state.ai_strategy.choose_sell_quantity(ai_state)
            exec_result = state.table.execute_market_auto_buy(
                player, market, qty, dice_price
            )
            if exec_result["success"]:
                state.add_log(
                    f"{player.username} sold {exec_result['quantity_sold']} "
                    f"{market.location.product} @{dice_price}"
                )
            state.action_queue.pop(0)

    return _end_round(state)


def _format_round_summary(state: GameState) -> str:
    """Build a short summary of what happened during the action phase."""
    # Last N log entries from this round (after the strategy lines)
    summary_lines = []
    for line in reversed(state.log):
        if line.startswith("— Round") or line.startswith("Order:"):
            break
        if line.strip():
            summary_lines.append(line)
    summary_lines.reverse()
    return "\n".join(summary_lines[-8:]) if summary_lines else ""


def _show_action_prompt(state: GameState):
    """Show UI for human quantity input."""
    act = state.current_action
    human = act["player"]
    # market = act["market"]

    status = render_status_bar(
        state.phase,
        state.round_number,
        state.total_rounds,
        human,
        state.difficulty.name,
    )
    markets_md = render_markets(state.markets)
    info = (
        render_turn_rolls(state.turn_rolls)
        + render_action_prompt(act)
        + render_world_panel(
            state.table.players,
            state.human_username,
            state.starting_balance,
        )
    )

    log_text = render_log(state.log)
    return _make_output(state, status, markets_md, info, log_text, show_action=True)


def submit_action(qty_input: int, state: GameState):
    """Execute the human's buy/sell quantity and continue processing."""
    if state.phase != "action" or not state.current_action:
        return _current_view(state, "No action pending.")

    act = state.current_action
    player = act["player"]
    market = act["market"]
    quantity = max(1, int(qty_input))

    if act["type"] == "buy":
        quantity = min(quantity, act["max_affordable"])
        exec_result = state.table.execute_buy_at_market_price(player, market, quantity)
        if exec_result["success"]:
            state.add_log(
                f"You bought {exec_result['units_bought']} {market.location.product} "
                f"@{exec_result['avg_price']} (tax:{exec_result['buy_tax']:.0f})"
            )
        else:
            state.add_log(f"Buy failed: {exec_result.get('error', '?')}")
    else:
        quantity = min(quantity, act["seller_qty"])
        dice_price = act["dice_price"]
        exec_result = state.table.execute_market_auto_buy(
            player, market, quantity, dice_price
        )
        if exec_result["success"]:
            state.add_log(
                f"You sold {exec_result['quantity_sold']} {act['product_name']} "
                f"@{dice_price} (net:{exec_result['net_revenue']:.0f})"
            )
        else:
            state.add_log(f"Sell failed: {exec_result.get('error', '?')}")

    state.current_action = None
    state.action_queue.pop(0)
    return _process_next_action(state)


def _end_round(state: GameState):
    """End current round, show standings or game over."""
    purchases = state.table.end_round(state.markets)
    for p in purchases:
        state.add_log(f"Market bought {p['quantity']} units @{p['purchase_price']}")

    if state.round_number >= state.total_rounds:
        state.phase = "game_over"
        state.add_log("\n=== GAME OVER ===")
        winner = sorted(state.table.players, key=lambda p: p.balance, reverse=True)[0]
        state.add_log(f"Winner: {winner.username}!")
    else:
        state.phase = "round_end"

    return _current_view(state)


def next_round(state: GameState):
    """Advance to next round."""
    if state.phase == "game_over":
        return _current_view(state)
    if state.phase != "round_end":
        return _current_view(state, "Finish the current phase first!")
    return _start_round(state)


def _current_view(state: GameState, error: str = ""):
    """Render the current state without changing phase."""
    human = state.table.get_player(state.human_username) if state.table else None

    if state.phase == "game_over":
        status = render_status_bar(
            state.phase,
            state.round_number,
            state.total_rounds,
            human,
            state.difficulty.name,
        )
        content = render_standings(state.table.players, state.starting_balance)
        winner = sorted(state.table.players, key=lambda p: p.balance, reverse=True)[0]
        info = (
            '<section class="action-panel">'
            f'<div><span class="eyebrow">🏆 Final Bell</span><h3>{winner.username} wins!</h3></div>'
            + render_world_panel(
                state.table.players, state.human_username, state.starting_balance
            )
            + "</section>"
        )
    elif state.phase == "round_end":
        status = render_status_bar(
            state.phase,
            state.round_number,
            state.total_rounds,
            human,
            state.difficulty.name,
        )
        content = render_standings(state.table.players, state.starting_balance)
        summary = _format_round_summary(state)
        info = (
            render_turn_rolls(state.turn_rolls)
            + render_round_summary(summary)
            + render_world_panel(
                state.table.players,
                state.human_username,
                state.starting_balance,
            )
        )
    else:
        difficulty = state.difficulty.name if state.difficulty else None
        status = render_status_bar(
            state.phase, state.round_number, state.total_rounds, human, difficulty
        )
        content = render_markets(state.markets)
        info = (
            render_world_panel(
                state.table.players,
                state.human_username,
                state.starting_balance,
                render_strategy_help() if state.phase == "strategy" else "",
            )
            if state.table
            else ""
        )

    if error:
        info = render_error(error, info)

    log_text = render_log(state.log)
    show_strategy = state.phase == "strategy"
    show_action = state.phase == "action"

    return _make_output(
        state, status, content, info, log_text, show_strategy, show_action
    )


# ---------------------------------------------------------------------------
# UI Layout
# ---------------------------------------------------------------------------


def build_ui() -> gr.Blocks:
    strategy_choices = [label for label, _ in list_strategies()]

    with gr.Blocks(
        title="Buyam-Sellam",
        head=(
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;600;700&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">'
        ),
    ) as app:
        state = gr.State(GameState())

        gr.HTML(
            '<div class="app-shell">'
            '<section class="hero-banner">'
            '<span class="eyebrow">🎲 Trading Board Game</span>'
            "<h1>BUYAM-SELLAM</h1>"
            "<p>Roll the dice. Read the markets. Outbid your rivals. Stack your balance and become the ultimate trader.</p>"
            "</section>"
            "</div>"
        )

        # --- Setup row ---
        with gr.Row(elem_classes=["setup-panel", "control-row"]):
            n_players = gr.Slider(2, 6, value=3, step=1, label="Players", scale=1)
            n_rounds = gr.Slider(1, 15, value=5, step=1, label="Rounds", scale=1)
            difficulty = gr.Dropdown(
                ["easy", "medium", "hard"], value="medium", label="Difficulty", scale=1
            )
            ai_strat = gr.Dropdown(
                strategy_choices, value="Random", label="AI Strategy", scale=1
            )
            start_btn = gr.Button(
                "⚔️ Start Game",
                variant="primary",
                scale=0,
                elem_classes=["action-button"],
            )

        # --- Status bar ---
        status_md = gr.HTML("")

        # --- Main content: markets + info side by side ---
        with gr.Row():
            content_md = gr.HTML("", scale=3)
            info_md = gr.HTML("", scale=2)

        # --- Input area: market choices OR action (never both) ---
        with gr.Column(elem_classes=["trade-panel"]):
            with gr.Row():
                market_choice_1 = gr.Radio(
                    ACTION_CHOICES,
                    value="Skip",
                    label="M1",
                    visible=False,
                    elem_classes=["trade-control"],
                    scale=1,
                )
                market_choice_2 = gr.Radio(
                    ACTION_CHOICES,
                    value="Skip",
                    label="M2",
                    visible=False,
                    elem_classes=["trade-control"],
                    scale=1,
                )
            with gr.Row():
                market_choice_3 = gr.Radio(
                    ACTION_CHOICES,
                    value="Skip",
                    label="M3",
                    visible=False,
                    elem_classes=["trade-control"],
                    scale=1,
                )
                market_choice_4 = gr.Radio(
                    ACTION_CHOICES,
                    value="Skip",
                    label="M4",
                    visible=False,
                    elem_classes=["trade-control"],
                    scale=1,
                )
            strategy_btn = gr.Button(
                "🎲 Play Round",
                visible=False,
                variant="primary",
                scale=0,
                elem_classes=["action-button"],
            )

        with gr.Row(elem_classes=["control-row"]):
            qty_input = gr.Number(
                label="Quantity",
                value=1,
                minimum=1,
                precision=0,
                visible=False,
                scale=1,
                elem_classes=["deal-control"],
            )
            action_btn = gr.Button(
                "💰 Deal",
                visible=False,
                variant="primary",
                scale=0,
                elem_classes=["action-button"],
            )

        # --- Next round button ---
        next_btn = gr.Button("▶ Next Round", size="sm", elem_classes=["action-button"])

        # --- Log ---
        with gr.Accordion("📜 Market Timeline", open=False):
            log_md = gr.HTML("")

        # --- Wiring ---
        market_choices = [
            market_choice_1,
            market_choice_2,
            market_choice_3,
            market_choice_4,
        ]
        outputs = [
            state,
            status_md,
            content_md,
            info_md,
            log_md,
            *market_choices,
            strategy_btn,
            qty_input,
            action_btn,
        ]

        start_btn.click(
            start_game,
            inputs=[n_players, n_rounds, difficulty, ai_strat, state],
            outputs=outputs,
        )
        strategy_btn.click(
            submit_strategy, inputs=[*market_choices, state], outputs=outputs
        )
        action_btn.click(submit_action, inputs=[qty_input, state], outputs=outputs)
        next_btn.click(next_round, inputs=[state], outputs=outputs)

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = build_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.amber,
            secondary_hue=gr.themes.colors.blue,
            neutral_hue=gr.themes.colors.slate,
            font=gr.themes.GoogleFont("Chakra Petch"),
        ).set(**COLOR),
        css=CSS,
    )
