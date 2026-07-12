"""Buyam-Sellam — automated simulation via the FastAPI web service.

Identical game flow to simulate/game.py but all decisions are made by
calling the REST API endpoints instead of the model classes directly.

Usage:
    # Start the server first:
    uvicorn app.main:app --host 0.0.0.0 --port 8000

    # Then run this script:
    python -m ksell.simulate.game_api
"""

import random
import sys
import time
from typing import Any, Dict, List

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "http://localhost:8000/games"
PROXY_AVOID = {"proxies": {}}  # Avoid corporate proxy for localhost


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _get(path: str) -> Dict[str, Any]:
    resp = requests.get(f"{BASE_URL}{path}", **PROXY_AVOID)
    if not resp.ok:
        try:
            detail = resp.json().get("detail", resp.text[:200])
        except Exception:
            detail = resp.text[:200]
        print(f"  ✗ GET {path} failed ({resp.status_code}): {detail}")
    resp.raise_for_status()
    return resp.json()


def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.post(f"{BASE_URL}{path}", json=payload, **PROXY_AVOID)
    if not resp.ok:
        try:
            detail = resp.json().get("detail", resp.text[:200])
        except Exception:
            detail = resp.text[:200]
        print(f"  ✗ POST {path} failed ({resp.status_code}): {detail}")
    resp.raise_for_status()
    return resp.json()


def _delete(path: str) -> Dict[str, Any]:
    resp = requests.delete(f"{BASE_URL}{path}", **PROXY_AVOID)
    if not resp.ok:
        try:
            detail = resp.json().get("detail", resp.text[:200])
        except Exception:
            detail = resp.text[:200]
        print(f"  ✗ DELETE {path} failed ({resp.status_code}): {detail}")
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


def main():
    print("""
Welcome to Buyam-Sellam App (API Mode)

Configure players and start the game!
""")

    n_players = int(input("Enter number of players: ").strip() or "3")
    if n_players < 2:
        print("At least 2 players are required to start the game.")
        sys.exit(1)

    # Difficulty selection
    print("\nDifficulty levels:")
    print("  1. Easy   — Generous resources, low taxes, fewer competitors")
    print("  2. Medium — Balanced challenge (default)")
    print("  3. Hard   — Tight budget, high taxes, more competition")
    diff_choice = input("Select difficulty (1/2/3): ").strip() or "2"
    DIFF_MAP = {"1": "easy", "2": "medium", "3": "hard"}
    difficulty = DIFF_MAP.get(diff_choice, "medium")

    n_rounds = int(input("Enter number of rounds for the game: ").strip() or "5")

    # ---- Create game ----
    print(f"\nCreating game with {n_players} players, {n_rounds} rounds (difficulty: {difficulty})...")
    state = _post(
        "",
        {
            "total_rounds": n_rounds,
            "difficulty": difficulty,
        },
    )
    game_id = state["game_id"]
    print(f"Game ID: {game_id} | Difficulty: {state.get('difficulty', difficulty)}")

    # ---- Add players ----
    usernames = []
    for i in range(n_players):
        username = f"Player_{i + 1}"
        _post(f"/{game_id}/players", {"username": username})
        usernames.append(username)
        print(f"  Added {username}")

    # ---- Start game ----
    print("\nStarting game...")
    state = _post(f"/{game_id}/start", {})
    print(f"Phase: {state['phase']} | Round: {state['round_number']}")
    print(f"Players: {[p['username'] for p in state['players']]}")

    # -----------------------------------------------------------------------
    # Game loop
    # -----------------------------------------------------------------------

    for round_number in range(1, n_rounds + 1):
        print(f"\n{'=' * 60}")
        print(f"--- Round {round_number} ---")
        print(f"{'=' * 60}")

        # Poll until we're in STRATEGY phase (server may auto-advance rounds)
        state = _wait_phase(game_id, "strategy", timeout=10)

        markets = state["markets"]
        print("\nAvailable Markets this round:")
        for m in markets:
            print(
                f"  {m['market_index']}. {m['name']} - {m['product']}, "
                f"Price: {m['market_fixed_price']} FCFA, Supply: {m['market_supply']}"
            )

        # ---- Strategy phase: random strategy for each player ----
        print(f"\n{'=' * 60}")
        print("STRATEGY PHASE")
        print(f"{'=' * 60}")

        for username in usernames:
            strategy = _random_strategy(markets, state["players"], username)
            parsed = [{"market_index": mi, "action": action} for mi, action in strategy]

            # Submit — this may trigger action phase if last player
            state = _post(
                f"/{game_id}/strategy",
                {"username": username, "strategy": parsed},
            )

            strat_str = ", ".join(f"M{mi}-{a}" for mi, a in strategy)
            print(f"  {username}: {strat_str}")

        # ---- Action phase: handle quantity prompts ----
        print(f"\n{'=' * 60}")
        print("ACTION PHASE")
        print(f"{'=' * 60}")

        state = _handle_actions(game_id, n_rounds)

        # ---- End of round standings ----
        print(f"\n{'=' * 50}")
        print(f"END OF ROUND {round_number} - STANDINGS")
        print(f"{'=' * 50}")
        for p in state["players"]:
            inv = (
                ", ".join(
                    f"{it['product']['name']}: {it['quantity']} (avg {it['avg_cost']:.0f} FCFA)"
                    for it in p["inventory"]
                )
                if p["inventory"]
                else "None"
            )
            print(
                f"  {p['username']}: Balance = {p['balance']:.2f} FCFA, Inventory = [{inv}]"
            )

    # -----------------------------------------------------------------------
    # Game over
    # -----------------------------------------------------------------------

    results = _get(f"/{game_id}/results")
    print(f"\n{'=' * 60}")
    print(f"{'GAME OVER - FINAL RESULTS':^60}")
    print(f"{'=' * 60}")

    for entry in results["standings"]:
        pl = entry["profit_loss"]
        status = "+" if pl >= 0 else ""
        inv = (
            ", ".join(
                f"{it['product']['name']}: {it['quantity']} (avg {it['avg_cost']:.0f} FCFA)"
                for it in entry["inventory"]
            )
            if entry["inventory"]
            else "None"
        )
        print(
            f"{entry['rank']}. {entry['username']:<20} Final Balance: {entry['final_balance']:>10,.0f} FCFA ({status}{pl:>10,.0f})"
        )
        print(f"   Inventory: [{inv}]")

    print(f"\n{'🏆 ' + results['winner'] + ' WINS! 🏆':^60}")
    print(f"{'=' * 60}")

    # Cleanup
    _delete(f"/{game_id}")
    print(f"\nGame {game_id} deleted.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _random_strategy(
    markets: List[Dict[str, Any]],
    players: List[Dict[str, Any]],
    username: str,
) -> List[tuple]:
    """Generate a random strategy that respects player inventory.

    Only picks 'sell' if the player actually has the market's product.
    """
    # Build set of products this player has in inventory
    player = next((p for p in players if p["username"] == username), None)
    owned_products: set = set()
    if player:
        for item in player.get("inventory", []):
            owned_products.add(item["product"]["name"])

    actions = ["buy", "sell", "skip"]
    strategy: List[tuple] = []
    market_list = list(markets)
    random.shuffle(market_list)
    for m in market_list:
        product = m["product"]
        # Only allow 'sell' if player owns this product
        allowed = actions if product in owned_products else ["buy", "skip"]
        strategy.append((m["market_index"], random.choice(allowed)))
    return strategy


def _wait_phase(game_id: str, phase: str, timeout: float = 30) -> Dict[str, Any]:
    """Poll GET /games/{id} until the phase matches."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = _get(f"/{game_id}")
        if state["phase"] == phase:
            return state
        time.sleep(0.1)
    raise TimeoutError(
        f"Timed out waiting for phase '{phase}'. Got '{state['phase']}'."
    )


def _handle_actions(game_id: str, current_round: int) -> Dict[str, Any]:
    """Handle the action phase, responding to quantity prompts."""
    max_iterations = 200  # Safety valve
    last_msg = ""  # Deduplicate printed messages
    for _ in range(max_iterations):
        state = _get(f"/{game_id}")
        phase = state["phase"]

        if phase == "game_over":
            return state

        if phase != "action":
            # Transitioned to next round's strategy phase or similar
            return state

        msg = state.get("message", "")
        if msg != last_msg:
            print(f"  → {msg}")
            last_msg = msg

        # Check if the API is waiting for a quantity (buy/sell condition met)
        if state.get("can_buy") is True:
            max_aff = state.get("max_affordable", 1)
            qty = random.randint(1, max(max_aff, 1))
            player = state.get("current_player", "?")
            print(f"      {player}: Buying {qty} units (max {max_aff})")
            state = _post(f"/{game_id}/action", {"quantity": qty})

        elif state.get("can_sell") is True:
            max_qty = state.get("seller_qty", 1)
            qty = random.randint(1, max(max_qty, 1))
            player = state.get("current_player", "?")
            print(f"      {player}: Selling {qty} units (max {max_qty})")
            state = _post(f"/{game_id}/action", {"quantity": qty})

        else:
            # Server is processing — small pause before next poll
            time.sleep(0.05)

    print("  ⚠ Action phase exceeded max iterations.")
    return _get(f"/{game_id}")


if __name__ == "__main__":
    main()
