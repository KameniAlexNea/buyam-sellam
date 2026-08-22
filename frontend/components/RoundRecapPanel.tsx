"use client";

import { useMemo } from "react";
import type { MoveFeedEntry, RoundRecap } from "@/lib/types";
import { money, playerColor, productMeta, TONE_CLASSES } from "@/lib/format";
import { useI18n } from "@/lib/i18n";

interface RoundRecapPanelProps {
  recap: RoundRecap;
  humanPlayers?: string[];
  moveFeed?: MoveFeedEntry[];
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
  moveFeed,
  busy,
  onNext,
}: RoundRecapPanelProps) {
  const { t } = useI18n();
  const MEDALS = ["🥇", "🥈", "🥉"];
  // Biggest gainer/loser of the round (by FCFA change).
  const byChange = useMemo(
    () => [...recap.players].sort((a, b) => b.change - a.change),
    [recap.players]
  );
  // Current standings (by balance) with rank + rank movement.
  const byBalance = useMemo(
    () => [...recap.players].sort((a, b) => b.balance - a.balance),
    [recap.players]
  );
  const leader = byChange[0];
  const laggard = byChange[byChange.length - 1];
  const maxAbsChange = Math.max(1, ...byChange.map((p) => Math.abs(p.change)));
  const colorOf = (name: string) =>
    playerColor(Math.max(0, byBalance.findIndex((p) => p.username === name)));

  // The "story" of the round: real trades first (biggest money first), then a
  // couple of dice rolls / skips / failures so the recap shows what happened.
  const highlights = useMemo(() => {
    const moves = (moveFeed ?? []).filter(
      (m) => m.round === recap.round && m.action !== "plan"
    );
    const trades = moves.filter((m) => m.action === "buy" || m.action === "sell");
    const others = moves.filter((m) => m.action !== "buy" && m.action !== "sell");
    const sortedTrades = [...trades].sort(
      (a, b) => Math.abs(b.total ?? 0) - Math.abs(a.total ?? 0)
    );
    return [...sortedTrades.slice(0, 4), ...others.slice(0, 2)];
  }, [moveFeed, recap.round]);

  const highlightLabel = (m: MoveFeedEntry): string => {
    switch (m.action) {
      case "buy":
        return t("move.bought", {
          qty: m.quantity,
          product: m.product,
          price: money(m.unit_price ?? 0),
          cost: money(m.total ?? 0),
        });
      case "sell":
        return t("move.sold", {
          qty: m.quantity,
          product: m.product,
          price: money(m.unit_price ?? 0),
          revenue: money(m.total ?? 0),
        });
      case "roll":
        return t("move.rolled", { dice: m.dice_total, price: money(m.dice_price ?? 0) });
      case "skip":
        return t("move.skipped", { reason: m.reason ?? t("move.noTrade") });
      default:
        return t("move.failed", { reason: m.reason ?? t("move.condition") });
    }
  };
  const highlightIcon = (a: string) =>
    a === "buy" ? "🟢" : a === "sell" ? "🔴" : a === "roll" ? "🎲" : a === "skip" ? "⚪" : "⚠️";

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

      {/* Highlights + standings side by side on wide screens */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Round highlights — the actual trades that made the news */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-4">
        <h3 className="mb-2 font-display text-sm font-bold uppercase tracking-wide">
          {t("recap.highlights")}
        </h3>
        {highlights.length === 0 ? (
          <p className="text-xs italic text-dim">{t("recap.noHighlights")}</p>
        ) : (
          <div className="flex flex-col gap-1.5">
            {highlights.map((m, i) => {
              const c = colorOf(m.player);
              const meta = m.product ? productMeta(m.product) : null;
              return (
                <div
                  key={i}
                  className="flex items-center gap-2 rounded-lg border border-[rgba(100,180,255,0.08)] bg-board/40 px-3 py-1.5 text-[12px]"
                >
                  {meta && (
                    <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md border text-sm ${TONE_CLASSES[meta.tone]}`}>
                      {meta.icon}
                    </span>
                  )}
                  <span className={`shrink-0 font-display text-[10px] font-black uppercase tracking-wide ${c.text}`}>
                    {m.player}
                  </span>
                  <span className="shrink-0">{highlightIcon(m.action)}</span>
                  <span className="truncate text-bright">{highlightLabel(m)}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

        {/* Standings with rank movement */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-4">
        <h3 className="mb-3 font-display text-sm font-bold uppercase tracking-wide">
          {t("recap.positions")}
        </h3>
        <div className="flex flex-col gap-1.5">
          {byBalance.map((p, i) => {
            const c = colorOf(p.username);
            const isHuman = humanPlayers?.includes(p.username) ?? false;
            const rank = i + 1;
            const rankMove = p.prev_rank == null ? null : rank - p.prev_rank;
            const deltaCls = p.change > 0 ? "text-buy" : p.change < 0 ? "text-sell" : "text-dim";
            return (
              <div
                key={p.username}
                className="rounded-lg border border-[rgba(100,180,255,0.08)] bg-board/40 px-3 py-2 text-[13px]"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[11px] ${
                      rank <= 3
                        ? "border-gold/30 bg-gold/15 text-gold"
                        : "border-[rgba(100,180,255,0.15)] bg-board text-dim"
                    }`}
                  >
                    {MEDALS[rank - 1] ?? rank}
                  </span>
                  <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-black ${c.avatar}`}>
                    {p.username.slice(0, 1).toUpperCase()}
                  </span>
                  <span className={`truncate font-semibold ${isHuman ? c.text : "text-bright"}`}>
                    {p.username}
                  </span>
                  {rankMove != null && rankMove !== 0 && (
                    <span className={`shrink-0 rounded px-1 text-[10px] font-black ${
                      rankMove < 0 ? "bg-buy/15 text-buy" : "bg-sell/15 text-sell"
                    }`}>
                      {rankMove < 0 ? `▲ ${Math.abs(rankMove)}` : `▼ ${rankMove}`}
                    </span>
                  )}
                  <span className="ml-auto shrink-0 font-display font-bold text-cyan">{money(p.balance)}</span>
                  <span className={`w-24 shrink-0 text-right font-display font-bold ${deltaCls}`}>
                    {p.change > 0 ? "▲ +" : p.change < 0 ? "▼ −" : ""}
                    {p.change !== 0 ? money(Math.abs(p.change)) : "—"}
                  </span>
                </div>
                <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-board">
                  <div
                    className={`h-full rounded-full ${p.change >= 0 ? "bg-buy/70" : "bg-sell/70"}`}
                    style={{ width: `${(Math.abs(p.change) / maxAbsChange) * 100}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
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
