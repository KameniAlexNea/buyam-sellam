"use client";

import type { Results } from "@/lib/types";
import { money, productMeta, TONE_CLASSES } from "@/lib/format";

interface ResultsPanelProps {
  results: Results | null;
  humanPlayers?: string[];
}

const RANK_STYLES: Record<number, string> = {
  1: "border-gold/50 bg-gold/10",
  2: "border-slate-400/40 bg-slate-400/10",
  3: "border-orange-500/40 bg-orange-500/10",
};

export default function ResultsPanel({ results, humanPlayers }: ResultsPanelProps) {
  if (!results) {
    return (
      <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-8 text-center shadow-card">
        <p className="text-dim">Fetching final results…</p>
      </div>
    );
  }

  const winner = results.standings[0];

  return (
    <div className="animate-fade-in-up">
      {/* Winner banner */}
      <div className="relative mb-6 overflow-hidden rounded-2xl border-2 border-gold/30 bg-gradient-to-br from-card via-board to-deep p-8 text-center shadow-glow-gold">
        <span className="font-display text-[11px] font-bold uppercase tracking-[0.3em] text-gold">
          🏆 Winner
        </span>
        <h2 className="mt-2 font-display text-4xl font-black uppercase tracking-wider text-shimmer">
          {results.winner}
        </h2>
        <p className="mt-2 text-sm text-dim">
          Final balance{" "}
          <span className="font-semibold text-buy">{money(winner.final_balance)}</span>{" "}
          · {winner.profit_loss >= 0 ? "+" : ""}
          {money(winner.profit_loss)} vs starting{" "}
          {money(results.starting_balance)}
        </p>
      </div>

      {/* Standings */}
      <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-5 shadow-card">
        <h3 className="mb-4 font-display text-lg font-bold uppercase tracking-wide">
          Final Standings
        </h3>
        <div className="space-y-2">
          {results.standings.map((s) => {
            const isHuman = humanPlayers?.includes(s.username) ?? false;
            return (
              <div
                key={s.username}
                className={`flex items-center gap-4 rounded-xl border p-3 ${
                  RANK_STYLES[s.rank] ?? "border-[rgba(100,180,255,0.08)] bg-board/50"
                }`}
              >
                <span className="w-8 text-center font-display text-2xl font-black text-gold">
                  {s.rank}
                </span>
                <div className="flex-1">
                  <p className="font-semibold">
                    {s.username}
                    {isHuman && s.username !== "You" && (
                      <span className="ml-2 rounded-full bg-gold/15 px-2 py-0.5 text-[10px] font-bold uppercase text-gold border border-gold/30">
                        You
                      </span>
                    )}
                  </p>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {s.inventory.length === 0 ? (
                      <span className="text-xs italic text-dim">no inventory</span>
                    ) : (
                      s.inventory.map((it) => {
                        const meta = productMeta(it.product.name);
                        return (
                          <span
                            key={it.product.name}
                            className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[11px] ${TONE_CLASSES[meta.tone]}`}
                          >
                            {meta.icon} {it.quantity}
                          </span>
                        );
                      })
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-display text-lg font-bold text-bright">
                    {money(s.final_balance)}
                  </p>
                  <p
                    className={`text-xs font-semibold ${
                      s.profit_loss >= 0 ? "text-buy" : "text-sell"
                    }`}
                  >
                    {s.profit_loss >= 0 ? "▲" : "▼"} {money(Math.abs(s.profit_loss))}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
