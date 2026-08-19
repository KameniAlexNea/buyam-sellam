import type { GameState } from "./types";

/** Snapshot of a game persisted to localStorage so you can resume after a reload. */
export interface SavedGame {
  gameId: string;
  difficulty: string;
  total_rounds: number;
  starting_balance: number;
  players: { username: string; role: string; strategy: string | null }[];
  phase: string;
  round_number: number;
  winner: string | null;
  updated_at: string;
}

const KEY = "buyam-sellam:lastGame";

export function buildSavedGame(game: GameState, winner?: string | null): SavedGame {
  return {
    gameId: game.game_id,
    difficulty: game.difficulty,
    total_rounds: game.total_rounds,
    starting_balance: 50_000,
    players: game.players.map((p) => ({
      username: p.username,
      role: game.player_roles[p.username]?.role ?? "human",
      strategy: game.player_roles[p.username]?.strategy ?? null,
    })),
    phase: game.phase,
    round_number: game.round_number,
    winner: winner ?? null,
    updated_at: new Date().toISOString(),
  };
}

export function saveGame(entry: SavedGame): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(entry));
  } catch {
    /* storage unavailable (private mode, etc.) */
  }
}

export function loadGame(): SavedGame | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SavedGame;
  } catch {
    return null;
  }
}

export function clearGame(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* noop */
  }
}
