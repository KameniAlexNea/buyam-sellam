import type {
  ActionResult,
  Difficulty,
  GameState,
  History,
  MarketAction,
  Results,
  StrategyInfo,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : JSON.stringify(detail));
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      0,
      `Cannot reach the game server at ${API_BASE}. Is the backend running?`
    );
  }

  if (!res.ok) {
    let detail: unknown = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }

  return (await res.json()) as T;
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  strategies: () => request<StrategyInfo[]>("/strategies"),

  createGame: (body: {
    total_rounds: number;
    difficulty: Difficulty;
  }) =>
    request<GameState>("/games", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getGame: (id: string) => request<GameState>(`/games/${id}`),

  addPlayer: (id: string, body: { username: string; role: string; strategy?: string | null }) =>
    request<GameState>(`/games/${id}/players`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  startGame: (id: string) =>
    request<GameState>(`/games/${id}/start`, { method: "POST" }),

  nextRound: (id: string) =>
    request<GameState>(`/games/${id}/next-round`, { method: "POST" }),

  submitStrategy: (
    id: string,
    body: { username: string; strategy: { market_index: number; action: MarketAction }[] }
  ) =>
    request<GameState>(`/games/${id}/strategy`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  submitBotStrategy: (id: string, body: { username: string; strategy_name: string }) =>
    request<GameState>(`/games/${id}/bot-strategy`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  executeAction: (id: string, quantity: number) =>
    request<ActionResult>(`/games/${id}/action`, {
      method: "POST",
      body: JSON.stringify({ quantity }),
    }),

  executeBotAction: (id: string, body: { strategy_name?: string; quantity?: number }) =>
    request<ActionResult>(`/games/${id}/bot-action`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  results: (id: string) => request<Results>(`/games/${id}/results`),

  history: (id: string) => request<History>(`/games/${id}/history`),
};
