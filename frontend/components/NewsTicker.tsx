"use client";

import type { NewsItem } from "@/lib/types";

interface NewsTickerProps {
  items: NewsItem[];
}

/**
 * A one-line market news ticker shown above the board during strategy/action
 * phases. Rotates through the round's headlines (price moves, calm markets).
 */
export default function NewsTicker({ items }: NewsTickerProps) {
  if (!items || items.length === 0) return null;
  return (
    <div className="flex items-center gap-2 overflow-hidden rounded-xl border border-[rgba(100,180,255,0.1)] bg-board/50 px-3 py-1.5">
      <span className="shrink-0 font-display text-[10px] font-bold uppercase tracking-widest text-gold">
        📰 Market
      </span>
      <div className="flex min-w-0 items-center gap-4">
        {items.map((n, i) => (
          <span
            key={i}
            className={`shrink-0 text-[11px] ${
              n.tone === "up" ? "text-buy" : n.tone === "down" ? "text-sell" : "text-dim"
            }`}
          >
            {n.tone === "up" ? "📈" : n.tone === "down" ? "📉" : "➖"} {n.text}
          </span>
        ))}
      </div>
    </div>
  );
}
