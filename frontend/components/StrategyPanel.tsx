"use client";

import { useMemo } from "react";
import type { MarketAction, MarketInfo, PlayerInfo } from "@/lib/types";
import { money, productMeta, TONE_CLASSES } from "@/lib/format";

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

  return (
    <div className="flex w-full flex-col items-center gap-4">
      <div className="text-center">
        <span className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
          🧠 Strategy
        </span>
        <h3 className="mt-1 font-display text-lg font-bold uppercase tracking-wide">
          {planner} — plan your moves
        </h3>
        <p className="mt-0.5 text-[11px] text-dim">
          Tap a market on the board, or pick below. {plannerPlayer && (
            <>
              · cash <span className="text-bright">{money(plannerPlayer.balance)}</span>
            </>
          )}
        </p>
        {plannerPlayer && plannerPlayer.inventory.length > 0 && (
          <p className="mt-1 text-[11px] text-dim">
            You own:{" "}
            {plannerPlayer.inventory.map((it) => (
              <span key={it.product.name} className="mx-0.5">
                {productMeta(it.product.name).icon}
                {it.quantity}
              </span>
            ))}
          </p>
        )}
      </div>

      <div className="grid w-full max-w-md grid-cols-1 gap-1.5">
        {markets.map((m) => {
          const meta = productMeta(m.product);
          const canSell = (ownedProducts[m.product] ?? 0) > 0;
          return (
            <div
              key={m.market_index}
              className="flex items-center justify-between gap-2 rounded-xl border border-[rgba(100,180,255,0.1)] bg-board/50 px-2.5 py-1.5"
            >
              <div className="flex min-w-0 items-center gap-2">
                <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border text-base ${TONE_CLASSES[meta.tone]}`}>
                  {meta.icon}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-xs font-semibold">{m.product}</p>
                  <p className="text-[10px] text-cyan">{money(m.market_fixed_price)}</p>
                </div>
              </div>
              <div className="flex gap-1">
                {ACTIONS.map((a) => {
                  const selected = (choices[m.market_index] ?? "skip") === a.value;
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
                      className={`rounded-md border px-2 py-1 text-[11px] font-bold uppercase tracking-wide transition-all ${
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

      <button
        type="button"
        onClick={onConfirm}
        disabled={busy}
        className="rounded-xl bg-gold px-8 py-2.5 font-display text-sm font-bold uppercase tracking-widest text-deep shadow-glow-gold transition-all hover:brightness-110 active:scale-95 disabled:opacity-50"
      >
        {busy ? "Resolving…" : chosen > 0 ? `Submit · ${chosen} move${chosen > 1 ? "s" : ""}` : "Submit · all skip"}
      </button>
    </div>
  );
}
