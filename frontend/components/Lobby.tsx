"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
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
  "Mama_Tchop",
  "Mami_Ben",
  "Papa_Ngassa",
  "Tata_Ndounou",
  "Na_Bella",
  "Uncle_Martin",
  "Sister_Marie",
  "Brother_Etienne",
  "Madam_Flore",
  "Monsieur_Pierre",
];

interface BotRow {
  name: string;
  strategy: string;
}

export default function Lobby() {
  const router = useRouter();
  const { t } = useI18n();
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
  // 3-step guided setup: 1) start/continue, 2) difficulty, 3) opponent profile.
  const [step, setStep] = useState(1);
  const stepDefs = [
    { n: 1, icon: "🎮", label: t("lobby.step1Label") },
    { n: 2, icon: "🎚️", label: t("lobby.step2Label") },
    { n: 3, icon: "🤖", label: t("lobby.step3Label") },
  ];

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

  // Opponent count is tied to difficulty: Easy seats 0-4, Medium 4-8, Hard
  // 6-10 (more traders drain market supply = harder). With 2+ humans the limit
  // is lifted — the humans already raise the complexity, so the table can be
  // configured freely up to the free cap.
  const humanCount = humans.length;
  const botRange = useMemo<[number, number]>(() => {
    if (!difficulties) return [0, 12];
    if (humanCount >= 2) return [0, difficulties[difficulty].free_max_bots];
    return difficulties[difficulty].bot_range;
  }, [difficulties, difficulty, humanCount]);
  const minBots = botRange[0];
  const maxBots = botRange[1];

  const freshName = (used: Set<string>): string => {
    for (const n of BOT_NAMES) if (!used.has(n)) return n;
    // Pool exhausted (only possible with 2+ humans and >10 bots): reuse a base
    // name with a numeral suffix instead of falling back to a generic "Bot_1".
    const base = BOT_NAMES[used.size % BOT_NAMES.length];
    let k = 2;
    while (used.has(`${base}_${k}`)) k += 1;
    return `${base}_${k}`;
  };

  // Keep the table size inside the difficulty's range: trim when a level is
  // too big, top up when it needs more opponents. The roster adapts to the
  // difficulty, just like the strategy pool does.
  useEffect(() => {
    if (!difficulties) return;
    setBots((prev) => {
      let list = prev;
      if (list.length > maxBots) list = list.slice(0, maxBots);
      if (list.length < minBots) {
        const next = [...list];
        const used = new Set([...humans, ...next.map((b) => b.name)]);
        while (next.length < minBots) {
          const name = freshName(used);
          used.add(name);
          const strat = allowedStrategies.length
            ? allowedStrategies[
                Math.floor(Math.random() * allowedStrategies.length)
              ].name
            : "";
          next.push({ name, strategy: strat });
        }
        list = next;
      }
      return list;
    });
  }, [difficulties, difficulty, humanCount, minBots, maxBots, allowedStrategies]);

  // Offer to resume the last game saved to localStorage.
  useEffect(() => {
    setSaved(loadGame());
  }, []);

  const usedNames = useMemo(
    () => new Set([...humans, ...bots.map((b) => b.name)]),
    [humans, bots]
  );
  const nextBotName = freshName(usedNames);

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
    if (bots.length >= maxBots) return; // difficulty seat cap reached
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
      setError(t("lobby.errMinPlayers"));
      return;
    }
    if (new Set(allNames).size !== allNames.length) {
      setError(t("lobby.errUniqueNames"));
      return;
    }
    if (allowedStrategies.length === 0) {
      setError(t("lobby.errLoading"));
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
        e instanceof ApiError ? e.message : t("lobby.errCreate")
      );
      setCreating(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-6">
      {/* Game-style header */}
      <GameHeader back={false} subtitle={t("lobby.subtitle")} />

      {/* Step indicator: Start → Difficulty → Opponents */}
      <nav className="flex items-center justify-center gap-2 sm:gap-3" aria-label="Setup steps">
        {stepDefs.map((s) => {
          const active = step === s.n;
          const done = step > s.n;
          return (
            <button
              key={s.n}
              type="button"
              onClick={() => done && setStep(s.n)}
              className={`flex items-center gap-2 rounded-full border px-3 py-1.5 font-display text-[11px] font-bold uppercase tracking-widest transition-all ${
                active
                  ? "border-gold/50 bg-gold/10 text-gold shadow-glow-gold"
                  : done
                  ? "border-buy/40 bg-buy/5 text-buy/80 cursor-pointer hover:border-buy/70"
                  : "border-[rgba(100,180,255,0.12)] bg-card/40 text-dim/60"
              }`}
            >
              <span className="text-sm">{done ? "✓" : s.icon}</span>
              <span>{s.n}. {s.label}</span>
            </button>
          );
        })}
      </nav>

      {/* STEP 1 — Start / Continue */}
      {step === 1 && (
        <div className="animate-fade-in-up space-y-4">
          <section
            className="relative overflow-hidden rounded-3xl border-2 border-gold/20 bg-gradient-to-br from-card via-board to-deep px-6 py-10 text-center shadow-card"
            style={{
              backgroundImage:
                "url(/bg-pattern.svg), radial-gradient(ellipse at 50% 0%, rgba(255,204,0,0.08), transparent 60%)",
            }}
          >
            <img
              src="/logo-mark.svg"
              alt=""
              className="mx-auto h-24 w-24 sm:h-28 sm:w-28"
              style={{ filter: "drop-shadow(0 0 20px rgba(255,204,0,0.35))" }}
            />
            <h1 className="mt-4 font-display text-3xl font-black uppercase tracking-wider text-shimmer sm:text-4xl">
              {t("lobby.stepStart")}
            </h1>
            <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-dim">
              {t("lobby.stepStartBody")}
            </p>
          </section>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {saved && (
              <button
                type="button"
                onClick={() => router.push(`/game/${saved.gameId}`)}
                className="group flex flex-col items-start gap-3 rounded-2xl border border-gold/30 bg-gradient-to-br from-card via-board to-card p-5 text-left shadow-glow-gold transition-all hover:brightness-110 active:scale-[0.99]"
              >
                <span className="text-3xl">{saved.phase === "game_over" ? "🏆" : "🎮"}</span>
                <div>
                  <p className="font-display text-sm font-bold uppercase tracking-widest text-gold">
                    {saved.phase === "game_over" ? t("lobby.viewResults") : t("lobby.continueGame")}
                  </p>
                  <p className="mt-1 text-xs text-dim">
                    {saved.phase === "game_over"
                      ? saved.winner
                        ? t("lobby.winner", { name: saved.winner })
                        : t("lobby.roundProgress", { round: saved.round_number, total: saved.total_rounds })
                      : t("lobby.roundProgressDiff", {
                          round: saved.round_number,
                          total: saved.total_rounds,
                          diff: saved.difficulty,
                        })}
                  </p>
                </div>
              </button>
            )}

            <button
              type="button"
              onClick={() => setStep(2)}
              className="group flex flex-col items-start gap-3 rounded-2xl border border-[rgba(100,180,255,0.15)] bg-card p-5 text-left shadow-card transition-all hover:border-gold/40 hover:bg-board/60 active:scale-[0.99]"
            >
              <span className="text-3xl">🎲</span>
              <div>
                <p className="font-display text-sm font-bold uppercase tracking-widest text-bright">
                  {t("lobby.newGame")}
                </p>
                <p className="mt-1 text-xs text-dim">{t("lobby.newGameDesc")}</p>
              </div>
              <span className="mt-1 rounded-lg bg-gold/10 px-3 py-1 font-display text-[10px] font-bold uppercase tracking-widest text-gold transition-colors group-hover:bg-gold/20">
                {t("lobby.next")}
              </span>
            </button>
          </div>

          {saved && (
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => {
                  clearGame();
                  setSaved(null);
                }}
                className="text-xs font-semibold uppercase tracking-widest text-dim transition-colors hover:text-gold"
              >
                {t("lobby.dismiss")}
              </button>
            </div>
          )}
        </div>
      )}

      {/* STEP 2 — Select difficulty */}
      {step === 2 && (
        <div className="animate-fade-in-up space-y-4">
          <section className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-6 shadow-card">
            <h2 className="font-display text-xl font-bold uppercase text-gold">
              {t("lobby.stepDifficulty")}
            </h2>
            <p className="mt-1 text-sm text-dim">{t("lobby.stepDifficultyBody")}</p>

            {/* Difficulty */}
            <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.value}
                  type="button"
                  onClick={() => setDifficulty(d.value)}
                  className={`rounded-xl border p-4 text-left transition-all ${
                    difficulty === d.value
                      ? `${d.active} scale-[1.02] shadow-glow-gold`
                      : "border-[rgba(100,180,255,0.12)] bg-board/40 hover:border-[rgba(100,180,255,0.3)]"
                  }`}
                >
                  <p className="font-display text-base font-bold uppercase tracking-wide">
                    {d.label}
                  </p>
                  <p className="mt-1 text-[11px] leading-snug text-dim">
                    {t(`diff.${d.value}.blurb`)}
                  </p>
                  <p className="mt-2 font-mono text-[11px] text-buy">
                    {t("diff.cashStart", { amount: d.cash.toLocaleString() })}
                  </p>
                  {difficulties && (
                    <p className="mt-1 font-mono text-[11px] text-cyan">
                      {t("lobby.opponentsRange", {
                        min: difficulties[d.value].bot_range[0],
                        max: difficulties[d.value].bot_range[1],
                      })}
                    </p>
                  )}
                </button>
              ))}
            </div>
            {rosterLocked && (
              <p className="mt-3 text-[11px] leading-snug text-dim">
                {t("lobby.difficultyLocked")}
              </p>
            )}

            <div className="mt-6 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="rounded-xl border border-[rgba(100,180,255,0.2)] px-5 py-2.5 font-display text-xs font-bold uppercase tracking-widest text-dim transition-colors hover:text-gold"
              >
                {t("lobby.back")}
              </button>
              <button
                type="button"
                onClick={() => setStep(3)}
                className="rounded-xl bg-gold px-7 py-2.5 font-display text-xs font-black uppercase tracking-widest text-deep shadow-glow-gold transition-all hover:brightness-110 active:scale-95"
              >
                {t("lobby.next")}
              </button>
            </div>
          </section>
        </div>
      )}

      {/* STEP 3 — Choose opponent profile */}
      {step === 3 && (
        <div className="animate-fade-in-up space-y-4">
          <section className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-6 shadow-card">
            <h2 className="font-display text-xl font-bold uppercase text-gold">
              {t("lobby.stepOpponents")}
            </h2>
            <p className="mt-1 text-sm text-dim">{t("lobby.stepOpponentsBody")}</p>

            {/* Rounds */}
            <div className="mt-5">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-semibold text-bright">{t("lobby.rounds")}</p>
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

            {/* Human players */}
            <div className="mt-6">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-semibold text-bright">
                  {t("players")}{" "}
                  <span className="text-dim">({humans.length})</span>
                </p>
                <button
                  type="button"
                  onClick={addHuman}
                  className="rounded-lg border border-gold/30 bg-gold/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-gold transition-colors hover:bg-gold/20"
                >
                  {t("lobby.addPlayer")}
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
                  {t("lobby.botOpponents")}{" "}
                  <span className="text-dim">({bots.length})</span>
                </p>
                <button
                  type="button"
                  onClick={addBot}
                  disabled={allowedStrategies.length === 0 || bots.length >= maxBots}
                  className="rounded-lg border border-gold/30 bg-gold/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-gold transition-colors hover:bg-gold/20 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {t("lobby.addBot")}
                </button>
              </div>

              {difficulties && (
                <p className="mb-2 text-[11px] leading-snug text-dim">
                  {humanCount >= 2
                    ? t("lobby.multiHumans", { max: maxBots })
                    : t("lobby.seats", { min: minBots, max: maxBots })}
                </p>
              )}

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
                      disabled={bots.length <= minBots}
                      className="h-8 w-8 shrink-0 rounded-lg border border-sell/30 text-sell transition-colors hover:bg-sell/10 disabled:cursor-not-allowed disabled:opacity-30"
                      aria-label={`Remove ${bot.name}`}
                    >
                      ✕
                    </button>
                  </div>
                ))}

                {bots.length === 0 && (
                  <p className="text-xs italic text-dim">
                    {t("lobby.noBots")}
                  </p>
                )}
              </div>
            </div>

            <p className="mt-4 text-xs leading-relaxed text-dim">
              {difficulties
                ? t("lobby.botRoster", {
                    label: difficulties[difficulty].label,
                    list: difficulties[difficulty].bot_pool
                      .map((s) => s.label)
                      .join(" · "),
                  })
                : t("lobby.loadingRoster")}
              {rosterLocked && t("lobby.rosterLocked")}
            </p>

            {error && (
              <div className="mt-4 rounded-xl border border-sell/30 bg-sell/10 px-4 py-3 text-sm text-sell">
                {error}
              </div>
            )}

            <div className="mt-6 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="rounded-xl border border-[rgba(100,180,255,0.2)] px-5 py-2.5 font-display text-xs font-bold uppercase tracking-widest text-dim transition-colors hover:text-gold"
              >
                {t("lobby.back")}
              </button>
              <button
                type="button"
                onClick={start}
                disabled={creating}
                className="rounded-2xl bg-gold px-10 py-3.5 font-display text-base font-black uppercase tracking-widest text-deep shadow-glow-gold transition-all hover:brightness-110 active:scale-95 disabled:opacity-50"
              >
                {creating ? t("lobby.dealing") : t("lobby.startGame")}
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
