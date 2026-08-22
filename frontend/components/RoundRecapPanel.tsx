"use client";

import { useMemo, useState } from "react";
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
  // Carousel: best/worst (0) → round highlights (1) → standings (2).
  const [slide, setSlide] = useState(0);
  // Collapsible market-news notification.
  const [newsOpen, setNewsOpen] = useState(false);
  const slideTitles = [
    t("recap.bestWorst"),
    t("recap.highlights"),
    t("recap.positions"),
  ];
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
  // few skips. Dice rolls and failed attempts are noise — not shown.
  const highlights = useMemo(() => {
    const moves = (moveFeed ?? []).filter(
      (m) =>
        m.round === recap.round &&
        (m.action === "buy" || m.action === "sell" || m.action === "skip")
    );
    const trades = moves.filter((m) => m.action === "buy" || m.action === "sell");
    const skips = moves.filter((m) => m.action === "skip");
    const sortedTrades = [...trades].sort(
      (a, b) => Math.abs(b.total ?? 0) - Math.abs(a.total ?? 0)
    );
    return [...sortedTrades.slice(0, 6), ...skips.slice(0, 3)];
  }, [moveFeed, recap.round]);

  const highlightLabel = (m: MoveFeedEntry): string => {
    switch (m.action) {
      case "buy":
        return t("move.bought", {
          qty: m.quantity ?? 0,
          product: m.product ?? "",
          price: money(m.unit_price ?? 0),
          cost: money(m.total ?? 0),
        });
      case "sell":
        return t("move.sold", {
          qty: m.quantity ?? 0,
          product: m.product ?? "",
          price: money(m.unit_price ?? 0),
          revenue: money(m.total ?? 0),
        });
      default:
        return t("move.skipped", { reason: m.reason ?? t("move.noTrade") });
    }
  };
  const highlightIcon = (a: string) =>
    a === "buy" ? "🟢" : a === "sell" ? "🔴" : "⚪";

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

      {/* Advance — pinned at the top so you never have to scroll to continue */}
      <div className="mb-4">
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

      {/* Carousel: round highlights ↔ standings */}
      <div className="mb-4 rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-4">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h3 className="font-display text-sm font-bold uppercase tracking-wide">
            {slideTitles[slide]}
          </h3>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSlide(Math.max(0, slide - 1))}
              disabled={slide === 0}
              aria-label={slideTitles[Math.max(0, slide - 1)]}
              className={`flex h-8 w-8 items-center justify-center rounded-lg border text-sm transition-all ${
                slide === 0
                  ? "cursor-default border-gold/30 bg-gold/15 text-gold"
                  : "border-[rgba(100,180,255,0.2)] bg-board/50 text-dim hover:text-gold"
              }`}
            >
              ◀
            </button>
            <div className="flex items-center gap-1.5">
              {[0, 1, 2].map((i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setSlide(i)}
                  aria-label={slideTitles[i]}
                  className={`h-2 w-2 rounded-full transition-all ${
                    slide === i ? "bg-gold" : "bg-dim/40 hover:bg-dim/70"
                  }`}
                />
              ))}
            </div>
            <button
              type="button"
              onClick={() => setSlide(Math.min(2, slide + 1))}
              disabled={slide === 2}
              aria-label={slideTitles[Math.min(2, slide + 1)]}
              className={`flex h-8 w-8 items-center justify-center rounded-lg border text-sm transition-all ${
                slide === 2
                  ? "cursor-default border-gold/30 bg-gold/15 text-gold"
                  : "border-[rgba(100,180,255,0.2)] bg-board/50 text-dim hover:text-gold"
              }`}
            >
              ▶
            </button>
          </div>
        </div>

        {slide === 0 ? (
          /* Best & worst of the round */
          <div className="grid grid-cols-2 gap-3">
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
        ) : slide === 1 ? (
          highlights.length === 0 ? (
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
          )
        ) : (
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
        )}
      </div>

      {/* Market news — a notification you click to expand */}
      {recap.news.length > 0 && (
        <div className="mb-4 rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card">
          <button
            type="button"
            onClick={() => setNewsOpen((v) => !v)}
            aria-expanded={newsOpen}
            className="flex w-full items-center gap-2 px-4 py-3 text-left transition-colors hover:bg-board/40"
          >
            <span className="font-display text-xs font-bold uppercase tracking-widest text-dim">
              {t("recap.marketNews")} ({recap.news.length})
            </span>
            <span
              className={`ml-auto text-xs text-dim transition-transform ${newsOpen ? "rotate-180" : ""}`}
            >
              ▾
            </span>
          </button>
          {newsOpen && (
            <div className="animate-fade-in-up flex flex-col gap-1.5 border-t border-[rgba(100,180,255,0.08)] px-4 py-3">
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
          )}
        </div>
      )}
    </div>
  );
}
