"use client";

import type { RoundRecap } from "@/lib/types";
import { money, playerColor } from "@/lib/format";
import { useI18n } from "@/lib/i18n";

interface RoundRecapPanelProps {
  recap: RoundRecap;
  humanPlayers?: string[];
  busy?: boolean;
  onNext: () => void;
}

/**
 * The "what happened this round" moment: shown between rounds. Summarizes each
 * player's balance change and the market news, with a button to advance.
 */
export default function RoundRecapPanel({
  recap,
  humanPlayers,
  busy,
  onNext,
}: RoundRecapPanelProps) {
  const { t } = useI18n();
  const sorted = [...recap.players].sort((a, b) => b.change - a.change);
  const leader = sorted[0];
  const laggard = sorted[sorted.length - 1];
  const colorOf = (name: string) =>
    playerColor(Math.max(0, sorted.findIndex((p) => p.username === name)));

  return (
    <div className="animate-fade-in-up w-full">
      {/* Header */}
      <div className="mb-4 text-center">
        <span className="font-display text-[11px] font-bold uppercase tracking-[0.3em] text-gold">
          {t("recap.roundComplete", { round: recap.round })}
        </span>
        <h2 className="mt-1 font-display text-2xl font-black uppercase tracking-wider text-shimmer">
          {t("recap.whatHappened")}
        </h2>
      </div>

      {/* Leader + laggard strip */}
      <div className="mb-4 grid grid-cols-2 gap-3">
        <div className="rounded-2xl border border-buy/30 bg-buy/5 p-4 text-center">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-buy">
            {t("recap.best")}
          </p>
          <p className="mt-1 font-display text-lg font-black text-buy">{leader.username}</p>
          <p className="text-sm font-bold text-bright">
            {leader.change >= 0 ? "+" : ""}
            {money(leader.change)}
          </p>
        </div>
        <div className="rounded-2xl border border-sell/30 bg-sell/5 p-4 text-center">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-sell">
            {t("recap.fellBehind")}
          </p>
          <p className="mt-1 font-display text-lg font-black text-sell">{laggard.username}</p>
          <p className="text-sm font-bold text-bright">
            {laggard.change >= 0 ? "+" : ""}
            {money(laggard.change)}
          </p>
        </div>
      </div>

      {/* Per-player rows */}
      <div className="mb-4 rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-4">
        <h3 className="mb-3 font-display text-sm font-bold uppercase tracking-wide">
          {t("recap.balances")}
        </h3>
        <div className="flex flex-col gap-1.5">
          {sorted.map((p) => {
            const c = colorOf(p.username);
            const isHuman = humanPlayers?.includes(p.username) ?? false;
            const deltaCls = p.change > 0 ? "text-buy" : p.change < 0 ? "text-sell" : "text-dim";
            return (
              <div key={p.username} className="flex items-center gap-2 rounded-lg border border-[rgba(100,180,255,0.08)] bg-board/40 px-3 py-2 text-[13px]">
                <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-black ${c.avatar}`}>
                  {p.username.slice(0, 1).toUpperCase()}
                </span>
                <span className={`truncate font-semibold ${isHuman ? c.text : "text-bright"}`}>
                  {p.username}
                </span>
                <span className="ml-auto font-display font-bold text-cyan">{money(p.balance)}</span>
                <span className={`w-24 shrink-0 text-right font-display font-bold ${deltaCls}`}>
                  {p.change > 0 ? "▲ +" : p.change < 0 ? "▼ −" : ""}
                  {p.change !== 0 ? money(Math.abs(p.change)) : "—"}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Market news */}
      {recap.news.length > 0 && (
        <div className="mb-4 rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-4">
          <h3 className="mb-2 font-display text-sm font-bold uppercase tracking-wide">
            {t("recap.marketNews")}
          </h3>
          <div className="flex flex-col gap-1.5">
            {recap.news.map((n, i) => (
              <p
                key={i}
                className={`rounded-lg border px-3 py-2 text-[12px] ${
                  n.tone === "up"
                    ? "border-buy/25 bg-buy/5 text-bright"
                    : n.tone === "down"
                    ? "border-sell/25 bg-sell/5 text-bright"
                    : "border-[rgba(100,180,255,0.08)] bg-board/40 text-dim"
                }`}
              >
                {n.tone === "up" ? "📈" : n.tone === "down" ? "📉" : "➖"} {n.text}
              </p>
            ))}
          </div>
        </div>
      )}

      {/* Advance */}
      <button
        type="button"
        onClick={onNext}
        disabled={busy}
        className="w-full rounded-xl bg-gold py-3 font-display text-sm font-black uppercase tracking-widest text-deep shadow-glow-gold transition-all hover:brightness-110 active:scale-[0.99] disabled:opacity-50"
      >
        {busy
          ? "…"
          : recap.is_last
          ? t("recap.seeResults")
          : t("recap.startNext", { round: recap.round + 1 })}
      </button>
    </div>
  );
}
