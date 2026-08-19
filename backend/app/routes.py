"""FastAPI routes for the Buyam-Sellam game API.

State machine:
  CREATED → SETUP → ROUND_START → STRATEGY → TURN_ORDER → ACTION → END_ROUND
                                                                    ↓
                                                    (back to ROUND_START or GAME_OVER)

The Table object is kept in-memory per game.  After every state transition
the full state is flushed to out/{game_id}/state.json.
"""

import random
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ksell.model.difficulty import Difficulty, DifficultyConfig
from ksell.model.market_board import MarketBoard, DICE_BASE
from ksell.model.player import Player
from ksell.model.product import ProductModel
from ksell.model.table import Table
from ksell.pojo.user import User
from ksell.strategy import ALL_STRATEGIES, get_strategy
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
    new_game_id,
    save_state,
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
        message=meta.get("message", ""),
    )


def _flush(game_id: str) -> None:
    """Persist the current in-memory state to disk."""
    table = _tables[game_id]
    meta = _meta[game_id]
    state = {
        "game_id": game_id,
        "phase": meta["phase"],
        "round_number": meta.get("round_number", table.current_round),
        "total_rounds": table.total_rounds,
        "difficulty": meta.get("difficulty", "medium"),
        "players": [_player_info(p).model_dump() for p in table.players],
        "player_roles": meta.get("player_roles", {}),
        "markets": [
            _market_info(i, m).model_dump()
            for i, m in enumerate(meta.get("active_markets", []), 1)
        ],
        "strategies_submitted": meta.get("strategies_submitted", []),
        "player_strategies": meta.get("player_strategies", {}),
        "turn_order": meta.get("turn_order"),
        "current_player": meta.get("current_player"),
        "current_market_index": meta.get("current_market_index"),
        "action_index": meta.get("action_index", 0),
        "dice_total": meta.get("dice_total"),
        "dice_price": meta.get("dice_price"),
        "can_buy": meta.get("can_buy"),
        "can_sell": meta.get("can_sell"),
        "max_affordable": meta.get("max_affordable"),
        "seller_qty": meta.get("seller_qty"),
        "message": meta.get("message", ""),
        "starting_balance": meta.get("starting_balance", 0),
    }
    save_state(game_id, state)


def _check_phase(game_id: str, *allowed: GamePhase) -> None:
    """Raise 400 if the game is not in one of the allowed phases."""
    if _meta[game_id]["phase"] not in {a.value for a in allowed}:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action in phase '{_meta[game_id]['phase']}'. "
            f"Expected one of: {[a.value for a in allowed]}",
        )


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
        "starting_balance": req.starting_balance,
        "difficulty": req.difficulty.value,
        "strategies_submitted": [],
        "player_strategies": {},
        "player_roles": {},
        "turn_order": [],
        "current_player": None,
        "current_market_index": None,
        "action_index": 0,
        "message": "Game created. Add players with POST /games/{id}/players",
    }
    append_history(
        game_id,
        "game_created",
        {
            "total_rounds": req.total_rounds,
            "difficulty": req.difficulty.value,
            "starting_balance": req.starting_balance,
        },
    )
    return _game_state(game_id)


@router.get("", summary="List all games")
def list_games_endpoint() -> GameListResponse:
    return GameListResponse(games=[GameListEntry(**g) for g in list_games()])


@router.get("/{game_id}", summary="Get game state")
def get_game(game_id: str) -> GameStateResponse:
    if game_id not in _tables:
        raise HTTPException(status_code=404, detail="Game not found")
    return _game_state(game_id)


@router.delete("/{game_id}", summary="Delete a game")
def delete_game_endpoint(game_id: str):
    if game_id not in _tables:
        raise HTTPException(status_code=404, detail="Game not found")
    del _tables[game_id]
    del _meta[game_id]
    delete_game(game_id)
    return {"deleted": game_id}


# ---------------------------------------------------------------------------
# Setup phase
# ---------------------------------------------------------------------------


@router.post("/{game_id}/players", summary="Add a player")
def add_player(game_id: str, req: AddPlayerRequest):
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
    # Bots without a strategy get a random one from the backend registry, so
    # the strategy list is always the single source of truth (no hardcoding).
    role = req.role if req.role in {"human", "bot"} else "human"
    strategy = req.strategy
    if role == "bot" and not strategy:
        strategy = random.choice(list(ALL_STRATEGIES.keys()))
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
    meta["message"] = (
        f"Round {table.current_round} started. {num_markets} markets active. Submit strategies."
    )

    _flush(game_id)


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
    choices = strategy.choose_strategy(market_dicts, player_dicts, req.username)
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

        if strategy == Action.SKIP.value:
            # Skip — just advance
            player_actions_done.setdefault(player.username, 0)
            player_actions_done[player.username] += 1
            meta["player_actions_done"] = player_actions_done
            meta["action_index"] += 1
            if meta["action_index"] < len(turn_order_list):
                next_p, _ = turn_order_list[meta["action_index"]]
                meta["current_player"] = next_p.username
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
                meta["message"] = (
                    f"{player.username}: Buy condition not met (dice {dice_price} < market {market.market_fixed_price}). Skipping."
                )
                player_actions_done.setdefault(player.username, 0)
                player_actions_done[player.username] += 1
                meta["player_actions_done"] = player_actions_done
                meta["action_index"] += 1
                if meta["action_index"] < len(turn_order_list):
                    next_p, _ = turn_order_list[meta["action_index"]]
                    meta["current_player"] = next_p.username
                continue
            meta["can_buy"] = True
            meta["max_affordable"] = result["max_affordable"]
            meta["message"] = (
                f"{player.username}: Buy condition met! Dice {dice_price} >= market {market.market_fixed_price}. Max affordable: {result['max_affordable']}. Send POST /action with quantity."
            )
            return  # Wait for client to send quantity

        elif strategy == Action.SELL.value:
            # Pay entry fee
            fee_result = table.pay_sell_entry_fee(player, market)
            if not fee_result["success"]:
                meta["message"] = f"{player.username}: {fee_result['error']} Skipping."
                player_actions_done.setdefault(player.username, 0)
                player_actions_done[player.username] += 1
                meta["player_actions_done"] = player_actions_done
                meta["action_index"] += 1
                if meta["action_index"] < len(turn_order_list):
                    next_p, _ = turn_order_list[meta["action_index"]]
                    meta["current_player"] = next_p.username
                continue

            result = table.process_market_action_sell(player, market, dice_total)
            if not result.get("can_sell"):
                meta["can_sell"] = None
                meta["message"] = (
                    f"{player.username}: Sell condition not met (dice {dice_price} > market {market.market_fixed_price}). Skipping."
                )
                player_actions_done.setdefault(player.username, 0)
                player_actions_done[player.username] += 1
                meta["player_actions_done"] = player_actions_done
                meta["action_index"] += 1
                if meta["action_index"] < len(turn_order_list):
                    next_p, _ = turn_order_list[meta["action_index"]]
                    meta["current_player"] = next_p.username
                continue
            meta["can_sell"] = True
            meta["seller_qty"] = result["seller_qty"]
            meta["message"] = (
                f"{player.username}: Sell condition met! Dice {dice_price} <= market {market.market_fixed_price}. You have {result['seller_qty']} units. Send POST /action with quantity."
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

    # Advance action index
    player_actions_done.setdefault(player.username, 0)
    player_actions_done[player.username] += 1
    meta["player_actions_done"] = player_actions_done

    # Clear flags so next poll doesn't see stale values
    meta["can_buy"] = None
    meta["can_sell"] = None

    turn_order_list = [
        (table.get_player(t["username"]), t["dice_total"]) for t in meta["turn_order"]
    ]
    meta["action_index"] += 1
    if meta["action_index"] < len(turn_order_list):
        next_p, _ = turn_order_list[meta["action_index"]]
        meta["current_player"] = next_p.username

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

    # Check if all actions are done
    all_done = meta["action_index"] >= len(turn_order_list)
    if all_done:
        _end_current_round(game_id)
        return ActionResultResponse(
            success=True,
            action=action_label,
            details=result,
            next_state=_game_state(game_id),
            message=f"{player.username} {action_label} complete. Round ended.",
        )

    # Execute next action automatically
    _execute_next_action(game_id)

    _flush(game_id)
    return ActionResultResponse(
        success=True,
        action=action_label,
        details=result,
        next_state=_game_state(game_id),
        message=f"{player.username} {action_label} complete. Next: {meta.get('current_player', '—')}",
    )


@router.post(
    "/{game_id}/action", summary="Execute the current action (buy/sell with quantity)"
)
def execute_action(game_id: str, req: ExecuteActionRequest):
    _check_phase(game_id, GamePhase.ACTION)
    if not req.quantity or req.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be >= 1")
    return _execute_action(game_id, req.quantity, actor="human")


@router.post(
    "/{game_id}/bot-action",
    summary="Execute the current action for an AI bot (auto quantity)",
)
def execute_bot_action(game_id: str, req: BotActionRequest):
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
    """End the current round and either start a new one or end the game."""
    table = _tables[game_id]
    meta = _meta[game_id]
    markets = meta["active_markets"]

    purchases = table.end_round(markets)

    if table.current_round >= table.total_rounds:
        meta["phase"] = GamePhase.GAME_OVER.value
        meta["message"] = "Game over! Final standings are ready."
    else:
        _start_new_round(game_id)

    meta["player_actions_done"] = {}
    meta["dice_total"] = None
    meta["dice_price"] = None
    meta["can_buy"] = None
    meta["can_sell"] = None
    meta["max_affordable"] = None
    meta["seller_qty"] = None

    _flush(game_id)
    append_history(
        game_id, "round_ended", {"round": table.current_round, "purchases": purchases}
    )


# ---------------------------------------------------------------------------
# Game over
# ---------------------------------------------------------------------------


@router.get("/{game_id}/results", summary="Get final results")
def get_results(game_id: str):
    _check_phase(game_id, GamePhase.GAME_OVER)
    table = _tables[game_id]
    meta = _meta[game_id]
    starting_balance = meta.get("starting_balance", 0)

    final_standings = sorted(table.players, key=lambda p: p.balance, reverse=True)
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
            }
        )

    return {
        "game_id": game_id,
        "winner": final_standings[0].username if final_standings else None,
        "standings": standings,
        "starting_balance": starting_balance,
    }


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


@router.get("/{game_id}/history", summary="Get the game's event history")
def get_history(game_id: str):
    if game_id not in _tables:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"game_id": game_id, "history": load_history(game_id)}
