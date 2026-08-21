"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "./api";
import type { GameState, HistoryEntry, MarketAction } from "./types";

const POLL_MS = 900;

export interface StrategyChoice {
  market_index: number;
  action: MarketAction;
}

export interface UseGameState {
  game: GameState | null;
  history: HistoryEntry[];
  loading: boolean;
  error: string | null;
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
 * Polls the backend for a game, automatically submits strategies for bot
 * players and executes their buy/sell actions, and exposes helpers so every
 * human player (hot-seat) can submit their own strategy and act on their turn.
 */
export function useGameState(gameId: string): UseGameState {
  const [game, setGame] = useState<GameState | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const gameRef = useRef<GameState | null>(null);
  const driving = useRef(false);

  const refresh = useCallback(async () => {
    const next = await api.getGame(gameId);
    gameRef.current = next;
    setGame(next);
    setError(null);
    setLoading(false);
  }, [gameId]);

  // History is only needed when the player opens the log — never poll it.
  const refreshHistory = useCallback(async () => {
    const hist = await api.history(gameId).catch(() => null);
    if (hist) setHistory(hist.history);
  }, [gameId]);

  // Drive bots: submit pending bot strategies, then execute bot actions.
  const drive = useCallback(async () => {
    const g = gameRef.current;
    if (!g || driving.current) return;
    driving.current = true;
    setBusy(true);
    try {
      if (g.phase === "strategy") {
        const pending = g.players.find(
          (p) => isBot(g, p.username) && !g.strategies_submitted.includes(p.username)
        );
        if (pending) {
          const strat = botStrategy(g, pending.username);
          if (!strat) {
            // Bot has no strategy assigned yet — wait for the backend.
            await refresh();
            return;
          }
          await api.submitBotStrategy(g.game_id, {
            username: pending.username,
            strategy_name: strat,
          });
          await refresh();
          return;
        }
      }

      if (g.phase === "action") {
        const cur = g.current_player;
        if (cur && isBot(g, cur) && (g.can_buy || g.can_sell)) {
          const strat = botStrategy(g, cur);
          if (!strat) {
            await refresh();
            return;
          }
          await api.executeBotAction(g.game_id, {
            strategy_name: strat,
          });
          await refresh();
          return;
        }
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

  // Polling loop.
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const tick = async () => {
      if (cancelled) return;
      try {
        await refresh();
        await drive();
      } catch (e) {
        if (!cancelled) {
          setLoading(false);
          setError(
            e instanceof ApiError
              ? e.message
              : "Something went wrong talking to the game server."
          );
        }
      } finally {
        if (!cancelled) timer = setTimeout(tick, POLL_MS);
      }
    };

    tick();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
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
