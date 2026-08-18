"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Difficulty, StrategyInfo } from "@/lib/types";
import Dice from "./Dice";

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
  const [rounds, setRounds] = useState(5);
  const [humanName, setHumanName] = useState("You");
  const [bots, setBots] = useState<BotRow[]>([
    { name: "Bot_Alpha", strategy: "buylowsellhigh" },
    { name: "Bot_Beta", strategy: "aggressivebuyer" },
  ]);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .strategies()
      .then(setStrategies)
      .catch(() => setStrategies([]));
  }, []);

  const usedNames = useMemo(
    () => new Set([humanName, ...bots.map((b) => b.name)]),
    [humanName, bots]
  );
  const nextBotName = BOT_NAMES.find((n) => !usedNames.has(n)) ?? `Bot_${bots.length + 1}`;

  const addBot = () => {
    setBots((prev) => [
      ...prev,
      { name: nextBotName, strategy: "buylowsellhigh" },
    ]);
  };

  const updateBot = (index: number, patch: Partial<BotRow>) => {
    setBots((prev) => prev.map((b, i) => (i === index ? { ...b, ...patch } : b)));
  };

  const removeBot = (index: number) => {
    setBots((prev) => prev.filter((_, i) => i !== index));
  };

  const start = async () => {
    setError(null);
    const name = humanName.trim() || "You";
    if (bots.length < 1) {
      setError("Add at least one bot opponent to start the game.");
      return;
    }
    setCreating(true);
    try {
      const game = await api.createGame({
        starting_balance: 50_000,
        total_rounds: rounds,
        difficulty,
      });
      await api.addPlayer(game.game_id, { username: name, role: "human" });
      for (const bot of bots) {
        await api.addPlayer(game.game_id, {
          username: bot.name,
          role: "bot",
          strategy: bot.strategy,
        });
      }
      await api.startGame(game.game_id);
      router.push(`/game/${game.game_id}`);
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Failed to create the game. Is the backend running?"
      );
      setCreating(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-8 px-4 py-10 sm:px-6">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl border-2 border-gold/20 bg-gradient-to-br from-card via-board to-deep px-6 py-12 text-center shadow-card">
        <span className="font-display text-[11px] font-bold uppercase tracking-[0.4em] text-gold">
          🎲 Marketplace Trading Game
        </span>
        <h1 className="text-shimmer mt-4 font-display text-5xl font-black uppercase tracking-wider sm:text-7xl">
          Buyam-Sellam
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-dim sm:text-base">
          Roll the dice, read the markets, and trade your way to riches. Buy low,
          sell high, pay your taxes — and out-trade the bots for the highest
          balance.
        </p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <Dice die1={4} die2={5} total={9} label="" size="lg" rolling />
        </div>
      </section>

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
              max={10}
              value={rounds}
              onChange={(e) => setRounds(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-[10px] uppercase tracking-widest text-dim">
              <span>1</span>
              <span>10</span>
            </div>
          </div>
        </section>

        {/* Players card */}
        <section className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-6 shadow-card">
          <span className="font-display text-[11px] font-bold uppercase tracking-[0.25em] text-gold">
            👥 Players
          </span>
          <h2 className="mt-1 font-display text-xl font-bold uppercase">
            You vs the bots
          </h2>

          <div className="mt-5">
            <label className="mb-2 block text-sm font-semibold text-bright">
              Your name
            </label>
            <input
              type="text"
              value={humanName}
              onChange={(e) => setHumanName(e.target.value)}
              maxLength={50}
              className="w-full rounded-xl border border-[rgba(100,180,255,0.2)] bg-board px-4 py-2.5 text-bright outline-none transition-colors focus:border-gold/50"
              placeholder="You"
            />
          </div>

          <div className="mt-5 space-y-2.5">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-bright">Bot opponents</p>
              <button
                type="button"
                onClick={addBot}
                className="rounded-lg border border-gold/30 bg-gold/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-gold transition-colors hover:bg-gold/20"
              >
                + Add bot
              </button>
            </div>

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
                <select
                  value={bot.strategy}
                  onChange={(e) => updateBot(i, { strategy: e.target.value })}
                  className="rounded-lg border border-[rgba(100,180,255,0.2)] bg-card px-2 py-1.5 text-xs text-bright outline-none focus:border-gold/50"
                >
                  {(strategies.length > 0 ? strategies : []).map((s) => (
                    <option key={s.name} value={s.name}>
                      {s.label}
                    </option>
                  ))}
                  {strategies.length === 0 && (
                    <option value="buylowsellhigh">BuyLowSellHigh</option>
                  )}
                </select>
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
                No bots — add at least one opponent to play.
              </p>
            )}
          </div>

          <p className="mt-4 text-xs text-dim">
            Each bot plays an AI strategy: BuyLowSellHigh hunts margins,
            AggressiveBuyer hoards stock, ConservativeTrader plays it safe,
            and MarketSniper targets value markets.
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
