"use client";

import { useEffect, useState } from "react";
import type { GameState } from "@/lib/types";
import { money, productMeta, TONE_CLASSES } from "@/lib/format";
import Dice from "./Dice";

interface ActionPanelProps {
  game: GameState;
  humanUsername?: string | null;
  busy?: boolean;
  onExecute: (quantity: number) => void;
}

export default function ActionPanel({
  game,
  humanUsername,
  busy,
  onExecute,
}: ActionPanelProps) {
  const isHumanTurn = game.current_player === humanUsername;
  const pending = !!game.can_buy || !!game.can_sell;
  const market = game.markets.find(
    (m) => m.market_index === game.current_market_index
  );
  const maxQty = Math.max(
    1,
    game.can_buy ? (game.max_affordable ?? 1) : (game.seller_qty ?? 1)
  );
  const [qty, setQty] = useState(maxQty);

  const dieTotal = game.dice_total;
  const die1 = dieTotal ? Math.ceil(dieTotal / 2) : null;
  const die2 = dieTotal && die1 != null ? dieTotal - die1 : null;

  // Reset the input whenever a new prompt arrives.
  useEffect(() => {
    setQty(maxQty);
  }, [game.current_player, game.current_market_index, game.can_buy, game.can_sell]); // eslint-disable-line react-hooks/exhaustive-deps

  const meta = market ? productMeta(market.product) : null;

  return (
    <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-5 shadow-card">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <span className="font-display text-[11px] font-bold uppercase tracking-[0.2em] text-gold">
            ⚡ Action Phase
          </span>
          <h3 className="mt-1 font-display text-xl font-bold uppercase">
            {game.current_player ? (
              <>
                {game.current_player}
                {isHumanTurn ? " — your move" : " is trading…"}
              </>
            ) : (
              "Resolving trades…"
            )}
          </h3>
        </div>
        <Dice die1={die1} die2={die2} total={dieTotal} label="Dice" size="sm" />
      </div>

      {/* Turn order strip */}
      {game.turn_order && game.turn_order.length > 0 && (
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <span className="text-[11px] uppercase tracking-widest text-dim">
            Turn order
          </span>
          {game.turn_order.map((t, i) => (
            <span
              key={t.username}
              className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs ${
                t.username === game.current_player
                  ? "border-gold/50 bg-gold/10 text-gold"
                  : "border-[rgba(100,180,255,0.12)] bg-board text-dim"
              }`}
            >
              <span className="font-display font-bold">{i + 1}</span>
              {t.username}
              <span className="opacity-70">🎲{t.dice_total}</span>
            </span>
          ))}
        </div>
      )}

      {isHumanTurn && pending ? (
        <div className="space-y-4">
          <div className="flex flex-col gap-4 rounded-xl border border-[rgba(100,180,255,0.08)] bg-board/60 p-4 sm:flex-row sm:items-center">
            {meta && (
              <span className={`flex h-14 w-14 items-center justify-center rounded-xl border text-2xl ${TONE_CLASSES[meta.tone]}`}>
                {meta.icon}
              </span>
            )}
            <div className="flex-1">
              <p className="text-sm text-dim">
                {game.can_buy ? (
                  <>
                    Buy <span className="font-bold text-buy">{market?.product}</span> at{" "}
                    <span className="font-bold text-cyan">{money(game.dice_price ?? market?.market_fixed_price ?? 0)}</span>
                  </>
                ) : (
                  <>
                    Sell <span className="font-bold text-sell">{market?.product}</span> at{" "}
                    <span className="font-bold text-cyan">{money(game.dice_price ?? 0)}</span>
                  </>
                )}{" "}
                — max{" "}
                <span className="font-bold text-bright">{maxQty} units</span>
              </p>
              {game.can_buy && (
                <p className="text-xs text-dim">
                  Market fixed price: {money(market?.market_fixed_price ?? 0)} · tax{" "}
                  {((market?.tax_rate ?? 0) * 100).toFixed(0)}%
                </p>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setQty((q) => Math.max(1, q - 1))}
                className="h-10 w-10 rounded-lg border border-[rgba(100,180,255,0.2)] bg-board text-lg text-bright hover:border-gold/40"
              >
                −
              </button>
              <input
                type="number"
                min={1}
                max={maxQty}
                value={qty}
                onChange={(e) =>
                  setQty(Math.min(maxQty, Math.max(1, Number(e.target.value) || 1)))
                }
                className="h-10 w-20 rounded-lg border border-[rgba(100,180,255,0.2)] bg-board text-center font-display text-lg font-bold text-gold outline-none focus:border-gold/50"
              />
              <button
                type="button"
                onClick={() => setQty((q) => Math.min(maxQty, q + 1))}
                className="h-10 w-10 rounded-lg border border-[rgba(100,180,255,0.2)] bg-board text-lg text-bright hover:border-gold/40"
              >
                +
              </button>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => onExecute(qty)}
              disabled={busy}
              className={`rounded-xl px-8 py-3 font-display text-sm font-bold uppercase tracking-widest text-deep shadow-card transition-all hover:brightness-110 active:scale-95 disabled:opacity-50 ${
                game.can_buy ? "bg-buy" : "bg-sell"
              }`}
            >
              {busy ? "Trading…" : game.can_buy ? "Confirm Buy" : "Confirm Sell"}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-4 rounded-xl border border-[rgba(100,180,255,0.08)] bg-board/60 p-5">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-gold/30 border-t-gold" />
          <p className="text-sm text-dim">
            {isHumanTurn
              ? "Your strategy is set — waiting for the other players to finish their trades."
              : `${game.current_player ?? "The market"} is trading… sit tight, this resolves automatically.`}
          </p>
        </div>
      )}
    </div>
  );
}
