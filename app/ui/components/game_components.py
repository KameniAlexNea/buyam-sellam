"""HTML render helpers for the Buyam-Sellam Gradio game UI."""

from __future__ import annotations

import html
from typing import Any, Iterable, List, Optional

from ksell.model.market_board import MarketBoard
from ksell.model.player import Player


PRODUCT_META = {
    "Cooked Rice": {"icon": "🍚", "tone": "amber"},
    "Fufu": {"icon": "🥘", "tone": "mint"},
    "Corn Flour": {"icon": "🌽", "tone": "gold"},
    "Peanut Butter": {"icon": "🥜", "tone": "earth"},
    "Smoked Fish": {"icon": "🐟", "tone": "blue"},
}


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def money(value: float) -> str:
    return f"{value:,.0f} FCFA"


def product_meta(product_name: str) -> dict[str, str]:
    return PRODUCT_META.get(product_name, {"icon": "box", "tone": "slate"})


def product_badge(product_name: str) -> str:
    meta = product_meta(product_name)
    return (
        f'<span class="product-badge product-{meta["tone"]}">'
        f'<span class="product-icon">{esc(meta["icon"])}</span>{esc(product_name)}</span>'
    )


def render_dice(
    total: Optional[int] = None,
    label: str = "Market dice",
    values: Optional[tuple[int, int]] = None,
) -> str:
    if total is None:
        return (
            '<div class="dice-tray is-waiting">'
            '<div class="die-face">?</div><div class="die-face">?</div>'
            f"<span>{esc(label)}</span></div>"
        )

    if values is None:
        die_one = max(1, min(6, total // 2))
        die_two = max(1, min(6, total - die_one))
    else:
        die_one, die_two = values
    return (
        '<div class="dice-tray">'
        f'<div class="die-face">{die_one}</div><div class="die-face">{die_two}</div>'
        f"<span>{esc(label)}: <strong>{total}</strong></span></div>"
    )


def render_turn_rolls(rolls: List[tuple[str, int, tuple[int, int]]]) -> str:
    if not rolls:
        return ""
    dice = "".join(
        render_dice(total, username, values) for username, total, values in rolls
    )
    return (
        '<section class="action-panel">'
        '<div><span class="eyebrow">🎲 Turn Order</span><h3>Dice Results</h3></div>'
        f'<div class="dice-strip">{dice}</div></section>'
    )


def render_status_bar(
    phase: str,
    round_number: int,
    total_rounds: int,
    human: Optional[Player],
    difficulty: Optional[str] = None,
) -> str:
    balance = money(human.balance) if human else "0 FCFA"
    phase_labels = {
        "setup": "⚙️ Setup",
        "strategy": "🧠 Strategy",
        "action": "⚡ Action",
        "round_end": "📊 Round End",
        "game_over": "🏆 Game Over",
    }
    phase_label = phase_labels.get(phase, phase.replace("_", " ").title())
    difficulty_chip = (
        f'<span class="hud-chip">🎯 {esc(difficulty)}</span>' if difficulty else ""
    )
    return (
        '<section class="hud-panel">'
        '<div><span class="eyebrow">🎲 Live Game</span>'
        f"<h2>Round {round_number} / {total_rounds}</h2></div>"
        '<div class="hud-stats">'
        f'<span class="hud-chip">{esc(phase_label)}</span>{difficulty_chip}'
        f'<span class="hud-chip balance-chip">💰 {esc(balance)}</span>'
        "</div></section>"
    )


def render_inventory(player: Optional[Player]) -> str:
    if player is None:
        return ""
    if not player.inventory:
        inventory = '<p class="empty-state">No goods in your warehouse yet.</p>'
    else:
        cards = []
        for item in player.inventory:
            cards.append(
                '<article class="inventory-card">'
                f"{product_badge(item.product.name)}"
                f"<strong>{item.quantity}</strong>"
                f"<span>Avg {item.avg_cost:,.0f}</span>"
                "</article>"
            )
        inventory = f'<div class="inventory-grid">{"".join(cards)}</div>'
    return (
        '<section class="side-panel">'
        '<div class="panel-heading"><span class="eyebrow">📦 Warehouse</span><h3>Your Stock</h3></div>'
        f"{inventory}</section>"
    )


def render_markets(markets: List[MarketBoard]) -> str:
    if not markets:
        return (
            '<section class="board-empty">'
            '<p style="font-size:3rem;margin:0 0 12px;">\U0001f3b2</p>'
            '<p class="empty-state">Hit <strong>Start Game</strong> to open the markets and begin trading.</p>'
            "</section>"
        )

    cards = []
    for idx, market in enumerate(markets, 1):
        supply_pct = (
            0
            if market.total_qty <= 0
            else int((market.market_supply / market.total_qty) * 100)
        )
        supply_pct = max(0, min(100, supply_pct))
        fee = getattr(market, "sell_entry_fee", 0)
        cards.append(
            '<article class="market-card">'
            '<div class="market-topline">'
            f'<span class="market-number">M{idx}</span>'
            f'<span class="market-name">{esc(market.location.name)}</span>'
            "</div>"
            f"{product_badge(market.location.product)}"
            '<div class="market-economy">'
            f"<div><span>Market pays</span><strong>{market.market_fixed_price:,}</strong></div>"
            f"<div><span>Entry fee</span><strong>{fee:,}</strong></div>"
            "</div>"
            '<div class="supply-line">'
            f"<span>Supply {market.market_supply}/{market.total_qty}</span>"
            f"<span>{supply_pct}%</span>"
            "</div>"
            f'<div class="supply-meter"><span style="width:{supply_pct}%"></span></div>'
            "</article>"
        )
    return '<section class="market-grid">' + "".join(cards) + "</section>"


def render_opponents(
    players: Iterable[Player], human_username: str, starting_balance: float
) -> str:
    opponents = [p for p in players if p.username != human_username]
    if not opponents:
        return ""
    rows = []
    for player in sorted(opponents, key=lambda p: p.balance, reverse=True):
        profit = player.balance - starting_balance
        sign = "+" if profit >= 0 else ""
        inventory_count = sum(item.quantity for item in player.inventory)
        rows.append(
            '<article class="opponent-card">'
            '<div class="avatar-token">AI</div>'
            '<div class="opponent-body">'
            f"<strong>{esc(player.username)}</strong>"
            f"<span>{money(player.balance)} · {sign}{profit:,.0f} P/L</span>"
            f"<small>{inventory_count} goods in stock</small>"
            "</div></article>"
        )
    return (
        '<section class="side-panel opponents-panel">'
        '<div class="panel-heading"><span class="eyebrow">🤖 Opponents</span><h3>Rival Traders</h3></div>'
        + "".join(rows)
        + "</section>"
    )


def render_strategy_help() -> str:
    return (
        '<section class="side-panel">'
        '<div class="panel-heading"><span class="eyebrow">🧠 Trade Console</span><h3>Set Your Moves</h3></div>'
        '<p class="empty-state">Pick <strong>Buy</strong>, <strong>Sell</strong>, or <strong>Skip</strong> for each open market below, then hit <strong>Play</strong> to roll.</p>'
        "</section>"
    )


def render_action_prompt(action: dict[str, Any]) -> str:
    market = action["market"]
    dice = render_dice(action.get("dice_total"), "Your roll", action.get("dice_values"))
    if action["type"] == "buy":
        body = (
            f"<p>{product_badge(market.location.product)}</p>"
            f'<div class="action-stat"><span>Dice price</span><strong>{action["dice_price"]:,}</strong></div>'
            f'<div class="action-stat"><span>Market price</span><strong>{action["market_price"]:,}</strong></div>'
            f'<div class="action-callout">You can buy up to <strong>{action["max_affordable"]}</strong> units.</div>'
        )
        title = f"🛒 Buy at {esc(market.location.name)}"
    else:
        body = (
            f"<p>{product_badge(action['product_name'])}</p>"
            f'<div class="action-stat"><span>Dice price</span><strong>{action["dice_price"]:,}</strong></div>'
            f'<div class="action-stat"><span>Market price</span><strong>{action["market_price"]:,}</strong></div>'
            f'<div class="action-stat"><span>Fee paid</span><strong>{action["entry_fee"]:,}</strong></div>'
            f'<div class="action-callout">You can sell up to <strong>{action["seller_qty"]}</strong> units.</div>'
        )
        title = f"💸 Sell at {esc(market.location.name)}"
    return (
        '<section class="action-panel">'
        f'<div><span class="eyebrow">⚡ Live Deal</span><h3>{title}</h3></div>{dice}'
        f'<div class="action-body">{body}</div></section>'
    )


def render_round_summary(summary: str) -> str:
    if not summary:
        summary = "No completed trades this round."
    lines = "".join(
        f"<li>{esc(line)}</li>" for line in summary.splitlines() if line.strip()
    )
    return (
        '<section class="action-panel">'
        '<div><span class="eyebrow">📋 Round Report</span><h3>Market Movement</h3></div>'
        f'<ul class="event-list">{lines}</ul><p class="next-copy">Press <strong>Next</strong> to continue trading.</p>'
        "</section>"
    )


def render_standings(players: List[Player], starting_balance: float) -> str:
    rows = []
    for index, player in enumerate(
        sorted(players, key=lambda p: p.balance, reverse=True), 1
    ):
        profit = player.balance - starting_balance
        sign = "+" if profit >= 0 else ""
        inventory = (
            ", ".join(
                f"{item.product.name} x{item.quantity}" for item in player.inventory
            )
            or "Empty"
        )
        rows.append(
            "<tr>"
            f"<td>{index}</td><td>{esc(player.username)}</td><td>{money(player.balance)}</td>"
            f"<td>{sign}{profit:,.0f}</td><td>{esc(inventory)}</td>"
            "</tr>"
        )
    return (
        '<section class="standings-panel"><table class="game-table">'
        "<thead><tr><th>#</th><th>Trader</th><th>Balance</th><th>P/L</th><th>Inventory</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></section>"
    )


def render_log(lines: List[str]) -> str:
    if not lines:
        return '<p class="empty-state">No events yet.</p>'
    items = []
    for line in lines[-28:]:
        cleaned = line.strip() or "-"
        items.append(f"<li>{esc(cleaned)}</li>")
    return '<ol class="timeline">' + "".join(items) + "</ol>"


def render_world_panel(
    players: Iterable[Player],
    human_username: str,
    starting_balance: float,
    extra: str = "",
) -> str:
    human = next((p for p in players if p.username == human_username), None)
    return (
        render_inventory(human)
        + render_opponents(players, human_username, starting_balance)
        + extra
    )


def render_error(error: str, content: str) -> str:
    if not error:
        return content
    return f'<div class="error-banner">{esc(error)}</div>{content}'
