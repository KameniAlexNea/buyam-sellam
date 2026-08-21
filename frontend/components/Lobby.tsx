"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Difficulties, Difficulty, StrategyInfo } from "@/lib/types";
import { buildSavedGame, clearGame, loadGame, saveGame, type SavedGame } from "@/lib/storage";
import GameHeader from "./GameHeader";

const DIFFICULTIES: { value: Difficulty; label: string; blurb: string; cash: number; active: string }[] = [
  {
    value: "easy",
    label: "Easy",
    blurb: "Generous cash, low taxes, calm markets. Best for learning.",
    cash: 80_000,
    active: "border-emerald-500/50 bg-emerald-500/10",
  },
  {
    value: "medium",
    label: "Medium",
    blurb: "The standard Buyam-Sellam experience. Balanced challenge.",
    cash: 50_000,
    active: "border-yellow-500/50 bg-yellow-500/10",
  },
  {
    value: "hard",
    label: "Hard",
    blurb: "Tight budget, heavy taxes, ruthless competition.",
    cash: 30_000,
    active: "border-red-500/50 bg-red-500/10",
  },
];

const BOT_NAMES = [
  "Bot_Alpha",
  "Bot_Beta",
  "Bot_Gamma",
  "Bot_Delta",
  "Bot_Epsilon",
  "Bot_Zeta",
];

interface BotRow {
  name: string;
  strategy: string;
}

export default function Lobby() {
  const router = useRouter();
  const [difficulty, setDifficulty] = useState<Difficulty>("medium");
  const [rounds, setRounds] = useState(10);
  const [humans, setHumans] = useState<string[]>(["You"]);
  // Default: 1 human vs 5 bots — you play only against the (weaker) AI.
  const [bots, setBots] = useState<BotRow[]>(
    BOT_NAMES.slice(0, 5).map((name) => ({ name, strategy: "" }))
  );
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [difficulties, setDifficulties] = useState<Difficulties | null>(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<SavedGame | null>(null);

  // Load the strategy list and the per-difficulty bot rosters, retrying until
  // the backend answers so the dropdown never gets stuck showing one option.
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const load = async () => {
      try {
        const [list, diffs] = await Promise.all([
          api.strategies(),
          api.difficulties(),
        ]);
        if (cancelled) return;
        if (list.length > 0 && diffs) {
          setStrategies(list);
          setDifficulties(diffs);
        } else {
          timer = setTimeout(load, 2500);
        }
      } catch {
        if (!cancelled) timer = setTimeout(load, 2500);
      }
    };
    load();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, []);

  // The strategies a bot may use come from the SELECTED difficulty's pool.
  // Until the difficulty metadata loads, fall back to the full strategy list.
  const allowedStrategies = useMemo<StrategyInfo[]>(() => {
    if (difficulties) return difficulties[difficulty].bot_pool;
    return strategies;
  }, [difficulties, difficulty, strategies]);

  // Easy fixes the bot roster (weak AI) — the user can only change the count.
  const rosterLocked = difficulties?.[difficulty].bot_pool_locked ?? false;

  const labelOf = (name: string) =>
    allowedStrategies.find((s) => s.name === name)?.label ?? name;

  // Keep every bot on a strategy from the current difficulty's pool: when the
  // level loads or changes, bots migrate to that pool automatically.
  useEffect(() => {
    if (allowedStrategies.length === 0) return;
    setBots((prev) =>
      prev.map((b) =>
        allowedStrategies.some((s) => s.name === b.strategy)
          ? b
          : {
              ...b,
              strategy:
                allowedStrategies[
                  Math.floor(Math.random() * allowedStrategies.length)
                ].name,
            }
      )
    );
  }, [allowedStrategies]);

  // Offer to resume the last game saved to localStorage.
  useEffect(() => {
    setSaved(loadGame());
  }, []);

  const usedNames = useMemo(
    () => new Set([...humans, ...bots.map((b) => b.name)]),
    [humans, bots]
  );
  const nextBotName =
    BOT_NAMES.find((n) => !usedNames.has(n)) ?? `Bot_${bots.length + 1}`;

  const addHuman = () => {
    setHumans((prev) => [...prev, `Player ${prev.length + 1}`]);
  };

  const updateHuman = (index: number, value: string) => {
    setHumans((prev) => prev.map((h, i) => (i === index ? value : h)));
  };

  const removeHuman = (index: number) => {
    setHumans((prev) => prev.filter((_, i) => i !== index));
  };

  const addBot = () => {
    if (allowedStrategies.length === 0) return; // roster not loaded yet
    const pick =
      allowedStrategies[Math.floor(Math.random() * allowedStrategies.length)];
    setBots((prev) => [...prev, { name: nextBotName, strategy: pick.name }]);
  };

  const updateBot = (index: number, patch: Partial<BotRow>) => {
    setBots((prev) => prev.map((b, i) => (i === index ? { ...b, ...patch } : b)));
  };

  const removeBot = (index: number) => {
    setBots((prev) => prev.filter((_, i) => i !== index));
  };

  const start = async () => {
    setError(null);
    const humanNames = humans.map((h, i) => h.trim() || `Player ${i + 1}`);
    const allNames = [...humanNames, ...bots.map((b) => b.name)];

    if (allNames.length < 2) {
      setError("You need at least 2 players to start (any mix of players and bots).");
      return;
    }
    if (new Set(allNames).size !== allNames.length) {
      setError("Player names must be unique.");
      return;
    }
    if (allowedStrategies.length === 0) {
      setError("Bot strategies are still loading — wait a moment and try again.");
      return;
    }

    setCreating(true);
    try {
      const game = await api.createGame({
        total_rounds: rounds,
        difficulty,
      });
      for (const name of humanNames) {
        await api.addPlayer(game.game_id, { username: name, role: "human" });
      }
      for (const bot of bots) {
        await api.addPlayer(game.game_id, {
          username: bot.name,
          role: "bot",
          strategy: bot.strategy,
        });
      }
      const started = await api.startGame(game.game_id);
      setSaved(null);
      saveGame(buildSavedGame(started));
      router.push(`/game/${started.game_id}`);
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Failed to create the game. Is the backend running?"
      );
      setCreating(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-8 px-4 py-10 sm:px-6">
      {/* Game-style header */}
      <GameHeader back={false} subtitle="New Game" />

      {/* Hero */}
      <section
        className="relative overflow-hidden rounded-3xl border-2 border-gold/20 bg-gradient-to-br from-card via-board to-deep px-6 py-12 text-center shadow-card"
        style={{
          backgroundImage:
            "url(/bg-pattern.svg), radial-gradient(ellipse at 50% 0%, rgba(255,204,0,0.08), transparent 60%)",
        }}
      >
        <img
          src="/logo-mark.svg"
          alt=""
          className="mx-auto h-28 w-28 sm:h-32 sm:w-32"
          style={{ filter: "drop-shadow(0 0 20px rgba(255,204,0,0.35))" }}
        />
        <h1 className="mx-auto mt-5 font-display text-4xl font-black uppercase tracking-wider sm:text-6xl">
          <span className="text-white">Buyam-</span>
          <span className="text-shimmer">Sellam</span>
        </h1>
        <p className="mt-2 font-display text-[11px] font-bold uppercase tracking-[0.4em] text-gold/80">
          Marketplace Trading Game
        </p>
        <p className="mx-auto mt-6 max-w-xl text-sm leading-relaxed text-dim sm:text-base">
          Buy low, sell high, pay your taxes — and out-trade your rivals for the
          highest balance.
        </p>
      </section>

      {saved && (
        <section className="animate-fade-in-up flex flex-col items-center justify-between gap-3 rounded-2xl border border-gold/30 bg-gradient-to-r from-card via-board to-card px-5 py-4 shadow-glow-gold sm:flex-row">
          <div className="flex items-center gap-3">
            <span className="text-2xl">
              {saved.phase === "game_over" ? "🏆" : "🎮"}
            </span>
            <div>
              <p className="font-display text-sm font-bold uppercase tracking-widest">
                {saved.phase === "game_over" ? "Last game finished" : "Game in progress"}
              </p>
              <p className="text-xs text-dim">
                {saved.phase === "game_over"
                  ? saved.winner
                    ? `Winner: ${saved.winner}`
                    : `Round ${saved.round_number}/${saved.total_rounds}`
                  : `Round ${saved.round_number}/${saved.total_rounds} · ${saved.difficulty}`}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => router.push(`/game/${saved.gameId}`)}
              className="rounded-xl bg-gold px-5 py-2 font-display text-sm font-bold uppercase tracking-widest text-deep transition-all hover:brightness-110 active:scale-95"
            >
              {saved.phase === "game_over" ? "View results" : "▶ Continue"}
            </button>
            <button
              type="button"
              onClick={() => {
                clearGame();
                setSaved(null);
              }}
              className="rounded-xl border border-[rgba(100,180,255,0.2)] px-4 py-2 text-xs font-semibold uppercase tracking-widest text-dim transition-colors hover:text-gold"
            >
              Dismiss
            </button>
          </div>
        </section>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1fr]">
        {/* Setup card */}
        <section className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-6 shadow-card">
          <span className="font-display text-[11px] font-bold uppercase tracking-[0.25em] text-gold">
            ⚙️ Game Setup
          </span>
          <h2 className="mt-1 font-display text-xl font-bold uppercase">
            Configure the table
          </h2>

          {/* Difficulty */}
          <div className="mt-5">
            <p className="mb-2 text-sm font-semibold text-bright">Difficulty</p>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.value}
                  type="button"
                  onClick={() => setDifficulty(d.value)}
                  className={`rounded-xl border p-3 text-left transition-all ${
                    difficulty === d.value
                      ? d.active
                      : "border-[rgba(100,180,255,0.12)] bg-board/40 hover:border-[rgba(100,180,255,0.3)]"
                  }`}
                >
                  <p className="font-display text-sm font-bold uppercase tracking-wide">
                    {d.label}
                  </p>
                  <p className="mt-1 text-[11px] leading-snug text-dim">
                    {d.blurb}
                  </p>
                  <p className="mt-2 font-mono text-[11px] text-buy">
                    {d.cash.toLocaleString()} FCFA start
                  </p>
                </button>
              ))}
            </div>
            {rosterLocked && (
              <p className="mt-2 text-[11px] leading-snug text-dim">
                🔒 This level fixes the bot roster — you can only change the
                number of opponents.
              </p>
            )}
          </div>

          {/* Rounds */}
          <div className="mt-6">
            <div className="mb-2 flex items-center justify-between">
              <p className="text-sm font-semibold text-bright">Rounds</p>
              <span className="rounded-lg bg-board px-2.5 py-0.5 font-display text-sm font-bold text-gold">
                {rounds}
              </span>
            </div>
            <input
              type="range"
              min={1}
              max={20}
              value={rounds}
              onChange={(e) => setRounds(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-[10px] uppercase tracking-widest text-dim">
              <span>1</span>
              <span>20</span>
            </div>
          </div>

          <p className="mt-6 rounded-xl border border-[rgba(100,180,255,0.1)] bg-board/40 p-3 text-[11px] leading-relaxed text-dim">
            🎮 Hot-seat multiplayer: each human player takes their own turn
            planning trades on the same screen. Bots play their AI strategy
            automatically.
          </p>
        </section>

        {/* Players card */}
        <section className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-6 shadow-card">
          <span className="font-display text-[11px] font-bold uppercase tracking-[0.25em] text-gold">
            👥 Players
          </span>
          <h2 className="mt-1 font-display text-xl font-bold uppercase">
            Who's at the table?
          </h2>

          {/* Human players */}
          <div className="mt-5">
            <div className="mb-2 flex items-center justify-between">
              <p className="text-sm font-semibold text-bright">
                Players <span className="text-dim">({humans.length})</span>
              </p>
              <button
                type="button"
                onClick={addHuman}
                className="rounded-lg border border-gold/30 bg-gold/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-gold transition-colors hover:bg-gold/20"
              >
                + Add player
              </button>
            </div>

            <div className="space-y-2">
              {humans.map((name, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 rounded-xl border border-[rgba(100,180,255,0.08)] bg-board/50 p-2"
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gold font-display text-sm font-black text-deep">
                    {(name.trim() || `Player ${i + 1}`).slice(0, 1).toUpperCase()}
                  </span>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => updateHuman(i, e.target.value)}
                    maxLength={50}
                    placeholder={`Player ${i + 1}`}
                    className="flex-1 rounded-lg border border-[rgba(100,180,255,0.15)] bg-card px-3 py-1.5 text-sm text-bright outline-none transition-colors focus:border-gold/50"
                  />
                  <button
                    type="button"
                    onClick={() => removeHuman(i)}
                    disabled={humans.length <= 1}
                    className="h-8 w-8 shrink-0 rounded-lg border border-sell/30 text-sell transition-colors hover:bg-sell/10 disabled:cursor-not-allowed disabled:opacity-30"
                    aria-label={`Remove player ${i + 1}`}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Bots */}
          <div className="mt-6">
            <div className="mb-2 flex items-center justify-between">
              <p className="text-sm font-semibold text-bright">
                Bot opponents <span className="text-dim">({bots.length})</span>
              </p>
              <button
                type="button"
                onClick={addBot}
                disabled={allowedStrategies.length === 0}
                className="rounded-lg border border-gold/30 bg-gold/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-gold transition-colors hover:bg-gold/20 disabled:cursor-not-allowed disabled:opacity-40"
              >
                + Add bot
              </button>
            </div>

            <div className="space-y-2">
              {bots.map((bot, i) => (
                <div
                  key={bot.name}
                  className="flex items-center gap-2 rounded-xl border border-[rgba(100,180,255,0.08)] bg-board/50 p-2"
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-violet to-accent font-display text-sm font-bold">
                    🤖
                  </span>
                  <span className="flex-1 truncate text-sm font-semibold">
                    {bot.name}
                  </span>
                  {rosterLocked ? (
                    <span
                      title="Fixed by difficulty — you can only change the number of opponents"
                      className="shrink-0 rounded-lg border border-[rgba(100,180,255,0.15)] bg-card/60 px-2 py-1.5 text-[11px] text-dim"
                    >
                      🔒 {labelOf(bot.strategy)}
                    </span>
                  ) : (
                    <select
                      value={bot.strategy}
                      onChange={(e) => updateBot(i, { strategy: e.target.value })}
                      className="rounded-lg border border-[rgba(100,180,255,0.2)] bg-card px-2 py-1.5 text-xs text-bright outline-none focus:border-gold/50"
                    >
                      {allowedStrategies.length === 0 ? (
                        <option value="">Loading strategies…</option>
                      ) : (
                        allowedStrategies.map((s) => (
                          <option key={s.name} value={s.name}>
                            {s.label}
                          </option>
                        ))
                      )}
                    </select>
                  )}
                  <button
                    type="button"
                    onClick={() => removeBot(i)}
                    className="h-8 w-8 shrink-0 rounded-lg border border-sell/30 text-sell transition-colors hover:bg-sell/10"
                    aria-label={`Remove ${bot.name}`}
                  >
                    ✕
                  </button>
                </div>
              ))}

              {bots.length === 0 && (
                <p className="text-xs italic text-dim">
                  No bots — just you humans. Add one to fill an empty seat.
                </p>
              )}
            </div>
          </div>

          <p className="mt-4 text-xs leading-relaxed text-dim">
            {difficulties
              ? `${difficulties[difficulty].label} bots: ${difficulties[
                  difficulty
                ].bot_pool
                  .map((s) => s.label)
                  .join(" · ")}.`
              : "Loading bot roster…"}
            {rosterLocked &&
              " You can only change the number of opponents — the roster is fixed."}
          </p>
        </section>
      </div>

      {error && (
        <div className="rounded-xl border border-sell/30 bg-sell/10 px-4 py-3 text-sm text-sell">
          {error}
        </div>
      )}

      <div className="flex justify-center pb-8">
        <button
          type="button"
          onClick={start}
          disabled={creating}
          className="rounded-2xl bg-gold px-12 py-4 font-display text-lg font-black uppercase tracking-widest text-deep shadow-glow-gold transition-all hover:brightness-110 active:scale-95 disabled:opacity-50"
        >
          {creating ? "Dealing the markets…" : "🎲 Start Game"}
        </button>
      </div>
    </div>
  );
}
