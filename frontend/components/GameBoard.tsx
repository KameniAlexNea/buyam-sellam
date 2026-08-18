"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Results } from "@/lib/types";
import { useGameState } from "@/lib/useGameState";
import { DIFFICULTY_META, phaseLabel } from "@/lib/format";
import PlayerHUD from "./PlayerHUD";
import MarketGrid from "./MarketGrid";
import StrategyPanel from "./StrategyPanel";
import ActionPanel from "./ActionPanel";
import ResultsPanel from "./ResultsPanel";
import GameLog from "./GameLog";
import Leaderboard from "./Leaderboard";

export default function GameBoard({ gameId }: { gameId: string }) {
  const {
    game,
    history,
    loading,
    error,
    humanUsername,
    busy,
    canSubmitStrategy,
    humanActionPending,
    botsStrategizing,
    refresh,
    submitStrategy,
    executeAction,
  } = useGameState(gameId);

  const [results, setResults] = useState<Results | null>(null);

  const gameOver = game?.phase === "game_over";

  // Fetch final results once the game ends.
  useEffect(() => {
    if (gameOver && !results) {
      api
        .results(gameId)
        .then(setResults)
        .catch(() => undefined);
    }
  }, [gameOver, results, gameId]);

  if (loading && !game) {
    return (
      <Shell>
        <div className="flex flex-col items-center justify-center gap-4 py-32">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-gold/30 border-t-gold" />
          <p className="font-display text-sm uppercase tracking-widest text-dim">
            Connecting to the game…
          </p>
        </div>
      </Shell>
    );
  }

  if (error && !game) {
    return (
      <Shell>
        <div className="mx-auto max-w-md rounded-2xl border border-sell/30 bg-card p-8 text-center shadow-card">
          <p className="text-3xl">📡</p>
          <h2 className="mt-3 font-display text-lg font-bold uppercase">
            Can't reach the game
          </h2>
          <p className="mt-2 text-sm text-dim">{error}</p>
          <button
            type="button"
            onClick={() => refresh()}
            className="mt-5 rounded-xl bg-gold px-6 py-2 font-display text-sm font-bold uppercase tracking-widest text-deep"
          >
            Retry
          </button>
          <p className="mt-4 text-xs text-dim">
            Tip: start the backend with{" "}
            <code className="text-cyan">uv run run-server</code> from the repo root.
          </p>
        </div>
      </Shell>
    );
  }

  if (!game) return null;

  const humanPlayer =
    game.players.find((p) => p.username === humanUsername) ?? null;
  const diff = DIFFICULTY_META[game.difficulty] ?? DIFFICULTY_META.medium;

  return (
    <Shell>
      {/* Header / HUD */}
      <header className="flex flex-wrap items-center justify-between gap-3">
        <Link
          href="/"
          className="rounded-lg border border-[rgba(100,180,255,0.2)] bg-card/60 px-3 py-1.5 text-xs font-semibold uppercase tracking-widest text-dim transition-colors hover:border-gold/40 hover:text-gold"
        >
          ← Lobby
        </Link>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-lg bg-card/60 px-3 py-1.5 font-display text-xs font-bold uppercase tracking-widest text-gold border border-gold/20">
            Round {game.round_number} / {game.total_rounds}
          </span>
          <span className={`rounded-lg border px-3 py-1.5 font-display text-xs font-bold uppercase tracking-widest ${diff.tone}`}>
            {diff.label}
          </span>
          <span className="rounded-lg border border-[rgba(100,180,255,0.2)] bg-card/60 px-3 py-1.5 font-display text-xs font-bold uppercase tracking-widest text-cyan">
            {phaseLabel(game.phase)}
          </span>
        </div>
      </header>

      {/* Message banner */}
      {game.message && (
        <div className="animate-fade-in-up rounded-xl border border-[rgba(100,180,255,0.14)] bg-board/70 px-4 py-3 text-sm text-bright shadow-glow">
          {game.message}
        </div>
      )}

      {/* Player HUD */}
      <PlayerHUD
        players={game.players}
        playerRoles={game.player_roles}
        currentPlayer={game.current_player}
        humanUsername={humanUsername}
      />

      {/* Markets */}
      <section>
        <h2 className="mb-3 font-display text-sm font-bold uppercase tracking-[0.2em] text-dim">
          🌐 Active Markets
        </h2>
        <MarketGrid
          markets={game.markets}
          currentMarketIndex={game.current_market_index}
        />
      </section>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_20rem]">
        {/* Main phase panel */}
        <section className="min-w-0">
          {game.phase === "strategy" && canSubmitStrategy && (
            <StrategyPanel
              markets={game.markets}
              humanPlayer={humanPlayer}
              busy={busy}
              onSubmit={submitStrategy}
            />
          )}

          {game.phase === "strategy" && !canSubmitStrategy && (
            <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-6 shadow-card">
              <span className="font-display text-[11px] font-bold uppercase tracking-[0.2em] text-gold">
                🧠 Strategy Phase
              </span>
              <div className="mt-3 flex items-center gap-3">
                {botsStrategizing ? (
                  <>
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-gold/30 border-t-gold" />
                    <p className="text-sm text-dim">
                      Waiting for the bots to lock in their strategies…
                    </p>
                  </>
                ) : (
                  <p className="text-sm text-dim">
                    All strategies are in. Resolving the round…
                  </p>
                )}
              </div>
            </div>
          )}

          {game.phase === "action" && (
            <ActionPanel
              game={game}
              humanUsername={humanUsername}
              busy={busy}
              onExecute={executeAction}
            />
          )}

          {game.phase === "game_over" && (
            <ResultsPanel results={results} humanUsername={humanUsername} />
          )}

          {!["strategy", "action", "game_over"].includes(game.phase) && (
            <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-8 text-center shadow-card">
              <p className="font-display text-sm uppercase tracking-widest text-dim">
                {phaseLabel(game.phase)}
              </p>
              <p className="mt-2 text-sm text-dim">{game.message || "Stand by…"}</p>
            </div>
          )}
        </section>

        {/* Sidebar */}
        <aside className="space-y-6">
          <Leaderboard players={game.players} currentPlayer={game.current_player} />
          <GameLog history={history} />
        </aside>
      </div>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6">
      <div className="text-center">
        <span className="font-display text-[11px] font-bold uppercase tracking-[0.4em] text-gold/80">
          Buyam-Sellam
        </span>
      </div>
      {children}
    </div>
  );
}
