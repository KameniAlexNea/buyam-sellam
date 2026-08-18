# Buyam-Sellam

A marketplace trading **game** — roll the dice, read the markets, buy low, sell
high, pay your taxes, and out-trade your rivals.

This is a **front + backend** web app:

| Part | Stack | Folder |
|------|-------|--------|
| Backend | FastAPI (Python) | [`backend/`](./backend) |
| Frontend | Next.js + TailwindCSS (TypeScript) | [`frontend/`](./frontend) |

## Game Overview

- Roll **2d6** every round — your dice total sets your buying/selling price
  (dice × 100 FCFA).
- Each active market trades **one product** at a fixed price, with a supply,
  a tax rate and an entry fee.
- **Buy** when your dice price is high enough; **sell** when the market will pay
  you a good price. There's an order book, market auto-buys, pending market
  purchases and even forced sales to cover taxes.
- Compete against **AI bots** (each running a different strategy) for the highest
  final balance. The winner takes the crown.

You play as the **human** player in a shared browser; bots auto-submit their
strategies and auto-execute their trades, so the round resolves live in front of
you.

## Project Structure

```
buyam-sellam/
├── backend/            # FastAPI game server
│   ├── app/            #   main.py, routes.py, schemas.py, state_manager.py
│   ├── ksell/          #   core game logic (Table, Player, MarketBoard, ...)
│   └── out/            #   per-game state files (gitignored)
├── frontend/           # Next.js + Tailwind web UI
│   ├── app/            #   App Router pages (lobby + game)
│   ├── components/     #   game UI components
│   └── lib/            #   API client, types, game-state hook (bot driver)
├── pyproject.toml      # Backend deps (uv) + scripts
├── tox.ini             # format / test
└── .gitignore
```

## Quick Start

### 1. Backend

```bash
uv sync                      # install Python deps (fastapi, uvicorn, ...)
uv run run-server            # start API on http://localhost:8000
```

Or manually:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

- API docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

> Note: game state is held in-memory on the server. Restarting the backend
> clears active games (their `backend/out/*` state files remain on disk).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                  # open http://localhost:3000
```

The frontend talks to the backend at `http://localhost:8000` by default. To
point it elsewhere, create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Play

1. Open <http://localhost:3000>.
2. Pick a difficulty and number of rounds.
3. Enter your name, add one or more bots (each with an AI strategy), and hit
   **Start Game**.
4. Each round: choose **Buy / Sell / Skip** per market and submit. Bots finalize
   theirs automatically and the round resolves live — watch the dice, the
   turn order and the trade feed.
5. When the game ends you get a full results leaderboard with profit/loss.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/strategies` | List available AI bot strategies |
| `POST` | `/games` | Create a game |
| `GET` | `/games` | List games |
| `GET` | `/games/{id}` | Get game state |
| `DELETE` | `/games/{id}` | Delete a game |
| `POST` | `/games/{id}/players` | Add a player (`role: human\|bot`, optional `strategy`) |
| `POST` | `/games/{id}/start` | Start the game |
| `POST` | `/games/{id}/strategy` | Submit a human player's strategy |
| `POST` | `/games/{id}/bot-strategy` | Compute & submit a bot's strategy |
| `POST` | `/games/{id}/action` | Execute the current action (human, with quantity) |
| `POST` | `/games/{id}/bot-action` | Execute the current action (bot, auto quantity) |
| `GET` | `/games/{id}/results` | Final results (game over) |
| `GET` | `/games/{id}/history` | Event history feed |

## Game Flow

```
CREATED → SETUP → STRATEGY → ACTION → (rounds...) → GAME_OVER
```

- **STRATEGY** — every player picks buy/sell/skip per active market.
- **ACTION** — players act in dice-roll turn order; buys/sells happen at the
  dice-derived price. The game pauses when it's your turn and you can buy/sell.
- **GAME_OVER** — final standings with winner and profit/loss.

## Bots

Built-in AI strategies live in `backend/ksell/strategy.py`:

- `buylowsellhigh` — classic arbitrage
- `aggressivebuyer` — hoards stock at max quantity
- `conservativetrader` — only trades on very favorable conditions
- `marketsniper` — targets high-supply, low-price markets
- `random` — baseline

## Development

```bash
tox -e format     # format + lint with ruff (backend)
tox -e test       # run pytest suite (when added)
```
