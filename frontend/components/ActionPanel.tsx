"use client";

import { useEffect, useState } from "react";
import type { GameState } from "@/lib/types";
import { money, productMeta, TONE_CLASSES } from "@/lib/format";
import Dice from "./Dice";

interface ActionPanelProps {
  game: GameState;
  isHumanTurn: boolean;
  busy?: boolean;
  onExecute: (quantity: number) => void;
}

export default function ActionPanel({
  game,
  isHumanTurn,
  busy,
  onExecute,
}: ActionPanelProps) {
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
  const actor = game.current_player ?? "The market";

  return (
    <div className="flex w-full flex-col items-center gap-3">
      <div className="flex items-center gap-4">
        <Dice die1={die1} die2={die2} total={dieTotal} label="Dice" size="lg" rolling />
        <div className="text-left">
          <span className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            ⚡ Action
          </span>
          <h3 className="font-display text-lg font-bold uppercase tracking-wide">
            {actor}
            {isHumanTurn ? " — your move!" : " is trading…"}
          </h3>
        </div>
      </div>

      {isHumanTurn && pending ? (
        <div className="flex w-full max-w-md flex-col items-center gap-3 rounded-2xl border border-[rgba(100,180,255,0.12)] bg-board/60 p-4">
          <div className="flex items-center gap-3">
            {meta && (
              <span className={`flex h-12 w-12 items-center justify-center rounded-xl border text-2xl ${TONE_CLASSES[meta.tone]}`}>
                {meta.icon}
              </span>
            )}
            <p className="text-sm">
              {game.can_buy ? (
                <>
                  <span className="font-bold text-buy">Buy {market?.product}</span> at{" "}
                  <span className="font-bold text-cyan">{money(game.dice_price ?? market?.market_fixed_price ?? 0)}</span>
                </>
              ) : (
                <>
                  <span className="font-bold text-sell">Sell {market?.product}</span> at{" "}
                  <span className="font-bold text-cyan">{money(game.dice_price ?? 0)}</span>
                </>
              )}{" "}
              · max <span className="font-bold">{maxQty}</span>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setQty((q) => Math.max(1, q - 1))}
              className="h-10 w-10 rounded-lg border border-[rgba(100,180,255,0.2)] bg-card text-lg text-bright hover:border-gold/40"
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
              className="h-10 w-20 rounded-lg border border-[rgba(100,180,255,0.2)] bg-card text-center font-display text-lg font-bold text-gold outline-none focus:border-gold/50"
            />
            <button
              type="button"
              onClick={() => setQty((q) => Math.min(maxQty, q + 1))}
              className="h-10 w-10 rounded-lg border border-[rgba(100,180,255,0.2)] bg-card text-lg text-bright hover:border-gold/40"
            >
              +
            </button>
            <button
              type="button"
              onClick={() => onExecute(qty)}
              disabled={busy}
              className={`ml-2 rounded-xl px-6 py-2.5 font-display text-sm font-bold uppercase tracking-widest text-deep transition-all hover:brightness-110 active:scale-95 disabled:opacity-50 ${
                game.can_buy ? "bg-buy" : "bg-sell"
              }`}
            >
              {busy ? "…" : game.can_buy ? "Buy" : "Sell"}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-3 rounded-2xl border border-[rgba(100,180,255,0.1)] bg-board/50 px-6 py-4">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-gold/30 border-t-gold" />
          <p className="text-sm text-dim">
            {isHumanTurn
              ? "Your strategy is locked in — waiting for the others to trade."
              : `${actor} is trading… this resolves automatically.`}
          </p>
        </div>
      )}
    </div>
  );
}
