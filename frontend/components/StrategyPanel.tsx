"use client";

import { useMemo, useState } from "react";
import type { MarketAction, MarketInfo, PlayerInfo } from "@/lib/types";
import { money, productMeta, TONE_CLASSES } from "@/lib/format";
import type { StrategyChoice } from "@/lib/useGameState";

interface StrategyPanelProps {
  markets: MarketInfo[];
  humanPlayer?: PlayerInfo | null;
  busy?: boolean;
  onSubmit: (choices: StrategyChoice[]) => void;
}

const ACTIONS: { value: MarketAction; label: string; icon: string; active: string }[] = [
  { value: "buy", label: "Buy", icon: "⬇", active: "bg-buy/20 border-buy text-buy" },
  { value: "sell", label: "Sell", icon: "⬆", active: "bg-sell/20 border-sell text-sell" },
  { value: "skip", label: "Skip", icon: "—", active: "bg-dim/20 border-dim text-dim" },
];

export default function StrategyPanel({
  markets,
  humanPlayer,
  busy,
  onSubmit,
}: StrategyPanelProps) {
  const [choices, setChoices] = useState<Record<number, MarketAction>>({});

  const ownedProducts = useMemo(() => {
    const map: Record<string, number> = {};
    humanPlayer?.inventory.forEach((it) => {
      map[it.product.name] = it.quantity;
    });
    return map;
  }, [humanPlayer]);

  const canSell = (product: string) => (ownedProducts[product] ?? 0) > 0;

  const setAction = (index: number, action: MarketAction) => {
    setChoices((prev) => ({ ...prev, [index]: action }));
  };

  const handleSubmit = () => {
    const strategy = markets.map((m) => ({
      market_index: m.market_index,
      action: choices[m.market_index] ?? "skip",
    }));
    onSubmit(strategy);
  };

  return (
    <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-5 shadow-card">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <span className="font-display text-[11px] font-bold uppercase tracking-[0.2em] text-gold">
            🧠 Strategy Phase
          </span>
          <h3 className="mt-1 font-display text-xl font-bold uppercase">
            Plan your trades
          </h3>
        </div>
        {humanPlayer && (
          <span className="text-xs text-dim">
            Balance: <span className="font-semibold text-bright">{money(humanPlayer.balance)}</span>
          </span>
        )}
      </div>

      <div className="space-y-3">
        {markets.map((m) => {
          const meta = productMeta(m.product);
          const owned = ownedProducts[m.product] ?? 0;
          const sellDisabled = !canSell(m.product);
          return (
            <div
              key={m.market_index}
              className="flex flex-col gap-3 rounded-xl border border-[rgba(100,180,255,0.08)] bg-board/60 p-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex items-center gap-3">
                <span className={`flex h-10 w-10 items-center justify-center rounded-lg border text-lg ${TONE_CLASSES[meta.tone]}`}>
                  {meta.icon}
                </span>
                <div>
                  <p className="font-semibold text-bright">
                    {m.name}{" "}
                    <span className="font-normal text-dim">
                      ({m.product})
                    </span>
                  </p>
                  <p className="text-xs text-dim">
                    <span className="text-cyan">{money(m.market_fixed_price)}</span> · tax{" "}
                    {(m.tax_rate * 100).toFixed(0)}% · supply {m.market_supply}u
                    {owned > 0 && (
                      <span className="ml-2 text-buy">
                        you own {owned}u
                      </span>
                    )}
                  </p>
                </div>
              </div>

              <div className="flex gap-1.5">
                {ACTIONS.map((a) => {
                  const selected = (choices[m.market_index] ?? "skip") === a.value;
                  const disabled = a.value === "sell" && sellDisabled;
                  return (
                    <button
                      key={a.value}
                      type="button"
                      disabled={disabled}
                      onClick={() => setAction(m.market_index, a.value)}
                      title={
                        disabled
                          ? `You don't have ${m.product} in your inventory`
                          : undefined
                      }
                      className={`rounded-lg border px-3 py-1.5 text-xs font-bold uppercase tracking-wider transition-all ${
                        selected
                          ? a.active
                          : "border-[rgba(100,180,255,0.12)] bg-card text-dim hover:border-[rgba(100,180,255,0.35)] hover:text-bright"
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

      <div className="mt-5 flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
        <p className="max-w-md text-xs text-dim">
          Your strategy is locked in when you submit. Bots will finalize theirs
          and the round will resolve automatically.
        </p>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={busy}
          className="rounded-xl bg-gold px-6 py-2.5 font-display text-sm font-bold uppercase tracking-widest text-deep shadow-glow-gold transition-all hover:brightness-110 active:scale-95 disabled:opacity-50"
        >
          {busy ? "Resolving…" : "Submit Strategy"}
        </button>
      </div>
    </div>
  );
}
