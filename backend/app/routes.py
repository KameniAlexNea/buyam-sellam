"""FastAPI routes for the Buyam-Sellam game API.

State machine:
  CREATED → SETUP → ROUND_START → STRATEGY → TURN_ORDER → ACTION → END_ROUND
                                                                    ↓
                                                    (back to ROUND_START or GAME_OVER)

The Table object is kept in-memory per game.  After every state transition
the full state is flushed to out/{game_id}/state.json.
"""

from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, HTTPException

from ksell.model.difficulty import (
    Difficulty,
    DifficultyConfig,
    allowed_bot_strategies,
    pick_bot_strategy,
)
from ksell.model.market_board import MarketBoard, DICE_BASE
from ksell.model.player import Player
from ksell.model.product import ProductModel
from ksell.model.table import Table
from ksell.pojo.user import User
from ksell.strategy import get_strategy
from ksell.utils.random_utils import uniform_int_range

from app.schemas import (
    Action,
    ActionResultResponse,
    BotActionRequest,
    BotStrategyRequest,
    CreateGameRequest,
    ExecuteActionRequest,
    GameListEntry,
    GameListResponse,
    GameStateResponse,
    GamePhase,
    MarketInfoResponse,
    PlayerInfoResponse,
    SubmitStrategyRequest,
    AddPlayerRequest,
)
from app.state_manager import (
    append_history,
    create_game_dir,
    delete_game,
    list_games,
    load_history,
    load_state,
    new_game_id,
    save_state,
    _now,
)

# ---------------------------------------------------------------------------
# In-memory game registry
# ---------------------------------------------------------------------------

# game_id → Table
_tables: Dict[str, Table] = {}

# game_id → metadata dict (phase, round, strategies, turn_order, etc.)
_meta: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/games", tags=["games"])


def _product_to_dict(pm: ProductModel) -> Dict[str, Any]:
    """Serialize a ProductModel to a plain dict."""
    return {
        "product": {
            "name": pm.product.name,
            "price": pm.product.price,
        },
        "quantity": pm.quantity,
        "avg_cost": pm.avg_cost,
    }


def _player_info(p: Player) -> PlayerInfoResponse:
    return PlayerInfoResponse(
        username=p.username,
        balance=p.balance,
        inventory=[_product_to_dict(item) for item in p.inventory],
    )


def _market_info(idx: int, m: MarketBoard) -> MarketInfoResponse:
    return MarketInfoResponse(
        market_index=idx,
        name=m.location.name,
        product=m.location.product,
        market_fixed_price=m.market_fixed_price,
        market_supply=m.market_supply,
        tax_rate=m.location.tax_rate,
        sell_entry_fee=m.sell_entry_fee,
        capacity=m.total_qty,
        price_history=m.price_history,
    )


def _game_state(game_id: str) -> GameStateResponse:
    """Build a GameStateResponse from the in-memory Table + metadata."""
    table = _tables[game_id]
    meta = _meta[game_id]
    markets = meta.get("active_markets", [])
    return GameStateResponse(
        game_id=game_id,
        phase=GamePhase(meta["phase"]),
        round_number=meta.get("round_number", table.current_round),
        total_rounds=table.total_rounds,
        difficulty=meta.get("difficulty", "medium"),
        players=[_player_info(p) for p in table.players],
        player_roles=meta.get("player_roles", {}),
        markets=[_market_info(i, m) for i, m in enumerate(markets, 1)],
        turn_order=meta.get("turn_order"),
        current_player=meta.get("current_player"),
        current_market_index=meta.get("current_market_index"),
        strategies_submitted=meta.get("strategies_submitted", []),
        dice_total=meta.get("dice_total"),
        dice_price=meta.get("dice_price"),
        can_buy=meta.get("can_buy"),
        can_sell=meta.get("can_sell"),
        max_affordable=meta.get("max_affordable"),
        seller_qty=meta.get("seller_qty"),
        action_failed=meta.get("action_failed"),
        action_fail_reason=meta.get("action_fail_reason"),
        move_feed=meta.get("move_feed", []),
        round_recap=meta.get("round_recap"),
        news=meta.get("news", []),
        message=meta.get("message", ""),
    )


# ---------------------------------------------------------------------------
# Persistence: full serialize/deserialize so games can be lazily restored
# from disk on first access (games survive backend restarts).
# ---------------------------------------------------------------------------


def _serialize_player(p: Player) -> Dict[str, Any]:
    return {
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


def _deserialize_player(data: Dict[str, Any]) -> Player:
    from ksell.pojo.product import Product as _P  # noqa: PLC0415

    user = User(username=data.get("username", ""))
    player = Player(user=user)
    player.balance = data.get("balance", 0.0)
    for item in data.get("inventory", []):
        prod = item.get("product", {})
        pm = ProductModel(
            product=_P(name=prod.get("name", ""), price=prod.get("price", 0)),
            quantity=item.get("quantity", 0),
            avg_cost=item.get("avg_cost", 0.0),
        )
        player.inventory.append(pm)
    return player


def _serialize_market(m: MarketBoard) -> Dict[str, Any]:
    return {
        "location": {
            "id": m.location.id,
            "name": m.location.name,
            "min_qty": m.location.min_qty,
            "max_qty": m.location.max_qty,
            "tax_rate": m.location.tax_rate,
            "product": m.location.product,
            "fixed_price": m.location.fixed_price,
        },
        "market_fixed_price": m.market_fixed_price,
        "last_purchase_price": m.last_purchase_price,
        "pending_market_purchase": m.pending_market_purchase,
        "price_history": m.price_history,
        "net_flow": m.net_flow,
        "market_supply": m.market_supply,
        "sell_orders": m.sell_orders,
        "completed_trades": m.completed_trades,
        "selling_players": m.selling_players,
        "total_qty": m.total_qty,
        "remaining_qty": m.remaining_qty,
        "passing_players": m.passing_players,
    }


def _deserialize_market(data: Dict[str, Any]) -> MarketBoard:
    from ksell.pojo.market import Market as _Market  # noqa: PLC0415

    loc_data = data.get("location", {})
    loc = _Market(
        id=loc_data.get("id", ""),
        name=loc_data.get("name", ""),
        min_qty=loc_data.get("min_qty", 50),
        max_qty=loc_data.get("max_qty", 200),
        tax_rate=loc_data.get("tax_rate", 0.05),
        product=loc_data.get("product", ""),
        fixed_price=loc_data.get("fixed_price", 1000),
    )
    m = MarketBoard(location=loc)
    m.market_fixed_price = data.get("market_fixed_price", loc.fixed_price)
    m.last_purchase_price = data.get("last_purchase_price")
    m.pending_market_purchase = data.get("pending_market_purchase")
    m.price_history = data.get("price_history", [m.market_fixed_price])
    m.net_flow = data.get("net_flow", 0)
    m.market_supply = data.get("market_supply", 0)
    m.sell_orders = data.get("sell_orders", [])
    m.completed_trades = data.get("completed_trades", [])
    m.selling_players = data.get("selling_players", [])
    m.total_qty = data.get("total_qty", m.market_supply)
    m.remaining_qty = data.get("remaining_qty", m.total_qty)
    m.passing_players = data.get("passing_players", [])
    m.product = loc.product
    return m


def _serialize_game(game_id: str, table: Table, meta: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize the full in-memory game so it can be restored later."""
    active_markets = meta.get("active_markets", [])
    return {
        "game_id": game_id,
        "phase": meta["phase"],
        "round_number": meta.get("round_number", table.current_round),
        "total_rounds": table.total_rounds,
        "difficulty": meta.get("difficulty", "medium"),
        "starting_balance": meta.get("starting_balance", 0),
        "players": [_serialize_player(p) for p in table.players],
        "player_roles": meta.get("player_roles", {}),
        "player_strategies": meta.get("player_strategies", {}),
        "strategies_submitted": meta.get("strategies_submitted", []),
        "turn_order": meta.get("turn_order"),
        "current_player": meta.get("current_player"),
        "current_market_index": meta.get("current_market_index"),
        "action_index": meta.get("action_index", 0),
        "player_actions_done": meta.get("player_actions_done", {}),
        "dice_total": meta.get("dice_total"),
        "dice_price": meta.get("dice_price"),
        "can_buy": meta.get("can_buy"),
        "can_sell": meta.get("can_sell"),
        "max_affordable": meta.get("max_affordable"),
        "seller_qty": meta.get("seller_qty"),
        "action_failed": meta.get("action_failed"),
        "action_fail_reason": meta.get("action_fail_reason"),
        "message": meta.get("message", ""),
        "move_feed": meta.get("move_feed", []),
        "round_history": meta.get("round_history", []),
        "round_recap": meta.get("round_recap"),
        "news": meta.get("news", []),
        "spoiled_inventory": meta.get("spoiled_inventory", {}),
        "created_at": meta.get("created_at", ""),
        "current_round": table.current_round,
        "markets": [_serialize_market(m) for m in table.markets],
        "active_market_indexes": [
            table.markets.index(m) for m in active_markets if m in table.markets
        ],
    }


def _deserialize_game(state: Dict[str, Any]) -> Tuple[Table, Dict[str, Any]]:
    """Rebuild a Table + meta from a persisted state dict."""
    diff = None
    if state.get("difficulty"):
        diff = DifficultyConfig.from_difficulty(Difficulty(state["difficulty"]))
    table = Table(
        total_rounds=state.get("total_rounds", 10),
        difficulty=diff,
    )
    table.current_round = state.get("current_round", state.get("round_number", 0))
    table.markets = [_deserialize_market(m) for m in state.get("markets", [])]
    for pd in state.get("players", []):
        table.add_player(_deserialize_player(pd))

    active_markets = [
        table.markets[i]
        for i in state.get("active_market_indexes", [])
        if 0 <= i < len(table.markets)
    ]
    meta: Dict[str, Any] = {
        "phase": state.get("phase", "created"),
        "round_number": state.get("round_number", table.current_round),
        "total_rounds": table.total_rounds,
        "starting_balance": state.get("starting_balance", 0),
        "difficulty": state.get("difficulty", "medium"),
        "strategies_submitted": state.get("strategies_submitted", []),
        "player_strategies": state.get("player_strategies", {}),
        "player_roles": state.get("player_roles", {}),
        "turn_order": state.get("turn_order"),
        "current_player": state.get("current_player"),
        "current_market_index": state.get("current_market_index"),
        "action_index": state.get("action_index", 0),
        "player_actions_done": state.get("player_actions_done", {}),
        "dice_total": state.get("dice_total"),
        "dice_price": state.get("dice_price"),
        "can_buy": state.get("can_buy"),
        "can_sell": state.get("can_sell"),
        "max_affordable": state.get("max_affordable"),
        "seller_qty": state.get("seller_qty"),
        "action_failed": state.get("action_failed"),
        "action_fail_reason": state.get("action_fail_reason"),
        "message": state.get("message", ""),
        "move_feed": state.get("move_feed", []),
        "round_history": state.get("round_history", []),
        "round_recap": state.get("round_recap"),
        "news": state.get("news", []),
        "spoiled_inventory": state.get("spoiled_inventory", {}),
        "created_at": state.get("created_at", ""),
        "active_markets": active_markets,
    }
    return table, meta


def _ensure_loaded(game_id: str) -> None:
    """Lazily load a game from disk into memory if it isn't already there.

    This is what makes games survive a backend restart: the first request that
    touches a game reads its state.json and rebuilds the in-memory Table. Games
    that were never persisted (or were deleted) stay 404.
    """
    if game_id in _tables:
        return
    state = load_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    try:
        table, meta = _deserialize_game(state)
    except Exception:
        raise HTTPException(status_code=404, detail="Game state is unreadable")
    _tables[game_id] = table
    _meta[game_id] = meta


def _flush(game_id: str) -> None:
    """Persist the current in-memory state to disk."""
    table = _tables[game_id]
    meta = _meta[game_id]
    save_state(game_id, _serialize_game(game_id, table, meta))


def _check_phase(game_id: str, *allowed: GamePhase) -> None:
    """Raise 400 if the game is not in one of the allowed phases."""
    if _meta[game_id]["phase"] not in {a.value for a in allowed}:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action in phase '{_meta[game_id]['phase']}'. "
            f"Expected one of: {[a.value for a in allowed]}",
        )


def _record_move(game_id: str, **fields: Any) -> None:
    """Append an action step to the game's move feed (for UI replay).

    Each entry is a small dict describing one visible step: who, what action,
    on which market, the dice, the quantity, the money moved, and the player's
    resulting balance. The frontend renders the tail of this feed so bot turns
    are visible instead of happening silently.
    """
    meta = _meta[game_id]
    feed = meta.setdefault("move_feed", [])
    feed.append({"round": meta.get("round_number", 0), **fields})
    # Keep the feed bounded (last ~80 steps) so it never grows unboundedly.
    if len(feed) > 80:
        del feed[:-80]


# ---------------------------------------------------------------------------
# Game lifecycle
# ---------------------------------------------------------------------------


@router.post("", summary="Create a new game")
def create_game(req: CreateGameRequest):
    game_id = new_game_id()
    create_game_dir(game_id)

    # Resolve difficulty config
    difficulty = DifficultyConfig.from_difficulty(Difficulty(req.difficulty.value))

    _tables[game_id] = Table(
        total_rounds=req.total_rounds,
        difficulty=difficulty,
    )
    _meta[game_id] = {
        "phase": GamePhase.CREATED.value,
        "round_number": 0,
        "total_rounds": req.total_rounds,
        "starting_balance": difficulty.starting_balance,
        "difficulty": req.difficulty.value,
        "strategies_submitted": [],
        "player_strategies": {},
        "player_roles": {},
        "turn_order": [],
        "current_player": None,
        "current_market_index": None,
        "action_index": 0,
        "move_feed": [],
        "round_recap": None,
        "news": [],
        "created_at": _now(),
        "message": "Game created. Add players with POST /games/{id}/players",
    }
    append_history(
        game_id,
        "game_created",
        {
            "total_rounds": req.total_rounds,
            "difficulty": req.difficulty.value,
            "starting_balance": difficulty.starting_balance,
        },
    )
    return _game_state(game_id)


@router.get("", summary="List all games")
def list_games_endpoint() -> GameListResponse:
    return GameListResponse(games=[GameListEntry(**g) for g in list_games()])


@router.get("/{game_id}", summary="Get game state")
def get_game(game_id: str) -> GameStateResponse:
    _ensure_loaded(game_id)
    return _game_state(game_id)


@router.delete("/{game_id}", summary="Delete a game")
def delete_game_endpoint(game_id: str):
    _ensure_loaded(game_id)
    del _tables[game_id]
    del _meta[game_id]
    delete_game(game_id)
    return {"deleted": game_id}


# ---------------------------------------------------------------------------
# Setup phase
# ---------------------------------------------------------------------------


@router.post("/{game_id}/players", summary="Add a player")
def add_player(game_id: str, req: AddPlayerRequest):
    _ensure_loaded(game_id)
    _check_phase(game_id, GamePhase.CREATED, GamePhase.SETUP)
    table = _tables[game_id]

    if any(p.username == req.username for p in table.players):
        raise HTTPException(
            status_code=400, detail=f"Player '{req.username}' already exists"
        )

    user = User(username=req.username)
    player = Player(user=user)
    player.balance = _meta[game_id]["starting_balance"]
    table.add_player(player)

    # Record whether this player is a human or an AI bot (and its strategy).
    # Bots are assigned a strategy from the DIFFICULTY's allowed pool, so the
    # level decides which brains can sit at the table (Easy only gets weak
    # bots; Hard only the probability-aware ones). A strategy outside the
    # level's pool is silently replaced — the roster is the source of truth.
    role = req.role if req.role in {"human", "bot"} else "human"
    strategy = req.strategy
    if role == "bot":
        diff = Difficulty(_meta[game_id]["difficulty"])
        allowed = set(allowed_bot_strategies(diff))
        if strategy not in allowed:
            strategy = pick_bot_strategy(diff)
    _meta[game_id]["player_roles"][req.username] = {
        "role": role,
        "strategy": strategy,
    }

    if _meta[game_id]["phase"] == GamePhase.CREATED.value:
        _meta[game_id]["phase"] = GamePhase.SETUP.value

    _meta[game_id]["message"] = f"Player '{req.username}' added. "
    if len(table.players) < 2:
        _meta[game_id]["message"] += "Add at least one more player to start."
    else:
        _meta[game_id]["message"] += "Ready to start with POST /games/{id}/start"

    _flush(game_id)
    append_history(game_id, "player_added", {"username": req.username})
    return _game_state(game_id)


@router.post("/{game_id}/start", summary="Start the game")
def start_game(game_id: str):
    _ensure_loaded(game_id)
    _check_phase(game_id, GamePhase.SETUP)
    table = _tables[game_id]

    if len(table.players) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 players to start")

    table.generate_markets()
    table.initialize_player_inventory()

    # Start round 1
    _start_new_round(game_id)

    _flush(game_id)
    append_history(
        game_id, "game_started", {"players": [p.username for p in table.players]}
    )
    return _game_state(game_id)


# ---------------------------------------------------------------------------
# Round start → Strategy phase
# ---------------------------------------------------------------------------


def _start_new_round(game_id: str):
    """Start a new round: pick markets, transition to STRATEGY phase."""
    table = _tables[game_id]
    meta = _meta[game_id]

    # Use difficulty config for number of markets, or fall back to default
    if table.difficulty is not None:
        num_markets = table.difficulty.sample_num_markets_per_round(len(table.markets))
    else:
        num_markets = uniform_int_range(1, min(3, len(table.markets)))

    markets = table.start_round(num_markets)

    meta["phase"] = GamePhase.STRATEGY.value
    meta["round_number"] = table.current_round
    meta["active_markets"] = markets
    meta["strategies_submitted"] = []
    meta["player_strategies"] = {}
    meta["action_failed"] = None
    meta["action_fail_reason"] = None
    meta["round_recap"] = None  # clear the previous round's recap
    meta["news"] = _build_news(markets)
    meta["message"] = (
        f"Round {table.current_round} started. {num_markets} markets active. Submit strategies."
    )

    _flush(game_id)


def _build_news(markets: List[MarketBoard]) -> List[Dict[str, Any]]:
    """Build market-news headlines from this round's price moves.

    Each active market's price_history holds the previous round's price and the
    new one (after volatility/net-flow). We surface the biggest movers as short
    ticker headlines so the board feels alive and hint at strategy.
    """
    items: List[Dict[str, Any]] = []
    for m in markets:
        hist = m.price_history
        prev = hist[-2] if len(hist) >= 2 else None
        cur = m.market_fixed_price
        pct = ((cur - prev) / prev * 100) if prev else 0.0
        tone = "up" if pct >= 5 else "down" if pct <= -5 else "flat"
        if tone != "flat":
            items.append(
                {
                    "product": m.product,
                    "market": m.location.name,
                    "pct": round(pct, 1),
                    "tone": tone,
                    "text": (
                        f"{m.product} {'surges' if pct > 0 else 'slumps'} "
                        f"{abs(pct):.0f}% at {m.location.name}"
                    ),
                }
            )
    if not items:
        items.append(
            {
                "product": None,
                "market": None,
                "pct": 0,
                "tone": "flat",
                "text": "Markets calm — prices holding steady this round.",
            }
        )
    return items


def _validate_strategy(
    game_id: str, username: str, entries: List[dict]
) -> List[tuple]:
    """Validate a strategy payload and return parsed (market_index, action) tuples."""
    table = _tables[game_id]
    meta = _meta[game_id]
    markets = meta["active_markets"]

    player = table.get_player(username)
    if not player:
        raise HTTPException(status_code=404, detail=f"Player '{username}' not found")

    parsed: List[tuple] = []
    for entry in entries:
        mi = entry["market_index"]
        action = entry["action"]
        if not (1 <= mi <= len(markets)):
            raise HTTPException(
                status_code=400,
                detail=f"Market index {mi} out of range (1-{len(markets)})",
            )
        if action not in {Action.BUY.value, Action.SELL.value, Action.SKIP.value}:
            raise HTTPException(status_code=400, detail=f"Invalid action '{action}'")
        # Validate sell: player must have the product
        if action == Action.SELL.value:
            market = markets[mi - 1]
            if player.get_inventory_quantity(market.location.product) <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"You don't have {market.location.product} to sell in market {mi}",
                )
        parsed.append((mi, action))
    return parsed


def _apply_submitted_strategy(
    game_id: str, username: str, parsed: List[tuple]
) -> None:
    """Record a strategy and advance to the ACTION phase once all players submitted."""
    table = _tables[game_id]
    meta = _meta[game_id]

    meta["player_strategies"][username] = parsed
    if username not in meta["strategies_submitted"]:
        meta["strategies_submitted"].append(username)

    # Record the player's plan in the move feed so the UI can show what each
    # player (especially bots) decided before trading.
    role = meta.get("player_roles", {}).get(username, {}).get("role", "human")
    if role == "bot":
        plan = ", ".join(
            f"{mi}:{act}" for mi, act in parsed
        )
        _record_move(
            game_id,
            player=username,
            action="plan",
            market=None,
            product=None,
            reason=plan or "skip all",
        )

    # All players submitted → determine turn order → transition to ACTION
    if len(meta["strategies_submitted"]) == len(table.players):
        turn_order = table.determine_turn_order()
        meta["turn_order"] = [
            {"username": p.username, "dice_total": d} for p, d in turn_order
        ]
        meta["phase"] = GamePhase.ACTION.value
        meta["action_index"] = 0
        meta["current_player"] = turn_order[0][0].username
        meta["current_market_index"] = None
        meta["message"] = (
            f"All strategies submitted. Turn order: {', '.join(t['username'] for t in meta['turn_order'])}"
        )
        _execute_next_action(game_id)
    else:
        remaining = [
            p.username
            for p in table.players
            if p.username not in meta["strategies_submitted"]
        ]
        meta["message"] = (
            f"Strategy for '{username}' recorded. Waiting for: {', '.join(remaining)}"
        )


@router.post("/{game_id}/strategy", summary="Submit a player's strategy")
def submit_strategy(game_id: str, req: SubmitStrategyRequest):
    _ensure_loaded(game_id)
    _check_phase(game_id, GamePhase.STRATEGY)
    parsed = _validate_strategy(game_id, req.username, req.strategy)
    _apply_submitted_strategy(game_id, req.username, parsed)

    _flush(game_id)
    append_history(
        game_id,
        "strategy_submitted",
        {"username": req.username, "strategy": [[m, a] for m, a in parsed]},
    )
    return _game_state(game_id)


@router.post("/{game_id}/bot-strategy", summary="Compute & submit a bot's strategy")
def submit_bot_strategy(game_id: str, req: BotStrategyRequest):
    _ensure_loaded(game_id)
    _check_phase(game_id, GamePhase.STRATEGY)
    table = _tables[game_id]
    meta = _meta[game_id]
    markets = meta["active_markets"]

    if table.get_player(req.username) is None:
        raise HTTPException(status_code=404, detail=f"Player '{req.username}' not found")

    # Build the same dict shape the AI strategies expect
    market_dicts = [_market_info(i, m).model_dump() for i, m in enumerate(markets, 1)]
    player_dicts = [_player_info(p).model_dump() for p in table.players]

    strategy = get_strategy(req.strategy_name)
    choices = strategy.choose_strategy(
        market_dicts,
        player_dicts,
        req.username,
        round_number=meta.get("round_number", table.current_round),
        total_rounds=table.total_rounds,
    )
    entries = [{"market_index": mi, "action": act} for mi, act in choices]

    parsed = _validate_strategy(game_id, req.username, entries)
    _apply_submitted_strategy(game_id, req.username, parsed)

    _flush(game_id)
    append_history(
        game_id,
        "bot_strategy_submitted",
        {
            "username": req.username,
            "strategy": req.strategy_name,
            "choices": [[m, a] for m, a in parsed],
        },
    )
    return _game_state(game_id)


# ---------------------------------------------------------------------------
# Action phase
# ---------------------------------------------------------------------------


def _is_human(meta: Dict[str, Any], username: str) -> bool:
    """True if the given player is a human (hot-seat) rather than a bot."""
    return meta.get("player_roles", {}).get(username, {}).get("role", "human") != "bot"


def _execute_next_action(game_id: str):
    """Execute the next action in the action queue (dice roll + condition check)."""
    table = _tables[game_id]
    meta = _meta[game_id]
    markets = meta["active_markets"]
    turn_order_list = [
        (table.get_player(t["username"]), t["dice_total"]) for t in meta["turn_order"]
    ]

    while meta["action_index"] < len(turn_order_list):
        player, initial_dice = turn_order_list[meta["action_index"]]
        strategies = meta["player_strategies"].get(player.username, [])

        # Find next unexecuted strategy for this player
        player_actions_done = meta.get("player_actions_done", {})
        done_count = player_actions_done.get(player.username, 0)

        if done_count >= len(strategies):
            # Move to next player
            meta["action_index"] += 1
            if meta["action_index"] < len(turn_order_list):
                next_p, _ = turn_order_list[meta["action_index"]]
                meta["current_player"] = next_p.username
            continue

        market_num, strategy = strategies[done_count]
        market = markets[market_num - 1]
        meta["current_player"] = player.username
        meta["current_market_index"] = market_num

        # Clear stale flags from previous action
        meta["can_buy"] = None
        meta["can_sell"] = None
        meta["action_failed"] = None
        meta["action_fail_reason"] = None

        if strategy == Action.SKIP.value:
            # Skip — mark it done. The while loop re-checks this player (they
            # may have more strategies, one per market) and only advances the
            # per-player action_index once ALL their actions are done.
            player_actions_done.setdefault(player.username, 0)
            player_actions_done[player.username] += 1
            meta["player_actions_done"] = player_actions_done
            _record_move(
                game_id,
                player=player.username,
                action="skip",
                market=market_num,
                product=market.location.product,
                dice_total=None,
                dice_price=None,
                reason="Chose to skip",
            )
            continue

        # Roll dice for this market
        dice_total = table.roll_dice_for_player()
        dice_price = dice_total * DICE_BASE
        meta["dice_total"] = dice_total
        meta["dice_price"] = dice_price

        if strategy == Action.BUY.value:
            result = table.process_market_action_buy(player, market, dice_total)
            if not result.get("can_buy"):
                meta["can_buy"] = None
                reason = result.get("error") or (
                    f"{player.username}: Buy not executed — dice {dice_price} FCFA < market {market.market_fixed_price} FCFA"
                )
                if _is_human(meta, player.username):
                    # Humans get to SEE the failed trade and confirm it.
                    meta["current_player"] = player.username
                    meta["current_market_index"] = market_num
                    meta["action_failed"] = True
                    meta["action_fail_reason"] = reason
                    meta["message"] = reason
                    return
                meta["message"] = f"{player.username}: {reason} Skipping."
                player_actions_done.setdefault(player.username, 0)
                player_actions_done[player.username] += 1
                meta["player_actions_done"] = player_actions_done
                _record_move(
                    game_id,
                    player=player.username,
                    action="failed_buy",
                    market=market_num,
                    product=market.location.product,
                    dice_total=dice_total,
                    dice_price=dice_price,
                    reason=reason,
                )
                continue
            meta["can_buy"] = True
            meta["max_affordable"] = result["max_affordable"]
            meta["message"] = (
                f"{player.username}: Buy condition met! Dice {dice_price} >= market {market.market_fixed_price}. Max affordable: {result['max_affordable']}. Send POST /action with quantity."
            )
            _record_move(
                game_id,
                player=player.username,
                action="roll",
                market=market_num,
                product=market.location.product,
                dice_total=dice_total,
                dice_price=dice_price,
                can_buy=True,
                max_affordable=result["max_affordable"],
            )
            return  # Wait for client to send quantity

        elif strategy == Action.SELL.value:
            # Pay entry fee
            fee_result = table.pay_sell_entry_fee(player, market)
            if not fee_result["success"]:
                reason = fee_result["error"]
                if _is_human(meta, player.username):
                    meta["current_player"] = player.username
                    meta["current_market_index"] = market_num
                    meta["action_failed"] = True
                    meta["action_fail_reason"] = reason
                    meta["message"] = reason
                    return
                meta["message"] = f"{player.username}: {reason} Skipping."
                player_actions_done.setdefault(player.username, 0)
                player_actions_done[player.username] += 1
                meta["player_actions_done"] = player_actions_done
                continue

            result = table.process_market_action_sell(player, market, dice_total)
            if not result.get("can_sell"):
                meta["can_sell"] = None
                reason = result.get("error") or (
                    f"{player.username}: Sell not executed — dice {dice_price} FCFA > market {market.market_fixed_price} FCFA"
                )
                if _is_human(meta, player.username):
                    meta["current_player"] = player.username
                    meta["current_market_index"] = market_num
                    meta["action_failed"] = True
                    meta["action_fail_reason"] = reason
                    meta["message"] = reason
                    return
                meta["message"] = f"{player.username}: {reason} Skipping."
                player_actions_done.setdefault(player.username, 0)
                player_actions_done[player.username] += 1
                meta["player_actions_done"] = player_actions_done
                _record_move(
                    game_id,
                    player=player.username,
                    action="failed_sell",
                    market=market_num,
                    product=market.location.product,
                    dice_total=dice_total,
                    dice_price=dice_price,
                    reason=reason,
                )
                continue
            meta["can_sell"] = True
            meta["seller_qty"] = result["seller_qty"]
            meta["message"] = (
                f"{player.username}: Sell condition met! Dice {dice_price} <= market {market.market_fixed_price}. You have {result['seller_qty']} units. Send POST /action with quantity."
            )
            _record_move(
                game_id,
                player=player.username,
                action="roll",
                market=market_num,
                product=market.location.product,
                dice_total=dice_total,
                dice_price=dice_price,
                can_sell=True,
                seller_qty=result["seller_qty"],
            )
            return  # Wait for client to send quantity

    # All actions done → end round
    _end_current_round(game_id)


def _execute_action(
    game_id: str, quantity: int, actor: str = "human"
) -> ActionResultResponse:
    """Execute the current pending action (buy or sell) with the given quantity."""
    table = _tables[game_id]
    meta = _meta[game_id]
    markets = meta["active_markets"]

    player = table.get_player(meta["current_player"])
    if not player:
        raise HTTPException(status_code=404, detail="Current player not found")

    market_num = meta["current_market_index"]
    market = markets[market_num - 1]
    dice_price = meta["dice_price"]

    # A failed planned action that the human acknowledged (Continue): there is
    # no trade to execute — record the skip and advance the action queue.
    if meta.get("action_failed"):
        reason = meta.get("action_fail_reason") or "Trade could not be executed"
        meta["action_failed"] = None
        meta["action_fail_reason"] = None
        player_actions_done = meta.get("player_actions_done", {})
        player_actions_done.setdefault(player.username, 0)
        player_actions_done[player.username] += 1
        meta["player_actions_done"] = player_actions_done
        meta["can_buy"] = None
        meta["can_sell"] = None

        _flush(game_id)
        append_history(
            game_id,
            "action_failed",
            {
                "player": player.username,
                "market": market_num,
                "reason": reason,
                "actor": actor,
            },
        )

        _execute_next_action(game_id)
        _flush(game_id)
        state = _game_state(game_id)
        round_ended = state.phase != GamePhase.ACTION.value
        return ActionResultResponse(
            success=True,
            action="skip",
            details={"reason": reason},
            next_state=state,
            message=(
                f"{player.username}: trade failed — {reason}. Round ended."
                if round_ended
                else f"{player.username}: trade failed — {reason}. Next: {state.current_player}"
            ),
        )

    if quantity is None or quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be >= 1")

    # Determine if this is a buy or sell from the strategy
    strategies = meta["player_strategies"].get(player.username, [])
    player_actions_done = meta.get("player_actions_done", {})
    done_count = player_actions_done.get(player.username, 0)
    _, strategy = strategies[done_count]

    result: Dict[str, Any] = {}

    if strategy == Action.BUY.value:
        max_aff = meta["max_affordable"]
        if quantity > max_aff:
            raise HTTPException(
                status_code=400,
                detail=f"Quantity {quantity} exceeds max affordable ({max_aff})",
            )
        result = table.execute_buy_at_market_price(player, market, quantity)
        action_label = "buy"

    elif strategy == Action.SELL.value:
        max_sell = meta["seller_qty"]
        if quantity > max_sell:
            raise HTTPException(
                status_code=400,
                detail=f"Quantity {quantity} exceeds inventory ({max_sell})",
            )
        result = table.execute_market_auto_buy(player, market, quantity, dice_price)
        action_label = "sell"

    else:
        raise HTTPException(status_code=400, detail="No pending action to execute")

    # Mark this action done. A player can have several strategies (one per
    # active market), so the per-player action_index must NOT advance here —
    # _execute_next_action moves to the player's next action, then to the next
    # player, and only ends the round once everyone's actions are done.
    player_actions_done.setdefault(player.username, 0)
    player_actions_done[player.username] += 1
    meta["player_actions_done"] = player_actions_done

    # Clear flags so next poll doesn't see stale values
    meta["can_buy"] = None
    meta["can_sell"] = None

    # Record the executed trade so the UI can show what actually happened.
    if action_label == "buy":
        _record_move(
            game_id,
            player=player.username,
            action="buy",
            market=market_num,
            product=result.get("product") or market.location.product,
            dice_total=meta.get("dice_total"),
            dice_price=dice_price,
            quantity=result.get("units_bought", quantity),
            unit_price=result.get("avg_price", market.market_fixed_price),
            total=result.get("total_with_tax", 0),
            balance=result.get("buyer_balance", player.balance),
        )
    else:
        _record_move(
            game_id,
            player=player.username,
            action="sell",
            market=market_num,
            product=result.get("product") or market.location.product,
            dice_total=meta.get("dice_total"),
            dice_price=dice_price,
            quantity=result.get("quantity_sold", quantity),
            unit_price=result.get("price_per_unit", dice_price),
            total=result.get("net_revenue", 0),
            balance=result.get("seller_balance", player.balance),
        )

    _flush(game_id)
    append_history(
        game_id,
        action_label,
        {
            "player": player.username,
            "market": market_num,
            "quantity": quantity,
            "actor": actor,
            "result": result,
        },
    )

    # Move to the player's next action, the next player, or end the round.
    _execute_next_action(game_id)

    _flush(game_id)
    state = _game_state(game_id)
    round_ended = state.phase != GamePhase.ACTION.value
    return ActionResultResponse(
        success=True,
        action=action_label,
        details=result,
        next_state=state,
        message=(
            f"{player.username} {action_label} complete. Round ended."
            if round_ended
            else f"{player.username} {action_label} complete. Next: {state.current_player}"
        ),
    )


@router.post(
    "/{game_id}/action", summary="Execute the current action (buy/sell with quantity)"
)
def execute_action(game_id: str, req: ExecuteActionRequest):
    _ensure_loaded(game_id)
    _check_phase(game_id, GamePhase.ACTION)
    return _execute_action(game_id, req.quantity, actor="human")


@router.post(
    "/{game_id}/bot-action",
    summary="Execute the current action for an AI bot (auto quantity)",
)
def execute_bot_action(game_id: str, req: BotActionRequest):
    _ensure_loaded(game_id)
    _check_phase(game_id, GamePhase.ACTION)
    meta = _meta[game_id]

    if not (meta.get("can_buy") or meta.get("can_sell")):
        raise HTTPException(
            status_code=400,
            detail="No pending action to execute for the current player",
        )

    quantity = req.quantity
    if quantity is None:
        # Let the strategy choose the quantity automatically
        strategy_name = req.strategy_name or "buylowsellhigh"
        strategy = get_strategy(strategy_name)
        state = _game_state(game_id).model_dump()
        if meta.get("can_buy"):
            quantity = strategy.choose_buy_quantity(state)
        else:
            quantity = strategy.choose_sell_quantity(state)

    return _execute_action(game_id, quantity, actor="bot")


def _end_current_round(game_id: str):
    """End the current round: record balance changes and pause for a recap.

    Instead of silently starting the next round (or ending the game), we
    transition to the END_ROUND phase and let the frontend show a recap. A
    separate POST /next-round advances past it, so the "what happened this
    round" moment is visible.
    """
    table = _tables[game_id]
    meta = _meta[game_id]
    markets = meta["active_markets"]

    purchases = table.end_round(markets)

    # Per-player balance delta this round (vs last round end or starting balance).
    round_history = meta.get("round_history", [])
    prev_balances = round_history[-1]["balances"] if round_history else None
    starting = meta.get("starting_balance", 0)
    players_recap = []
    for p in table.players:
        prev = (prev_balances or {}).get(p.username, starting)
        players_recap.append(
            {
                "username": p.username,
                "balance": p.balance,
                "change": round(p.balance - prev, 2),
                "role": meta.get("player_roles", {}).get(p.username, {}).get("role", "human"),
            }
        )

    # Snapshot balances for results stats (best/worst round, win rate, etc.).
    meta.setdefault("round_history", []).append(
        {
            "round": table.current_round,
            "balances": {p.username: round(p.balance, 2) for p in table.players},
        }
    )

    meta["round_recap"] = {
        "round": table.current_round,
        "players": players_recap,
        "news": meta.get("news", []),
        "is_last": table.current_round >= table.total_rounds,
    }

    # Clear transient action state.
    meta["player_actions_done"] = {}
    meta["dice_total"] = None
    meta["dice_price"] = None
    meta["can_buy"] = None
    meta["can_sell"] = None
    meta["max_affordable"] = None
    meta["seller_qty"] = None
    meta["current_player"] = None
    meta["current_market_index"] = None

    meta["phase"] = GamePhase.END_ROUND.value
    meta["message"] = f"Round {table.current_round} complete."

    _flush(game_id)
    append_history(
        game_id, "round_ended", {"round": table.current_round, "purchases": purchases}
    )


@router.post("/{game_id}/next-round", summary="Advance past the round recap")
def next_round(game_id: str):
    """Move from the end-of-round recap to the next round (or game over)."""
    _ensure_loaded(game_id)
    _check_phase(game_id, GamePhase.END_ROUND)
    table = _tables[game_id]
    meta = _meta[game_id]

    if table.current_round >= table.total_rounds:
        meta["phase"] = GamePhase.GAME_OVER.value
        meta["message"] = "Game over! Final standings are ready."

        # Market day is over — any unsold stock spoils and is worthless.
        # Snapshot it for the results screen, then clear inventory so the
        # final ranking reflects cash only (spoiled goods don't count).
        spoiled: Dict[str, List[Dict[str, Any]]] = {}
        for p in table.players:
            spoiled[p.username] = [_product_to_dict(it) for it in p.inventory]
            p.inventory.clear()
        meta["spoiled_inventory"] = spoiled
    else:
        _start_new_round(game_id)

    _flush(game_id)
    return _game_state(game_id)


# ---------------------------------------------------------------------------
# Game over
# ---------------------------------------------------------------------------


@router.get("/{game_id}/results", summary="Get final results")
def get_results(game_id: str):
    _ensure_loaded(game_id)
    _check_phase(game_id, GamePhase.GAME_OVER)
    table = _tables[game_id]
    meta = _meta[game_id]
    starting_balance = meta.get("starting_balance", 0)
    round_history = meta.get("round_history", [])

    final_standings = sorted(table.players, key=lambda p: p.balance, reverse=True)
    spoiled = meta.get("spoiled_inventory", {})
    standings = []
    for rank, player in enumerate(final_standings, 1):
        profit_loss = player.balance - starting_balance
        standings.append(
            {
                "rank": rank,
                "username": player.username,
                "final_balance": player.balance,
                "profit_loss": round(profit_loss, 2),
                "inventory": [_product_to_dict(item) for item in player.inventory],
                "spoiled": spoiled.get(player.username, []),
            }
        )

    # Per-player round stats: wins (led a round), best/worst round, biggest
    # single-round gain/loss, computed from the balance snapshots.
    rounds_stats: Dict[str, Dict[str, Any]] = {}
    for username in [p.username for p in table.players]:
        wins = 0
        best_gain = 0.0
        worst_loss = 0.0
        best_round = None
        worst_round = None
        prev = starting_balance
        for rh in round_history:
            bal = rh["balances"].get(username)
            if bal is None:
                continue
            # Leader this round = highest balance at round end.
            if rh["balances"] and max(rh["balances"].values()) == bal:
                wins += 1
            delta = bal - prev
            if delta > best_gain:
                best_gain = delta
                best_round = rh["round"]
            if delta < worst_loss:
                worst_loss = delta
                worst_round = rh["round"]
            prev = bal
        rounds_stats[username] = {
            "rounds_played": len(round_history),
            "wins": wins,
            "win_rate": round(wins / len(round_history), 4) if round_history else 0.0,
            "best_round": best_round,
            "best_gain": round(best_gain, 2),
            "worst_round": worst_round,
            "worst_loss": round(worst_loss, 2),
        }

    return {
        "game_id": game_id,
        "winner": final_standings[0].username if final_standings else None,
        "standings": standings,
        "starting_balance": starting_balance,
        "total_rounds": table.total_rounds,
        "rounds_played": len(round_history),
        "stats": rounds_stats,
    }


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


@router.get("/{game_id}/history", summary="Get the game's event history")
def get_history(game_id: str):
    _ensure_loaded(game_id)
    return {"game_id": game_id, "history": load_history(game_id)}
