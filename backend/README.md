# Backend — Buyam-Sellam API

FastAPI game server for the Buyam-Sellam marketplace trading game.

## Run

From the repo root:

```bash
uv sync
uv run run-server        # → http://localhost:8000
```

or directly:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Interactive docs at <http://localhost:8000/docs>.

## Structure

```
backend/
├── app/               # FastAPI application
│   ├── main.py        #   app factory, CORS, /health, /strategies
│   ├── routes.py      #   game lifecycle endpoints + bot endpoints
│   ├── schemas.py     #   Pydantic request/response models
│   └── state_manager.py  # file persistence under out/{game_id}/
├── ksell/             # core game logic (framework-agnostic)
│   ├── model/         #   Table, Player, MarketBoard, Dice, ProductModel, DifficultyConfig
│   ├── pojo/          #   Market, Product, User dataclasses
│   ├── strategy.py    #   AI bot strategies
│   └── utils/         #   random helpers
└── out/               # per-game state files (gitignored)
```

## Endpoints

All game routes live under `/games` (see the full table in the [root README](../README.md)).

Notable additions for the web UI:

- `POST /games/{id}/bot-strategy` — body `{username, strategy_name}`. Computes a
  bot's per-market choices with the named AI strategy and submits them.
- `POST /games/{id}/bot-action` — body `{strategy_name?, quantity?}`. Executes
  the current pending action for the current player; if `quantity` is omitted
  the strategy picks one.
- `GET /games/{id}/history` — full event feed for the game log.
- `GET /strategies` — lists available bot strategies.

Players can be tagged when added:

```json
{ "username": "Bot_Alpha", "role": "bot", "strategy": "buylowsellhigh" }
```

The state returned by `GET /games/{id}` includes `player_roles`, letting clients
know who is a human and who is a bot.

## Persistence

State is kept in-memory per process and flushed to `out/{game_id}/state.json` on
every transition; an append-only `out/{game_id}/history.json` records events.
Restarting the server clears the in-memory games (the files remain).
