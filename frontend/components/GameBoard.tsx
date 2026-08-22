"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Difficulty, MarketAction, Results } from "@/lib/types";
import { useGameState } from "@/lib/useGameState";
import { DIFFICULTY_META } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { buildSavedGame, clearGame, saveGame } from "@/lib/storage";
import Board from "./Board";
import GameHeader from "./GameHeader";
import BotTurnDashboard from "./BotTurnDashboard";
import StrategyDashboard from "./StrategyDashboard";
import ActionDashboard from "./ActionDashboard";
import ResultsPanel from "./ResultsPanel";
import RoundRecapPanel from "./RoundRecapPanel";
import NewsTicker from "./NewsTicker";
import GameLog from "./GameLog";

const CYCLE: MarketAction[] = ["skip", "buy", "sell"];

export default function GameBoard({ gameId }: { gameId: string }) {
  const {
    game,
    history,
    loading,
    error,
    notFound,
    humanPlayers,
    isHuman,
    currentPlanner,
    busy,
    canSubmitStrategy,
    botsStrategizing,
    refresh,
    refreshHistory,
    submitStrategy,
    executeAction,
    nextRound,
  } = useGameState(gameId);

  const [results, setResults] = useState<Results | null>(null);
  const [choices, setChoices] = useState<Record<number, MarketAction>>({});
  const [showLog, setShowLog] = useState(false);
  const [navError, setNavError] = useState<string | null>(null);
  const [confirmRematch, setConfirmRematch] = useState(false);
  const [rematching, setRematching] = useState(false);
  const router = useRouter();
  const { t } = useI18n();

  const gameOver = game?.phase === "game_over";

  // The game no longer exists on the server (backend restart wiped the
  // in-memory state). Drop the stale save and let the player start fresh.
  useEffect(() => {
    if (notFound) clearGame();
  }, [notFound]);

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

  // Fetch the event log only while it's actually open (and re-fetch when the
  // round or phase advances so it stays fresh). No background polling.
  useEffect(() => {
    if (showLog) refreshHistory();
  }, [showLog, game?.round_number, game?.phase, refreshHistory]);

  if (notFound) {
    return (
      <Shell>
        <div className="mx-auto max-w-md rounded-2xl border border-dim/30 bg-card p-8 text-center shadow-card">
          <p className="text-3xl">🕳️</p>
          <h2 className="mt-3 font-display text-lg font-bold uppercase">
            {t("board.goneTitle")}
          </h2>
          <p className="mt-2 text-sm text-dim">{t("board.goneBody")}</p>
          <button
            type="button"
            onClick={() => router.push("/")}
            className="mt-5 rounded-xl bg-gold px-6 py-2 font-display text-sm font-bold uppercase tracking-widest text-deep"
          >
            {t("board.backLobby")}
          </button>
        </div>
      </Shell>
    );
  }

  if (loading && !game) {
    return (
      <Shell>
        <div className="flex flex-col items-center justify-center gap-4 py-32">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-gold/30 border-t-gold" />
          <p className="font-display text-sm uppercase tracking-widest text-dim">
            {t("board.connecting")}
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
            {t("board.unreachable")}
          </h2>
          <p className="mt-2 text-sm text-dim">{error}</p>
          <button
            type="button"
            onClick={() => refresh()}
            className="mt-5 rounded-xl bg-gold px-6 py-2 font-display text-sm font-bold uppercase tracking-widest text-deep"
          >
            {t("board.retry")}
          </button>
          <p className="mt-4 text-xs text-dim">
            {t("board.tip")}{" "}
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
  // Guarded by a confirmation dialog so it can't fire by accident.
  const requestRematch = () => {
    if (!game) return;
    setConfirmRematch(true);
  };

  const doRematch = async () => {
    if (!game) return;
    setConfirmRematch(false);
    setRematching(true);
    setNavError(null);
    try {
      const fresh = await api.createGame({
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
              ? (game.player_roles[p.username]?.strategy ?? null)
              : null,
        });
      }
      const started = await api.startGame(fresh.game_id);
      saveGame(buildSavedGame(started));
      router.push(`/game/${started.game_id}`);
    } catch (e) {
      setNavError(
        e instanceof ApiError ? e.message : t("board.rematchFail")
      );
    } finally {
      setRematching(false);
    }
  };

  let center: React.ReactNode;
  if (game.phase === "game_over") {
    center = (
      <div className="flex w-full flex-col items-center gap-3">
        <ResultsPanel
          results={results}
          humanPlayers={humanPlayers}
          onRematch={requestRematch}
          onNewGame={newGame}
        />
        {navError && <p className="text-xs text-sell">{navError}</p>}
      </div>
    );
  } else {
    center = <Waiting text={game.message || t(`phase.${game.phase}`)} />;
  }

  return (
    <Shell>
      {/* Game-style header: back left, title center, badges + controls right */}
      <div className="shrink-0">
        <GameHeader
          subtitle={t(`phase.${game.phase}`)}
          badges={
            <>
              <span className="rounded-lg bg-card/60 px-3 py-1.5 font-display text-xs font-bold uppercase tracking-widest text-gold border border-gold/20">
                {t("round", { round: game.round_number, total: game.total_rounds })}
              </span>
              <span className={`rounded-lg border px-3 py-1.5 font-display text-xs font-bold uppercase tracking-widest ${diff.tone}`}>
                {diff.label}
              </span>
            </>
          }
          actions={
            <button
              type="button"
              onClick={() => setShowLog((v) => !v)}
              className="rounded-lg border border-[rgba(100,180,255,0.2)] bg-card/60 px-3 py-1.5 text-xs font-semibold uppercase tracking-widest text-dim transition-colors hover:border-gold/40 hover:text-gold"
            >
              {showLog ? t("log.hide") : t("log.show")}
            </button>
          }
        />
      </div>

      {/* Market news ticker (strategy & action phases) */}
      {["strategy", "action"].includes(game.phase) && game.news.length > 0 && (
        <div className="shrink-0">
          <NewsTicker items={game.news} />
        </div>
      )}

      {/* Compact message (transitions only) */}
      {game.message && !["strategy", "action", "end_round", "game_over"].includes(game.phase) && (
        <div className="shrink-0">
          <p className="animate-fade-in-up truncate rounded-lg border border-[rgba(100,180,255,0.12)] bg-board/50 px-3 py-1.5 text-center text-xs text-bright">
            {game.message}
          </p>
        </div>
      )}

      {/* Phase content fills the remaining viewport height on desktop; each
          panel scrolls internally instead of scrolling the whole page. */}
      <div className="min-h-0 flex-1">
        {game.phase === "strategy" ? (
          <StrategyDashboard
            game={game}
            planner={currentPlanner ?? ""}
            plannerPlayer={plannerPlayer}
            choices={choices}
            onChoice={onChoice}
            busy={busy}
            canSubmit={canSubmitStrategy}
            onConfirm={confirmStrategy}
          />
        ) : game.phase === "action" && isHumanTurn ? (
          <ActionDashboard game={game} busy={busy} onExecute={executeAction} />
        ) : game.phase === "action" ? (
          // Bot's action turn — same dashboard look, but auto-driven replay.
          <BotTurnDashboard game={game} />
        ) : game.phase === "end_round" && game.round_recap ? (
          // Round-end recap gets the full width — the "what happened" moment.
          <div className="mx-auto h-full w-full max-w-2xl overflow-y-auto">
            <RoundRecapPanel
              recap={game.round_recap}
              humanPlayers={humanPlayers}
              moveFeed={game.move_feed}
              busy={busy}
              onNext={nextRound}
            />
          </div>
        ) : game.phase === "game_over" ? (
          // Final results get the full width — no board decorations around them.
          <div className="mx-auto h-full w-full max-w-2xl overflow-y-auto">{center}</div>
        ) : (
          <div className="h-full overflow-y-auto">
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
          </div>
        )}
      </div>

      {/* Optional event log */}
      {showLog && (
        <div className="animate-fade-in-up rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3 shadow-card">
          <GameLog history={history} />
        </div>
      )}

      {/* Rematch confirmation dialog */}
      {confirmRematch && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="animate-fade-in-up w-full max-w-sm rounded-2xl border border-gold/30 bg-card p-6 text-center shadow-glow-gold">
            <p className="text-3xl">♻️</p>
            <h3 className="mt-2 font-display text-lg font-black uppercase tracking-wide">
              {t("board.rematchTitle")}
            </h3>
            <p className="mt-2 text-sm text-dim">{t("board.rematchBody")}</p>
            <div className="mt-5 flex gap-2">
              <button
                type="button"
                onClick={() => setConfirmRematch(false)}
                disabled={rematching}
                className="flex-1 rounded-xl border border-[rgba(100,180,255,0.2)] bg-card/60 px-4 py-2.5 font-display text-xs font-bold uppercase tracking-widest text-bright transition-all hover:border-gold/40 hover:text-gold"
              >
                {t("board.cancel")}
              </button>
              <button
                type="button"
                onClick={doRematch}
                disabled={rematching}
                className="flex-1 rounded-xl bg-gold px-4 py-2.5 font-display text-xs font-bold uppercase tracking-widest text-deep shadow-glow-gold transition-all hover:brightness-110 active:scale-95 disabled:opacity-50"
              >
                {rematching ? "…" : t("board.yesRematch")}
              </button>
            </div>
          </div>
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
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-2 overflow-hidden px-4 py-3 sm:px-6 lg:h-dvh">
      <div className="shrink-0 text-center">
        <span className="font-display text-[11px] font-bold uppercase tracking-[0.4em] text-gold/80">
          Buyam-Sellam
        </span>
      </div>
      <div className="flex min-h-0 flex-1 flex-col gap-2">{children}</div>
    </div>
  );
}
