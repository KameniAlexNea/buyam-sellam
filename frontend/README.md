# Frontend — Buyam-Sellam Web App

Next.js (App Router) + TailwindCSS game UI for Buyam-Sellam. Dark
cyberpunk trading aesthetic: gold hero, neon buy/sell accents, dice rolls,
a live trade feed and an auto-resolving game loop.

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
- The human player (first player with `role: human`) gets the **StrategyPanel**
  each round and a **quantity prompt** in the **ActionPanel** when the game
  pauses on their buy/sell.

## Structure

```
frontend/
├── app/
│   ├── layout.tsx          # fonts (Orbitron + Chakra Petch), metadata
│   ├── page.tsx            # lobby
│   ├── globals.css         # Tailwind + theme background
│   └── game/[gameId]/page.tsx
├── components/
│   ├── Lobby.tsx           # create game + bots
│   ├── GameBoard.tsx       # orchestrates the live board
│   ├── PlayerHUD.tsx       # player cards: balance + inventory
│   ├── MarketGrid.tsx      # market cards (price, tax, supply, entry fee)
│   ├── StrategyPanel.tsx   # per-market Buy/Sell/Skip for the human
│   ├── ActionPanel.tsx     # dice, turn order, quantity prompt
│   ├── ResultsPanel.tsx    # winner banner + final standings
│   ├── Leaderboard.tsx     # live ranking sidebar
│   ├── GameLog.tsx         # event feed
│   └── Dice.tsx            # animated dice
└── lib/
    ├── api.ts              # typed API client
    ├── types.ts            # shared game types
    ├── format.ts           # money/product/phase helpers
    └── useGameState.tsx    # polling hook + bot driver
```

## Scripts

```bash
npm run dev      # development server
npm run build    # production build
npm run start    # serve the production build
```
