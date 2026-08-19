"use client";

import type { MarketAction, MarketInfo } from "@/lib/types";
import { moneyShort, productMeta, TONE_CLASSES } from "@/lib/format";
import PlayerToken from "./PlayerToken";
import Sparkline from "./Sparkline";

interface MarketTileProps {
  market?: MarketInfo;
  orientation?: "horizontal" | "vertical";
  badge?: MarketAction | null;
  active?: boolean;
  token?: { username: string; color: number } | null;
  onClick?: () => void;
  placeholder?: boolean;
  dimmed?: boolean;
}

const BADGE_META: Record<
  MarketAction,
  { label: string; cls: string }
> = {
  buy: { label: "BUY", cls: "bg-buy/90 text-deep" },
  sell: { label: "SELL", cls: "bg-sell/90 text-white" },
  skip: { label: "—", cls: "bg-dim/30 text-dim" },
};

/** Solid product-tone stripe colors for the tile edge. */
const STRIPE: Record<string, string> = {
  amber: "bg-amber-400",
  mint: "bg-emerald-400",
  gold: "bg-yellow-400",
  earth: "bg-orange-400",
  blue: "bg-blue-400",
  slate: "bg-slate-400",
};

/**
 * A single market space on the board edge. During the strategy phase it can be
 * tapped to cycle Buy → Sell → Skip. During the action phase it highlights the
 * active market and shows the current player's token.
 */
export default function MarketTile({
  market,
  orientation = "horizontal",
  badge,
  active = false,
  token,
  onClick,
  placeholder = false,
  dimmed = false,
}: MarketTileProps) {
  if (placeholder || !market) {
    return (
      <div
        className={`flex flex-1 items-center justify-center rounded-xl border border-dashed border-[rgba(100,180,255,0.12)] bg-board/30 ${
          orientation === "horizontal" ? "h-full min-h-[4.5rem]" : "w-full min-w-[4.5rem] min-h-full"
        }`}
      >
        <span className="text-lg text-[rgba(100,180,255,0.18)]">◆</span>
      </div>
    );
  }

  const meta = productMeta(market.product);
  const horizontal = orientation === "horizontal";

  // Trend vs the previous round, derived from the market's price history.
  const hist = market.price_history ?? [];
  const last = hist.length > 0 ? hist[hist.length - 1] : market.market_fixed_price;
  const prev = hist.length > 1 ? hist[hist.length - 2] : last;
  const pct = prev ? ((last - prev) / prev) * 100 : 0;
  const trendUp = pct > 0.1;
  const trendDown = pct < -0.1;
  const trendStroke = trendUp ? "#00e68a" : trendDown ? "#ff4d6a" : "#7a89aa";
  const trendLabel = trendUp
    ? `▲ ${Math.abs(pct).toFixed(1)}%`
    : trendDown
    ? `▼ ${Math.abs(pct).toFixed(1)}%`
    : "—";

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      className={`group relative flex-1 rounded-xl border text-left transition-all duration-200 ${
        onClick ? "cursor-pointer hover:scale-[1.03]" : "cursor-default"
      } ${
        active
          ? "border-gold/60 shadow-glow-gold ring-1 ring-gold/40"
          : "border-[rgba(100,180,255,0.14)] bg-card hover:border-[rgba(100,180,255,0.35)]"
      } ${dimmed ? "opacity-45" : ""}`}
      style={
        horizontal
          ? { minHeight: "5.5rem" }
          : { minWidth: "4.75rem", minHeight: "7rem" }
      }
    >
      <div
        className={`absolute inset-y-0 left-0 w-1.5 rounded-l-xl ${
          STRIPE[meta.tone] ?? "bg-slate-400"
        }`}
      />
      <div className={`flex h-full w-full items-center gap-2 px-2.5 ${horizontal ? "flex-row" : "flex-col justify-center text-center"}`}>
        <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border text-lg ${TONE_CLASSES[meta.tone]}`}>
          {meta.icon}
        </span>
        <div className={`min-w-0 ${horizontal ? "flex-1" : ""}`}>
          <p className="truncate text-[11px] font-bold uppercase tracking-wide">
            {market.product}
          </p>
          <p className="text-[10px] text-dim">{market.name}</p>
          <p className={`font-display text-sm font-bold ${active ? "text-gold" : "text-cyan"}`}>
            {moneyShort(market.market_fixed_price)}
          </p>
          <div className="mt-0.5 flex items-center gap-1.5">
            <Sparkline
              data={hist}
              width={horizontal ? 56 : 44}
              height={16}
              stroke={trendStroke}
            />
            <span
              className={`text-[9px] font-bold ${
                trendUp ? "text-buy" : trendDown ? "text-sell" : "text-dim"
              }`}
            >
              {trendLabel}
            </span>
          </div>
        </div>
        {token && (
          <PlayerToken
            username={token.username}
            color={token.color}
            compact
            showBalance={false}
          />
        )}
      </div>

      {badge && (
        <span
          className={`absolute right-1.5 top-1.5 rounded-md px-1.5 py-0.5 font-display text-[9px] font-black tracking-wider ${
            BADGE_META[badge].cls
          }`}
        >
          {BADGE_META[badge].label}
        </span>
      )}
    </button>
  );
}
