# buyam-sellam

A business simulation / marketplace game with a FastAPI REST API.

## Game Overview

Buyam-Sellam is a marketplace simulation game where players:
- Roll dice (2d6) to determine buy/sell conditions
- Trade products in dynamic markets with taxes and entry fees
- Manage inventory and balance across multiple rounds
- Compete with other players for the highest final balance

## Project Structure

```
buyam-sellam/
├── game.py                  # CLI game (reference implementation)
├── pyproject.toml           # Dependencies & scripts
├── app/                     # FastAPI web service
│   ├── main.py              # App entry point
│   ├── routes.py            # All API endpoints
│   ├── schemas.py           # Pydantic request/response models
│   └── state_manager.py     # File-based state persistence
├── ksell/                   # Core game logic (unchanged)
│   ├── model/               # Table, Player, MarketBoard, Dice, ProductModel
│   ├── pojo/                # User, Product, Market data classes
│   ├── simulate/            # Automated simulation
│   └── utils/               # Random utilities
└── out/                     # Game state files (one folder per game)
```

## Installation

```bash
uv sync
```

## Running the API Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API docs are available at `http://localhost:8000/docs`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/games` | Create a new game |
| `GET` | `/games` | List all games |
| `GET` | `/games/{id}` | Get game state |
| `DELETE` | `/games/{id}` | Delete a game |
| `POST` | `/games/{id}/players` | Add a player |
| `POST` | `/games/{id}/start` | Start the game |
| `POST` | `/games/{id}/strategy` | Submit a player's strategy |
| `POST` | `/games/{id}/action` | Execute buy/sell with quantity |
| `GET` | `/games/{id}/results` | Get final results (game over) |

## Quick Start (curl)

```bash
# Create a game
GAME=$(curl -s -X POST http://localhost:8000/games \
  -H 'Content-Type: application/json' \
  -d '{"starting_balance": 50000, "total_rounds": 3}')
ID=$(echo $GAME | python3 -c "import sys,json; print(json.load(sys.stdin)['game_id'])")

# Add players
curl -s -X POST http://localhost:8000/games/$ID/players \
  -H 'Content-Type: application/json' -d '{"username": "alice"}'
curl -s -X POST http://localhost:8000/games/$ID/players \
  -H 'Content-Type: application/json' -d '{"username": "bob"}'

# Start the game
curl -s -X POST http://localhost:8000/games/$ID/start

# Submit strategies (each player)
curl -s -X POST http://localhost:8000/games/$ID/strategy \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","strategy":[{"market_index":1,"action":"buy"}]}'
curl -s -X POST http://localhost:8000/games/$ID/strategy \
  -H 'Content-Type: application/json' \
  -d '{"username":"bob","strategy":[{"market_index":1,"action":"sell"}]}'

# Execute actions (when can_buy or can_sell is true)
curl -s -X POST http://localhost:8000/games/$ID/action \
  -H 'Content-Type: application/json' -d '{"quantity": 10}'

# Get results (when phase is game_over)
curl -s http://localhost:8000/games/$ID/results
```

## Game Flow

```
CREATED → SETUP → ROUND_START → STRATEGY → TURN_ORDER → ACTION → END_ROUND
                                                                    ↓
                                                    (back to ROUND_START or GAME_OVER)
```

Each phase transition writes the full state to `out/{game_id}/state.json` and appends to `out/{game_id}/history.json`.

## Game Mechanics

### Dice Rolling
- Two dice (1-6 each) determine market conditions
- Total range: 2-12
- Higher rolls = better market conditions

### Markets
- Each market has a location with min/max quantity range
- Tax rate applied to total quantity
- Players can pass through or sell in markets

### Player Economy
- Fortune: Player's wealth
- Cards: Collectible game cards
- Subscribers: Social network followers
- Competitions: Number of games played
- Stars: Achievement rating
