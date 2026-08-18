"use client";

import type { MarketInfo } from "@/lib/types";
import { money, productMeta, TONE_CLASSES } from "@/lib/format";

interface MarketGridProps {
  markets: MarketInfo[];
  currentMarketIndex?: number | null;
}

export default function MarketGrid({
  markets,
  currentMarketIndex,
}: MarketGridProps) {
  if (markets.length === 0) {
    return (
      <p className="py-8 text-center text-dim">
        No markets active this round yet.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {markets.map((m) => {
        const meta = productMeta(m.product);
        const isCurrent = m.market_index === currentMarketIndex;
        return (
          <div
            key={m.market_index}
            className={`relative rounded-2xl border bg-card p-4 shadow-card transition-all duration-200 hover:-translate-y-0.5 ${
              isCurrent
                ? "border-gold/50 shadow-glow-gold ring-1 ring-gold/30"
                : "border-[rgba(100,180,255,0.12)] hover:border-[rgba(100,180,255,0.3)]"
            }`}
          >
            {isCurrent && (
              <span className="absolute -top-2.5 right-3 rounded-full bg-gold px-2 py-0.5 font-display text-[10px] font-bold uppercase tracking-wider text-deep shadow-glow-gold">
                Active
              </span>
            )}

            <div className="flex items-start justify-between gap-2">
              <div>
                <span
                  className={`inline-flex items-center gap-1.5 rounded-lg border px-2 py-0.5 text-xs font-semibold ${TONE_CLASSES[meta.tone]}`}
                >
                  <span>{meta.icon}</span>
                  {m.product}
                </span>
                <h3 className="mt-2 font-display text-sm font-bold uppercase tracking-wide text-bright">
                  {m.name}
                </h3>
              </div>
              <span className="rounded-lg bg-board px-2 py-1 font-mono text-xs text-dim">
                M{m.market_index}
              </span>
            </div>

            <div className="mt-3 flex items-end justify-between">
              <div>
                <p className="text-[11px] uppercase tracking-widest text-dim">
                  Market price
                </p>
                <p className="font-display text-xl font-bold text-cyan">
                  {money(m.market_fixed_price)}
                </p>
              </div>
              <div className="text-right text-xs text-dim">
                <p>Supply: <span className="text-bright">{m.market_supply} u</span></p>
                <p>Tax: <span className="text-amberc">{(m.tax_rate * 100).toFixed(0)}%</span></p>
                <p>Entry: <span className="text-sell">{money(m.sell_entry_fee)}</span></p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
