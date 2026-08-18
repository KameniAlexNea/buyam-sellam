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
    starting_balance: float = Field(50000, ge=0)
    total_rounds: int = Field(5, ge=1, le=100)
    difficulty: Difficulty = Field(
        Difficulty.MEDIUM,
        description="Game difficulty level (affects markets, taxes, player resources)",
    )


class AddPlayerRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)


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


class ExecuteActionRequest(BaseModel):
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


class GameStateResponse(BaseModel):
    game_id: str
    phase: GamePhase
    round_number: int
    total_rounds: int
    difficulty: str = "medium"
    players: list[PlayerInfoResponse] = []
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
