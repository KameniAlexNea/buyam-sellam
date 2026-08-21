"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "./api";
import type { GameState, HistoryEntry, MarketAction } from "./types";

const POLL_MS = 900; // poll while a bot needs driving

// Polling is strictly action-driven: requests are only made while a bot is
// being driven. When it's a human's turn (or any state where nothing can
// change until the player acts), zero requests are sent.

export interface StrategyChoice {
  market_index: number;
  action: MarketAction;
}

export interface UseGameState {
  game: GameState | null;
  history: HistoryEntry[];
  loading: boolean;
  error: string | null;
  /** true when the game no longer exists on the server (404). */
  notFound: boolean;
  /** usernames of all human-controlled players. */
  humanPlayers: string[];
  isHuman: (username: string) => boolean;
  /** the human whose strategy is currently due (strategy phase), or null. */
  currentPlanner: string | null;
  /** true while a bot submission / action is being driven. */
  busy: boolean;
  /** true when there is a human still due to plan (strategy phase). */
  canSubmitStrategy: boolean;
  /** true when a human has a pending buy/sell action to confirm. */
  humanActionPending: boolean;
  /** true when bots are still submitting strategies this round. */
  botsStrategizing: boolean;
  refresh: () => Promise<void>;
  refreshHistory: () => Promise<void>;
  submitStrategy: (username: string, choices: StrategyChoice[]) => Promise<void>;
  executeAction: (quantity: number) => Promise<void>;
}

function isBot(game: GameState, username: string): boolean {
  return game.player_roles[username]?.role === "bot";
}

function botStrategy(game: GameState, username: string): string {
  // Bots always get a strategy from the backend at creation, so this is
  // effectively always set; empty string means "not ready yet".
  return game.player_roles[username]?.strategy ?? "";
}

/**
 * True when a bot still needs driving (strategy to submit or action to take),
 * i.e. when fast polling actually does something. On a human's turn nothing
 * can change server-side until the human acts, so fast polling is waste.
 */
function needsLivePolling(game: GameState | null): boolean {
  if (!game) return true;
  if (game.phase === "strategy") {
    // Bots still planning -> they must be driven forward.
    return game.players.some(
      (p) => isBot(game, p.username) && !game.strategies_submitted.includes(p.username)
    );
  }
  if (game.phase === "action") {
    // A bot whose buy/sell is due -> drive it.
    return !!game.current_player && isBot(game, game.current_player);
  }
  // Human's turn, transition, waiting, or game over: nothing moves on its
  // own, so there is nothing to poll for.
  return false;
}

/**
 * Polls the backend for a game, automatically submits strategies for bot
 * players and executes their buy/sell actions, and exposes helpers so every
 * human player (hot-seat) can submit their own strategy and act on their turn.
 */
export function useGameState(gameId: string): UseGameState {
  const [game, setGame] = useState<GameState | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [busy, setBusy] = useState(false);

  const gameRef = useRef<GameState | null>(null);
  const driving = useRef(false);

  const refresh = useCallback(async () => {
    const next = await api.getGame(gameId);
    gameRef.current = next;
    setGame(next);
    setNotFound(false);
    setError(null);
    setLoading(false);
  }, [gameId]);

  // History is only needed when the player opens the log — never poll it.
  const refreshHistory = useCallback(async () => {
    const hist = await api.history(gameId).catch(() => null);
    if (hist) setHistory(hist.history);
  }, [gameId]);

  // Drive bots: keep executing consecutive bot steps (submit pending bot
  // strategies, then bot buy/sell actions) until it's a human's turn again or
  // there is nothing left to drive. This is the ONLY thing that should ever
  // trigger requests outside of a human explicitly acting.
  const drive = useCallback(async () => {
    if (driving.current) return;
    driving.current = true;
    setBusy(true);
    try {
      while (needsLivePolling(gameRef.current)) {
        const g = gameRef.current;
        if (!g) break;

        if (g.phase === "strategy") {
          const pending = g.players.find(
            (p) => isBot(g, p.username) && !g.strategies_submitted.includes(p.username)
          );
          if (!pending) break;
          const strat = botStrategy(g, pending.username);
          if (!strat) {
            // Bot has no strategy assigned yet — wait for the poll loop.
            break;
          }
          await api.submitBotStrategy(g.game_id, {
            username: pending.username,
            strategy_name: strat,
          });
          await refresh();
          continue;
        }

        if (g.phase === "action") {
          const cur = g.current_player;
          if (!cur || !isBot(g, cur) || !(g.can_buy || g.can_sell)) break;
          const strat = botStrategy(g, cur);
          if (!strat) {
            break;
          }
          await api.executeBotAction(g.game_id, {
            strategy_name: strat,
          });
          await refresh();
          continue;
        }

        // Any other phase — nothing to drive.
        break;
      }
    } catch (e) {
      if (e instanceof ApiError && e.status === 400) {
        // Transient race (e.g. action already executed) — refresh and move on.
        await refresh().catch(() => undefined);
      }
    } finally {
      driving.current = false;
      setBusy(false);
    }
  }, [refresh]);

  // Polling loop: requests happen ONLY while a bot needs driving. As soon as
  // it's a human's turn, scheduling stops -> zero requests. A human acting
  // (submitStrategy / executeAction) re-triggers refresh + drive, which resumes
  // bot-driving until it's back to a human turn. Hidden tab = zero requests.
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const schedule = (ms: number) => {
      if (!cancelled) timer = setTimeout(tick, ms);
    };

    const tick = async () => {
      if (cancelled) return;
      // Never poll a hidden tab.
      if (typeof document !== "undefined" && document.hidden) return;
      try {
        await refresh();
        await drive();
      } catch (e) {
        if (!cancelled) {
          setLoading(false);
          if (e instanceof ApiError && e.status === 404) {
            // The game was wiped (backend restart, etc.) — stop polling it.
            setNotFound(true);
            return; // do NOT reschedule
          }
          setError(
            e instanceof ApiError
              ? e.message
              : "Something went wrong talking to the game server."
          );
        }
      }
      // Only keep polling if there is actually bot work left to do.
      if (needsLivePolling(gameRef.current)) schedule(POLL_MS);
    };

    const onVisibility = () => {
      // Tab came back into view — refresh once and resume if bots need driving.
      if (typeof document !== "undefined" && document.visibilityState === "visible") {
        if (timer) clearTimeout(timer);
        tick();
      }
    };

    tick();
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [refresh, drive]);

  const humanPlayers =
    game?.players.filter((p) => !isBot(game, p.username)).map((p) => p.username) ??
    [];

  const isHuman = useCallback(
    (username: string) => (game ? !isBot(game, username) : false),
    [game]
  );

  const currentPlanner =
    game?.phase === "strategy"
      ? (humanPlayers.find(
          (u) => !game.strategies_submitted.includes(u)
        ) ?? null)
      : null;

  const canSubmitStrategy = currentPlanner != null;

  const humanActionPending =
    !!game &&
    game.phase === "action" &&
    !!game.current_player &&
    isHuman(game.current_player) &&
    (!!game.can_buy || !!game.can_sell);

  const botsStrategizing =
    !!game &&
    game.phase === "strategy" &&
    game.players.some(
      (p) => isBot(game, p.username) && !game.strategies_submitted.includes(p.username)
    );

  const submitStrategy = useCallback(
    async (username: string, choices: StrategyChoice[]) => {
      await api.submitStrategy(gameId, { username, strategy: choices });
      await refresh();
      await drive();
    },
    [gameId, refresh, drive]
  );

  const executeAction = useCallback(
    async (quantity: number) => {
      await api.executeAction(gameId, quantity);
      await refresh();
      await drive();
    },
    [gameId, refresh, drive]
  );

  return {
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
    humanActionPending,
    botsStrategizing,
    refresh,
    refreshHistory,
    submitStrategy,
    executeAction,
  };
}
