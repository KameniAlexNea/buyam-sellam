# Frontend — Buyam-Sellam Web App

Next.js (App Router) + TailwindCSS game UI for Buyam-Sellam. Dark cyberpunk
trading aesthetic, rendered as a **board game**: market spaces on the four
edges of a plus board, player tokens in the corner home bases, and the dice +
action prompts in the centre (Monopoly / Ludo-King style). Supports hot-seat
**multi-player** (several humans on one screen) plus AI bots.

## Run

```bash
npm install
npm run dev          # → http://localhost:3000
```

The app talks to the FastAPI backend at `http://localhost:8000` by default.
Override with `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Lobby — configure difficulty, rounds, your name and bot opponents, then start |
| `/game/[gameId]` | Live game board — strategy, action, and results phases |

## How it works

- **`lib/useGameState.tsx`** — polls `GET /games/{id}` (and the history feed)
  every ~0.9s. It automatically:
  - submits strategies for bot players (`POST /games/{id}/bot-strategy`) when in
    the **strategy** phase, one at a time;
  - executes bot trades (`POST /games/{id}/bot-action`) when a bot has a pending
    buy/sell in the **action** phase.
- **Multi-player:** every player with `role: human` takes a turn. In the
  strategy phase the hook exposes `currentPlanner` (the next human who hasn't
  planned); in the action phase `humanActionPending` is true whenever the
  current actor is a human with a pending buy/sell — the centre shows their
  quantity prompt.
- The board is rendered by **`Board.tsx`**: 4 corner "home bases" (player
  tokens), market spaces on the 4 edges (tappable during strategy to cycle
  Buy → Sell → Skip), and the phase controls in the centre. The active player's
  corner gets a **PLANNING / TRADING** badge and their token moves onto the
  active market space during the action phase.
- **`TurnTracker.tsx`** is a ribbon above the board that always makes clear
  whose turn it is: the current player's name in their color, plus a status chip
  per player (✓ planned / ◌ planning / … waiting in strategy; turn order with
  dice in action).
- **Persistence & navigation:** progress is saved to `localStorage`
  (`lib/storage.ts`). The lobby offers **▶ Continue** for an in-progress game
  or **View results** after it ends, and the game-over screen has
  **♻️ Rematch** (same table) and **🏠 New Game** buttons. Raw backend hint
  messages (e.g. "Check GET /games/{id}/results") are never shown in the UI.

## Structure

```
frontend/
├── app/
│   ├── layout.tsx          # fonts (Orbitron + Chakra Petch), metadata
│   ├── page.tsx            # lobby
│   ├── globals.css         # Tailwind + theme background
│   └── game/[gameId]/page.tsx
├── components/
│   ├── Lobby.tsx           # create game: humans + bots
│   ├── GameBoard.tsx       # orchestrates the board + phase controls
│   ├── Board.tsx           # plus board: corners, edge markets, centre
│   ├── PlayerToken.tsx     # player tokens (home bases / on tiles)
│   ├── MarketTile.tsx      # a market space on the board edge
│   ├── StrategyPanel.tsx   # compact per-market Buy/Sell/Skip (current planner)
│   ├── ActionPanel.tsx     # dice + quantity prompt in the centre
│   ├── ResultsPanel.tsx    # winner + standings in the centre
│   ├── GameLog.tsx         # collapsible event feed
│   └── Dice.tsx            # animated dice
└── lib/
    ├── api.ts              # typed API client
    ├── types.ts            # shared game types
    ├── format.ts           # money/product/player-colour helpers
    └── useGameState.tsx    # polling hook + bot driver + multi-player logic
```

## Scripts

```bash
npm run dev      # development server
npm run build    # production build
npm run start    # serve the production build
```
