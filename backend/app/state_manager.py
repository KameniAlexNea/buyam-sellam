"""File-based game state persistence.

Each game gets a folder under out/{game_id}/ with:
  - state.json   : current game state (overwritten on every transition)
  - history.json : append-only log of actions
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# Root directory for game state files.
OUT_DIR = Path(__file__).resolve().parent.parent / "out"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _game_dir(game_id: str) -> Path:
    """Return the path for a game's state directory."""
    return OUT_DIR / game_id


def _state_path(game_id: str) -> Path:
    return _game_dir(game_id) / "state.json"


def _history_path(game_id: str) -> Path:
    return _game_dir(game_id) / "history.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_game_dir(game_id: str) -> None:
    """Create the game directory and initial state file."""
    d = _game_dir(game_id)
    d.mkdir(parents=True, exist_ok=True)
    save_state(
        game_id,
        {
            "game_id": game_id,
            "phase": "created",
            "round_number": 0,
            "players": [],
            "markets": [],
            "strategies_submitted": [],
            "turn_order": [],
            "current_player": None,
            "current_market_index": None,
            "created_at": _now(),
            "updated_at": _now(),
        },
    )


def save_state(game_id: str, state: Dict[str, Any]) -> None:
    """Overwrite the current state file for a game."""
    state["updated_at"] = _now()
    path = _state_path(game_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, default=str))


def load_state(game_id: str) -> Optional[Dict[str, Any]]:
    """Load the current state file for a game, or None if not found."""
    path = _state_path(game_id)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def append_history(
    game_id: str, action: str, details: Optional[Dict[str, Any]] = None
) -> None:
    """Append an entry to the game's history log."""
    path = _history_path(game_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": _now(),
        "action": action,
        "details": details or {},
    }
    history: List[dict] = []
    if path.exists():
        history = json.loads(path.read_text())
    history.append(entry)
    path.write_text(json.dumps(history, indent=2, default=str))


def load_history(game_id: str) -> List[Dict[str, Any]]:
    """Load the full event history for a game (empty list if not found)."""
    path = _history_path(game_id)
    if not path.exists():
        return []
    return json.loads(path.read_text())


def list_games() -> List[Dict[str, Any]]:
    """Return a summary of all games found in the out/ directory."""
    if not OUT_DIR.exists():
        return []
    games = []
    for entry in sorted(OUT_DIR.iterdir()):
        if entry.is_dir() and not entry.name.startswith("."):
            state = load_state(entry.name)
            if state:
                games.append(
                    {
                        "game_id": entry.name,
                        "phase": state.get("phase", "unknown"),
                        "round_number": state.get("round_number", 0),
                        "total_rounds": state.get("total_rounds", 0),
                        "player_count": len(state.get("players", [])),
                        "created_at": state.get("created_at", ""),
                    }
                )
    return games


def delete_game(game_id: str) -> bool:
    """Delete a game's state directory."""
    import shutil

    d = _game_dir(game_id)
    if d.exists():
        shutil.rmtree(d)
        return True
    return False


def new_game_id() -> str:
    """Generate a new short game ID."""
    return uuid.uuid4().hex[:12]
