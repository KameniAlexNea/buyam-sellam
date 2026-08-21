"use client";

import type { GameState, MoveFeedEntry } from "@/lib/types";
import { money, playerColor, productMeta, TONE_CLASSES } from "@/lib/format";
import Dice from "./Dice";

interface BotTurnPanelProps {
  game: GameState;
}

/** Render one move-feed entry as a compact "what happened" row. */
function MoveRow({ move, index }: { move: MoveFeedEntry; index: number }) {
  const meta = move.product ? productMeta(move.product) : null;
  const color = playerColor(Math.max(0, index % 4));

  const actionIcon =
    move.action === "buy"
      ? "🟢"
      : move.action === "sell"
      ? "🔴"
      : move.action === "roll"
      ? "🎲"
      : move.action === "skip"
      ? "⚪"
      : "⚠️";

  let label = "";
  if (move.action === "roll") {
    label = `rolled ${move.dice_total} → dice price ${money(move.dice_price ?? 0)}`;
  } else if (move.action === "buy") {
    label = `bought ${move.quantity}× ${move.product} @ ${money(move.unit_price ?? 0)} · −${money(move.total ?? 0)}`;
  } else if (move.action === "sell") {
    label = `sold ${move.quantity}× ${move.product} @ ${money(move.unit_price ?? 0)} · +${money(move.total ?? 0)}`;
  } else if (move.action === "skip") {
    label = `skipped · ${move.reason ?? "no trade"}`;
  } else {
    label = `trade failed · ${move.reason ?? "condition not met"}`;
  }

  return (
    <div className="flex items-center gap-2 rounded-lg border border-[rgba(100,180,255,0.08)] bg-board/40 px-3 py-1.5 text-xs">
      {meta && (
        <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md border text-sm ${TONE_CLASSES[meta.tone]}`}>
          {meta.icon}
        </span>
      )}
      <span className={`shrink-0 font-display text-[10px] font-black uppercase tracking-wide ${color.text}`}>
        {move.player}
      </span>
      <span className="shrink-0">{actionIcon}</span>
      <span className="truncate text-bright">{label}</span>
      {move.balance != null && (
        <span className="ml-auto shrink-0 font-mono text-[10px] text-dim">
          {money(move.balance)}
        </span>
      )}
    </div>
  );
}

/**
 * Replays what the bots are doing during the action phase: the current dice
 * roll plus a feed of the latest moves so trading stays visible instead of
 * resolving invisibly.
 */
export default function BotTurnPanel({ game }: BotTurnPanelProps) {
  const feed = game.move_feed ?? [];
  const recent = feed.slice(-6).reverse();

  const dieTotal = game.dice_total;
  const die1 = dieTotal ? Math.ceil(dieTotal / 2) : null;
  const die2 = dieTotal && die1 != null ? dieTotal - die1 : null;
  const actor = game.current_player ?? "The market";

  return (
    <div className="flex w-full flex-col items-center gap-3">
      <div className="flex items-center gap-4">
        <Dice die1={die1} die2={die2} total={dieTotal} label="Dice" size="lg" rolling />
        <div className="text-left">
          <span className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            🤖 Bot turn
          </span>
          <h3 className="font-display text-lg font-bold uppercase tracking-wide">
            {actor} is trading…
          </h3>
        </div>
      </div>

      <div className="flex w-full max-w-md flex-col gap-1.5">
        {recent.length === 0 ? (
          <div className="flex items-center gap-3 rounded-2xl border border-[rgba(100,180,255,0.1)] bg-board/50 px-6 py-4">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-gold/30 border-t-gold" />
            <p className="text-sm text-dim">Resolving trades…</p>
          </div>
        ) : (
          <>
            {recent.map((m, i) => (
              <MoveRow key={`${m.round}-${m.player}-${i}`} move={m} index={i} />
            ))}
            <div className="mt-1 flex items-center justify-center gap-2 text-[10px] uppercase tracking-widest text-dim/70">
              <span className="h-3 w-3 animate-pulse rounded-full bg-gold/60" />
              automatic — no action needed
            </div>
          </>
        )}
      </div>
    </div>
  );
}
