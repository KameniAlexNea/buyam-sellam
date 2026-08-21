"""Pydantic schemas for the Buyam-Sellam API."""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


from ksell.model.difficulty import Difficulty


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class GamePhase(str, Enum):
    CREATED = "created"
    SETUP = "setup"
    ROUND_START = "round_start"
    STRATEGY = "strategy"
    TURN_ORDER = "turn_order"
    ACTION = "action"
    END_ROUND = "end_round"
    GAME_OVER = "game_over"


class Action(str, Enum):
    BUY = "buy"
    SELL = "sell"
    SKIP = "skip"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CreateGameRequest(BaseModel):
    # The starting balance comes from the selected difficulty preset
    # (Easy 80k / Medium 50k / Hard 30k) — see ksell/model/difficulty.py.
    total_rounds: int = Field(10, ge=1, le=20)
    difficulty: Difficulty = Field(
        Difficulty.MEDIUM,
        description="Game difficulty level (affects markets, taxes, player resources)",
    )


class AddPlayerRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    role: str = Field(
        "human",
        description="'human' for a live player, 'bot' for an AI-controlled player",
    )
    strategy: Optional[str] = Field(
        None,
        description="Bot strategy name (required when role='bot', e.g. 'buylowsellhigh')",
    )


class SubmitStrategyRequest(BaseModel):
    username: str
    strategy: list[dict] = Field(
        ...,
        description="List of {market_index: int, action: 'buy'|'sell'|'skip'}",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "alice",
                "strategy": [
                    {"market_index": 1, "action": "buy"},
                    {"market_index": 2, "action": "skip"},
                ],
            }
        }
    }


class BotStrategyRequest(BaseModel):
    username: str = Field(..., description="The bot player's username")
    strategy_name: str = Field(
        ...,
        description="Bot strategy key (e.g. 'buylowsellhigh', 'aggressivebuyer')",
    )


class ExecuteActionRequest(BaseModel):
    # quantity=0 is used as an "acknowledge" for a failed planned action
    # (the human confirms the failure before the action queue advances).
    quantity: Optional[int] = Field(None, ge=0)


class BotActionRequest(BaseModel):
    strategy_name: Optional[str] = Field(
        None,
        description="Bot strategy used to choose the quantity automatically",
    )
    quantity: Optional[int] = Field(None, ge=1)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class PlayerInfoResponse(BaseModel):
    username: str
    balance: float
    inventory: list[dict] = []


class MarketInfoResponse(BaseModel):
    market_index: int
    name: str
    product: str
    market_fixed_price: float
    market_supply: int
    tax_rate: float = 0.0
    sell_entry_fee: int = 0
    price_history: list[int] = Field(
        default_factory=list,
        description="Price per active round (drives the sparkline charts)",
    )


class GameStateResponse(BaseModel):
    game_id: str
    phase: GamePhase
    round_number: int
    total_rounds: int
    difficulty: str = "medium"
    players: list[PlayerInfoResponse] = []
    player_roles: dict[str, dict] = Field(
        default_factory=dict,
        description="username → {role: 'human'|'bot', strategy: str|None}",
    )
    markets: list[MarketInfoResponse] = []
    turn_order: Optional[list[dict]] = None
    current_player: Optional[str] = None
    current_market_index: Optional[int] = None
    strategies_submitted: list[str] = []
    dice_total: Optional[int] = None
    dice_price: Optional[int] = None
    can_buy: Optional[bool] = None
    can_sell: Optional[bool] = None
    max_affordable: Optional[int] = None
    seller_qty: Optional[int] = None
    action_failed: Optional[bool] = None
    action_fail_reason: Optional[str] = None
    move_feed: list[dict] = Field(
        default_factory=list,
        description="Recent action steps (plan/buy/sell/skip/dice) for UI replay",
    )
    round_recap: Optional[dict] = Field(
        default=None,
        description="End-of-round summary (per-player changes, market moves, headline)",
    )
    news: list[dict] = Field(
        default_factory=list,
        description="Market news headlines for the current round (ticker)",
    )
    message: str = ""


class ActionResultResponse(BaseModel):
    success: bool
    action: str
    details: dict[str, Any] = {}
    next_state: Optional[GameStateResponse] = None
    message: str = ""


class GameListEntry(BaseModel):
    game_id: str
    phase: str
    round_number: int
    total_rounds: int
    player_count: int
    created_at: str


class GameListResponse(BaseModel):
    games: list[GameListEntry] = []


class FinalResultsResponse(BaseModel):
    game_id: str
    winner: str
    standings: list[dict]
    starting_balance: float


class StrategyInfoResponse(BaseModel):
    name: str
    label: str
    description: str


class HistoryEntry(BaseModel):
    timestamp: str
    action: str
    details: dict[str, Any] = Field(default_factory=dict)


class HistoryResponse(BaseModel):
    game_id: str
    history: list[HistoryEntry] = []
