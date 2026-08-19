"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Difficulty, MarketAction, Results } from "@/lib/types";
import { useGameState } from "@/lib/useGameState";
import { DIFFICULTY_META, phaseLabel } from "@/lib/format";
import { buildSavedGame, saveGame } from "@/lib/storage";
import Board from "./Board";
import TurnTracker from "./TurnTracker";
import StrategyPanel from "./StrategyPanel";
import ActionPanel from "./ActionPanel";
import ResultsPanel from "./ResultsPanel";
import GameLog from "./GameLog";

const CYCLE: MarketAction[] = ["skip", "buy", "sell"];

export default function GameBoard({ gameId }: { gameId: string }) {
  const {
    game,
    history,
    loading,
    error,
    humanPlayers,
    isHuman,
    currentPlanner,
    busy,
    canSubmitStrategy,
    botsStrategizing,
    refresh,
    submitStrategy,
    executeAction,
  } = useGameState(gameId);

  const [results, setResults] = useState<Results | null>(null);
  const [choices, setChoices] = useState<Record<number, MarketAction>>({});
  const [showLog, setShowLog] = useState(false);
  const [navError, setNavError] = useState<string | null>(null);
  const router = useRouter();

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

  // Persist progress to localStorage so the game can be resumed after a reload.
  useEffect(() => {
    if (game) saveGame(buildSavedGame(game, results?.winner ?? null));
  }, [game, results]);

  // Fresh plan selections each time a new planner takes the stage.
  useEffect(() => {
    setChoices({});
  }, [game?.round_number, currentPlanner]);

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

  const diff = DIFFICULTY_META[game.difficulty] ?? DIFFICULTY_META.medium;
  const plannerPlayer =
    game.players.find((p) => p.username === currentPlanner) ?? null;
  const isHumanTurn =
    game.phase === "action" && !!game.current_player && isHuman(game.current_player);

  // Tap a market tile on the board to cycle Skip → Buy → Sell.
  const onMarketTap = (index: number) => {
    if (!currentPlanner) return;
    setChoices((prev) => {
      const cur = prev[index] ?? "skip";
      const next = CYCLE[(CYCLE.indexOf(cur) + 1) % CYCLE.length];
      return { ...prev, [index]: next };
    });
  };

  const onChoice = (index: number, action: MarketAction) => {
    setChoices((prev) => ({ ...prev, [index]: action }));
  };

  const confirmStrategy = async () => {
    if (!currentPlanner) return;
    const strategy = game.markets.map((m) => ({
      market_index: m.market_index,
      action: choices[m.market_index] ?? "skip",
    }));
    await submitStrategy(currentPlanner, strategy);
  };

  const newGame = () => router.push("/");

  // Start a fresh game with the exact same table (difficulty, rounds, players).
  const rematch = async () => {
    if (!game) return;
    setNavError(null);
    try {
      const fresh = await api.createGame({
        starting_balance: 50_000,
        total_rounds: game.total_rounds,
        difficulty: game.difficulty as Difficulty,
      });
      for (const p of game.players) {
        const role = game.player_roles[p.username]?.role ?? "human";
        await api.addPlayer(fresh.game_id, {
          username: p.username,
          role,
          strategy:
            role === "bot"
              ? (game.player_roles[p.username]?.strategy ?? "buylowsellhigh")
              : null,
        });
      }
      const started = await api.startGame(fresh.game_id);
      saveGame(buildSavedGame(started));
      router.push(`/game/${started.game_id}`);
    } catch (e) {
      setNavError(
        e instanceof ApiError ? e.message : "Could not start a rematch."
      );
    }
  };

  let center: React.ReactNode;
  if (game.phase === "strategy" && canSubmitStrategy) {
    center = (
      <StrategyPanel
        markets={game.markets}
        planner={currentPlanner ?? ""}
        plannerPlayer={plannerPlayer}
        choices={choices}
        onChoice={onChoice}
        busy={busy}
        onConfirm={confirmStrategy}
      />
    );
  } else if (game.phase === "strategy") {
    center = (
      <Waiting
        text={
          botsStrategizing
            ? "Waiting for the bots to plan…"
            : "All plans are in — resolving the round…"
        }
      />
    );
  } else if (game.phase === "action") {
    center = (
      <ActionPanel
        game={game}
        isHumanTurn={isHumanTurn}
        busy={busy}
        onExecute={executeAction}
      />
    );
  } else if (game.phase === "game_over") {
    center = (
      <div className="flex w-full flex-col items-center gap-3">
        <ResultsPanel
          results={results}
          humanPlayers={humanPlayers}
          onRematch={rematch}
          onNewGame={newGame}
        />
        {navError && <p className="text-xs text-sell">{navError}</p>}
      </div>
    );
  } else {
    center = <Waiting text={game.message || phaseLabel(game.phase)} />;
  }

  return (
    <Shell>
      {/* Header */}
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
          <button
            type="button"
            onClick={() => setShowLog((v) => !v)}
            className="rounded-lg border border-[rgba(100,180,255,0.2)] bg-card/60 px-3 py-1.5 text-xs font-semibold uppercase tracking-widest text-dim transition-colors hover:border-gold/40 hover:text-gold"
          >
            {showLog ? "Hide" : "📜"} Log
          </button>
        </div>
      </header>

      {/* Whose turn is it — shown on the strategy & action phases */}
      {["strategy", "action"].includes(game.phase) && (
        <TurnTracker
          game={game}
          currentPlanner={currentPlanner}
          humanPlayers={humanPlayers}
        />
      )}

      {/* Compact message (transitions only) */}
      {game.message && !["strategy", "action", "game_over"].includes(game.phase) && (
        <p className="animate-fade-in-up truncate rounded-lg border border-[rgba(100,180,255,0.12)] bg-board/50 px-3 py-1.5 text-center text-xs text-bright">
          {game.message}
        </p>
      )}

      {/* The board */}
      <Board
        players={game.players}
        playerRoles={game.player_roles}
        markets={game.markets}
        phase={game.phase}
        humanPlayers={humanPlayers}
        currentPlayer={game.current_player}
        currentPlanner={currentPlanner}
        currentMarketIndex={game.current_market_index}
        choices={choices}
        onMarketTap={onMarketTap}
        center={center}
      />

      {/* Optional event log */}
      {showLog && (
        <div className="animate-fade-in-up rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3 shadow-card">
          <GameLog history={history} />
        </div>
      )}
    </Shell>
  );
}

function Waiting({ text }: { text: string }) {
  return (
    <div className="flex flex-col items-center gap-3 px-4 text-center">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-gold/30 border-t-gold" />
      <p className="text-sm text-dim">{text}</p>
    </div>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto max-w-5xl space-y-4 px-4 py-6 sm:px-6">
      <div className="text-center">
        <span className="font-display text-[11px] font-bold uppercase tracking-[0.4em] text-gold/80">
          Buyam-Sellam
        </span>
      </div>
      {children}
    </div>
  );
}
