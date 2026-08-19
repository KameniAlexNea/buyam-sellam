"use client";

import { useMemo } from "react";
import type { MarketAction, MarketInfo, PlayerInfo } from "@/lib/types";
import { money, moneyShort, productMeta, TONE_CLASSES } from "@/lib/format";
import {
  probAtLeast,
  probAtMost,
  probLabel,
  rollForBuy,
  rollForSell,
} from "@/lib/dice";

interface StrategyPanelProps {
  markets: MarketInfo[];
  planner: string;
  plannerPlayer?: PlayerInfo | null;
  choices: Record<number, MarketAction>;
  onChoice: (index: number, action: MarketAction) => void;
  busy?: boolean;
  onConfirm: () => void;
}

const ACTIONS: { value: MarketAction; label: string; icon: string; active: string }[] = [
  { value: "buy", label: "Buy", icon: "⬇", active: "bg-buy/25 border-buy text-buy" },
  { value: "sell", label: "Sell", icon: "⬆", active: "bg-sell/25 border-sell text-sell" },
  { value: "skip", label: "Skip", icon: "—", active: "bg-dim/25 border-dim text-dim" },
];

/** Tiny likelihood dot: green = likely, amber = risky, red = unlikely. */
function chanceDot(p: number) {
  const cls = p >= 0.5 ? "bg-buy" : p >= 0.15 ? "bg-amberc" : "bg-sell";
  return <span className={`inline-block h-1.5 w-1.5 rounded-full ${cls}`} />;
}

export default function StrategyPanel({
  markets,
  planner,
  plannerPlayer,
  choices,
  onChoice,
  busy,
  onConfirm,
}: StrategyPanelProps) {
  const ownedProducts = useMemo(() => {
    const map: Record<string, number> = {};
    plannerPlayer?.inventory.forEach((it) => {
      map[it.product.name] = it.quantity;
    });
    return map;
  }, [plannerPlayer]);

  const chosen = markets.filter((m) => (choices[m.market_index] ?? "skip") !== "skip").length;
  const planSellFees = markets
    .filter((m) => (choices[m.market_index] ?? "skip") === "sell")
    .reduce((sum, m) => sum + m.sell_entry_fee, 0);

  return (
    <div className="flex w-full flex-col items-center gap-3">
      {/* Header */}
      <div className="text-center">
        <span className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
          🧠 Strategy Phase
        </span>
        <h3 className="mt-1 font-display text-lg font-bold uppercase tracking-wide">
          {planner} — plan your trades
        </h3>
        <p className="mt-0.5 text-[11px] text-dim">
          Your dice roll decides each trade. {plannerPlayer && (
            <>cash <span className="text-bright">{money(plannerPlayer.balance)}</span></>
          )}
        </p>
        <p className="mx-auto mt-1.5 inline-flex items-center gap-1.5 rounded-lg border border-[rgba(100,180,255,0.15)] bg-board/50 px-2.5 py-1 text-[10px] text-dim">
          🎲 Roll 2–12 → price 200–1,200 FCFA ·{" "}
          <span className="text-buy">low = buy</span> ·{" "}
          <span className="text-sell">high = sell</span>
        </p>
        {plannerPlayer && plannerPlayer.inventory.length > 0 && (
          <p className="mt-1 text-[11px] text-dim">
            Inventory:{" "}
            {plannerPlayer.inventory.map((it) => (
              <span key={it.product.name} className="mx-0.5">
                {productMeta(it.product.name).icon}
                {it.quantity}
              </span>
            ))}
          </p>
        )}
      </div>

      {/* Market decision cards */}
      <div className="grid w-full max-w-lg grid-cols-1 gap-1.5">
        {markets.map((m) => {
          const meta = productMeta(m.product);
          const owned = ownedProducts[m.product] ?? 0;
          const canSell = owned > 0;
          const sel = choices[m.market_index] ?? "skip";
          const buyRoll = rollForBuy(m.market_fixed_price);
          const sellRoll = rollForSell(m.market_fixed_price);
          const buyProb = probAtLeast(buyRoll);
          const sellProb = probAtMost(sellRoll);
          return (
            <div
              key={m.market_index}
              className={`rounded-xl border p-2.5 transition-colors ${
                sel !== "skip"
                  ? sel === "buy"
                    ? "border-buy/40 bg-buy/5"
                    : "border-sell/40 bg-sell/5"
                  : "border-[rgba(100,180,255,0.1)] bg-board/50"
              }`}
            >
              {/* Identity + facts */}
              <div className="flex items-center justify-between gap-2">
                <div className="flex min-w-0 items-center gap-2">
                  <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border text-lg ${TONE_CLASSES[meta.tone]}`}>
                    {meta.icon}
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-xs font-semibold">{m.product}</p>
                    <p className="text-[10px] text-dim">{m.name}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-display text-base font-bold ${sel === "buy" ? "text-buy" : sel === "sell" ? "text-sell" : "text-cyan"}`}>
                    {moneyShort(m.market_fixed_price)}
                  </p>
                  <p className="text-[10px] text-dim">
                    supply {m.market_supply}u · tax {(m.tax_rate * 100).toFixed(0)}% · fee {moneyShort(m.sell_entry_fee)}
                  </p>
                </div>
              </div>

              {/* Dice window */}
              <div className="mt-1.5 flex items-center justify-between gap-2 text-[10px]">
                <p className="flex items-center gap-1.5">
                  <span className={sel === "buy" ? "text-buy" : "text-buy/70"}>
                    {chanceDot(buyProb)} Buy ≥ {buyRoll} ({probLabel(buyProb)})
                  </span>
                  <span className="text-dim">·</span>
                  <span className={sel === "sell" ? "text-sell" : "text-sell/70"}>
                    {chanceDot(sellProb)} Sell ≤ {sellRoll} ({probLabel(sellProb)})
                  </span>
                </p>
                <span className="text-dim">
                  you own <b className={canSell ? "text-bright" : "text-dim"}>{owned}</b>
                </span>
              </div>

              {/* Actions */}
              <div className="mt-1.5 flex justify-end gap-1">
                {ACTIONS.map((a) => {
                  const selected = sel === a.value;
                  const disabled = a.value === "sell" && !canSell;
                  return (
                    <button
                      key={a.value}
                      type="button"
                      disabled={disabled}
                      onClick={() => onChoice(m.market_index, a.value)}
                      title={
                        disabled
                          ? `${planner} doesn't have ${m.product} in inventory`
                          : undefined
                      }
                      className={`rounded-md border px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide transition-all ${
                        selected
                          ? a.active
                          : "border-[rgba(100,180,255,0.12)] bg-card text-dim hover:text-bright"
                      } ${disabled ? "cursor-not-allowed opacity-30" : ""}`}
                    >
                      {a.icon} {a.label}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Plan summary */}
      {chosen > 0 && (
        <div className="flex w-full max-w-lg flex-wrap items-center justify-between gap-2 rounded-xl border border-[rgba(100,180,255,0.1)] bg-board/40 px-3 py-2 text-[11px]">
          <span className="text-dim">Your plan:</span>
          <span className="flex flex-wrap gap-x-2.5">
            {markets.map((m) => {
              const a = choices[m.market_index] ?? "skip";
              if (a === "skip") return null;
              return (
                <span key={m.market_index} className={a === "buy" ? "text-buy" : "text-sell"}>
                  {productMeta(m.product).icon} {a}
                </span>
              );
            })}
          </span>
          {planSellFees > 0 && (
            <span className="text-dim">est. fees {moneyShort(planSellFees)}</span>
          )}
        </div>
      )}

      {/* Confirm */}
      <button
        type="button"
        onClick={onConfirm}
        disabled={busy}
        className="rounded-xl bg-gold px-8 py-2.5 font-display text-sm font-bold uppercase tracking-widest text-deep shadow-glow-gold transition-all hover:brightness-110 active:scale-95 disabled:opacity-50"
      >
        {busy
          ? "Resolving…"
          : chosen > 0
          ? `Confirm ${chosen} move${chosen > 1 ? "s" : ""}`
          : "Confirm · all skip"}
      </button>
    </div>
  );
}
