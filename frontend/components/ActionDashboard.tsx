"use client";

import { useEffect, useState } from "react";
import type { GameState } from "@/lib/types";
import { money, moneyShort, playerColor, productMeta, TONE_CLASSES } from "@/lib/format";
import Dice from "./Dice";

interface ActionDashboardProps {
  game: GameState;
  busy?: boolean;
  onExecute: (quantity: number) => void;
}

export default function ActionDashboard({ game, busy, onExecute }: ActionDashboardProps) {
  const isBuy = !!game.can_buy;
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

  useEffect(() => {
    setQty(maxQty);
  }, [game.current_player, game.current_market_index, game.can_buy, game.can_sell]); // eslint-disable-line react-hooks/exhaustive-deps

  const meta = market ? productMeta(market.product) : null;
  const actor = game.current_player ?? "The market";
  const player = game.players.find((p) => p.username === actor);
  const colorOf = (name: string) =>
    playerColor(Math.max(0, game.players.findIndex((p) => p.username === name)));
  const pc = colorOf(actor);

  const marketPrice = market?.market_fixed_price ?? 0;
  const taxRate = market?.tax_rate ?? 0;
  const entryFee = market?.sell_entry_fee ?? 0;
  const dicePrice = game.dice_price ?? dicePriceSafe(dieTotal);

  // --- Math preview ---
  const unitPrice = isBuy ? marketPrice : dicePrice;
  const gross = qty * unitPrice;
  const tax = Math.round(gross * taxRate);
  const total = isBuy ? gross + tax : gross - tax;
  const balance = player?.balance ?? 0;
  const newBalance = isBuy ? balance - total : balance + total;

  // Cost basis for the product we're trading (avg price paid per unit).
  const invItem = player?.inventory.find((it) => it.product.name === market?.product);
  const avgCost = invItem?.avg_cost ?? 0;
  const profitPerUnit = !isBuy && avgCost > 0 ? unitPrice - avgCost : null;
  const profitTotal = profitPerUnit != null ? profitPerUnit * qty : null;

  const hist = market?.price_history ?? [];
  const last = hist.length > 0 ? hist[hist.length - 1] : marketPrice;
  const prev = hist.length > 1 ? hist[hist.length - 2] : last;
  const pct = prev ? ((last - prev) / prev) * 100 : 0;
  const trendDown = pct < -0.1;
  const trendUp = pct > 0.1;
  const trendLabel = trendUp
    ? `▲ ${Math.abs(pct).toFixed(1)}%`
    : trendDown
    ? `▼ ${Math.abs(pct).toFixed(1)}%`
    : "—";

  // ---- failure card ----
  if (game.action_failed) {
    return (
      <div className="grid w-full grid-cols-1 gap-4 lg:grid-cols-[17rem_minmax(0,1fr)_17rem]">
        <PlayerSideBar game={game} actor={actor} pc={pc} balance={balance} />
        <div className="flex flex-col gap-4">
          <MarketCard market={market} meta={meta} trendLabel={trendLabel} trendUp={trendUp} trendDown={trendDown} />
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-sell/40 bg-sell/5 p-5">
            <div className="flex items-center gap-3">
              {meta && (
                <span className={`flex h-12 w-12 items-center justify-center rounded-xl border text-2xl ${TONE_CLASSES[meta.tone]}`}>
                  {meta.icon}
                </span>
              )}
              <div className="text-left">
                <p className="text-sm font-bold text-sell">❌ Trade didn't go through</p>
                <p className="mt-1 text-[11px] text-bright">{game.action_fail_reason}</p>
              </div>
            </div>
            <p className="text-[10px] text-dim">
              🎲 Rolled {game.dice_total} → dice price {money(game.dice_price ?? 0)}
            </p>
            <button
              type="button"
              onClick={() => onExecute(0)}
              disabled={busy}
              className="rounded-xl bg-dim px-8 py-2 font-display text-xs font-bold uppercase tracking-widest text-white transition-all hover:brightness-110 active:scale-95 disabled:opacity-50"
            >
              {busy ? "…" : "Continue"}
            </button>
          </div>
        </div>
        <PlayersSideBar game={game} actor={actor} />
      </div>
    );
  }

  return (
    <div className="grid w-full grid-cols-1 gap-4 lg:grid-cols-[17rem_minmax(0,1fr)_17rem]">
      {/* LEFT: player */}
      <div className="flex flex-col gap-4">
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">Trading</p>
          <div className={`mt-2 flex items-center gap-2 ${pc.avatar} h-12 w-12 rounded-full`}>
            <span className="w-full text-center font-display text-lg font-black">
              {actor.slice(0, 1).toUpperCase()}
            </span>
          </div>
          <p className={`mt-2 truncate font-display text-sm font-bold ${pc.text}`}>{actor}</p>
          <p className="mt-1 text-[11px] text-dim">
            Balance{" "}
            <span className="font-display text-sm font-bold text-gold">{money(balance)}</span>
          </p>
          {player && player.inventory.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {player.inventory.map((it) => (
                <span
                  key={it.product.name}
                  className="inline-flex items-center gap-1 rounded-md border border-[rgba(100,180,255,0.12)] bg-board/50 px-1.5 py-0.5 text-[11px]"
                  title={it.product.name}
                >
                  {productMeta(it.product.name).icon}
                  <b className={it.quantity > 0 ? "text-bright" : "text-dim/50"}>{it.quantity}</b>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* CENTER */}
      <div className="flex flex-col gap-4">
        <MarketCard market={market} meta={meta} trendLabel={trendLabel} trendUp={trendUp} trendDown={trendDown} />

        {/* Dice */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            Your dice (2d6)
          </p>
          <div className="mt-2 flex flex-wrap items-center justify-center gap-4">
            <Dice die1={die1} die2={die2} total={dieTotal} size="lg" rolling />
            <div className="text-center">
              <p className="font-display text-2xl font-black text-gold">
                {dieTotal ?? "—"}
              </p>
              <p className="text-[10px] text-dim">→ dice price</p>
              <p className="font-display text-base font-bold text-cyan">{money(dicePrice)}</p>
            </div>
          </div>
        </div>

        {/* Action + quantity + breakdown */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
          <div className="flex items-center justify-between">
            <p className={`font-display text-sm font-black uppercase tracking-wide ${isBuy ? "text-buy" : "text-sell"}`}>
              {isBuy ? "⬇ Buy" : "⬆ Sell"} {market?.product}
            </p>
            <p className={`text-[10px] font-bold ${isBuy ? "text-buy" : "text-sell"}`}>
              {isBuy
                ? `dice ${money(dicePrice)} ≥ ${money(marketPrice)} needed`
                : `dice ${money(dicePrice)} ≤ ${money(marketPrice)}`}
            </p>
          </div>

          <div className="mt-2 rounded-lg border border-[rgba(100,180,255,0.08)] bg-board/40 p-2 text-[11px]">
            {isBuy ? (
              <p className="text-buy">
                ✅ Success — dice price {money(dicePrice)} ≥ market {money(marketPrice)}
              </p>
            ) : (
              <p className="text-sell">
                ✅ Success — dice price {money(dicePrice)} ≤ market {money(marketPrice)}
              </p>
            )}
          </div>

          {/* Quantity */}
          <div className="mt-3 flex items-center justify-center gap-2">
            <span className="text-[10px] uppercase tracking-wider text-dim">Quantity</span>
            <button
              type="button"
              onClick={() => setQty((q) => Math.max(1, q - 1))}
              className="h-9 w-9 rounded-lg border border-[rgba(100,180,255,0.2)] bg-card text-lg text-bright hover:border-gold/40"
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
              className="h-9 w-16 rounded-lg border border-[rgba(100,180,255,0.2)] bg-card text-center font-display text-lg font-bold text-gold outline-none focus:border-gold/50"
            />
            <button
              type="button"
              onClick={() => setQty((q) => Math.min(maxQty, q + 1))}
              className="h-9 w-9 rounded-lg border border-[rgba(100,180,255,0.2)] bg-card text-lg text-bright hover:border-gold/40"
            >
              +
            </button>
            <span className="text-[10px] text-dim">max {maxQty}</span>
          </div>

          {/* Breakdown */}
          <div className="mt-3 space-y-1 rounded-lg border border-[rgba(100,180,255,0.08)] bg-board/40 p-2 text-[11px]">
            {isBuy ? (
              <>
                <Row label={`Cost (${qty} × ${moneyShort(unitPrice)})`} value={`−${money(gross)}`} />
                <Row label={`Tax (${Math.round(taxRate * 100)}%)`} value={`−${money(tax)}`} />
                <Row label="Total" value={`${money(total)}`} strong />
              </>
            ) : (
              <>
                <Row
                  label="Cost basis"
                  value={`${money(avgCost)}/u`}
                  note={`you paid ${money(avgCost * qty)} for ${qty}u`}
                />
                {profitTotal != null && (
                  <Row
                    label="Profit vs sell price"
                    value={`${profitTotal >= 0 ? "+" : ""}${money(profitTotal)}`}
                    accent
                    note={`${moneyShort(profitPerUnit ?? 0)}/u`}
                  />
                )}
                <Row label={`Revenue (${qty} × ${moneyShort(unitPrice)})`} value={`+${money(gross)}`} />
                <Row label={`Entry fee`} value={`−${money(entryFee)}`} note="paid at entry" />
                <Row label={`Tax (${Math.round(taxRate * 100)}%)`} value={`−${money(tax)}`} />
                <Row label="You receive" value={`+${money(total)}`} strong />
              </>
            )}
            <Row label="New balance" value={money(newBalance)} accent />
          </div>

          <button
            type="button"
            onClick={() => onExecute(qty)}
            disabled={busy}
            className={`mt-3 w-full rounded-xl py-2.5 font-display text-sm font-bold uppercase tracking-widest text-deep transition-all hover:brightness-110 active:scale-[0.99] disabled:opacity-50 ${
              isBuy
                ? "bg-buy shadow-[0_0_16px_rgba(0,230,138,0.4)]"
                : "bg-sell text-white shadow-[0_0_16px_rgba(255,77,106,0.4)]"
            }`}
          >
            {busy ? "…" : `${isBuy ? "Buy" : "Sell"} ${qty} ${market?.product ?? ""}`.trim()}
          </button>
        </div>
      </div>

      {/* RIGHT: opponents */}
      <PlayersSideBar game={game} actor={actor} />
    </div>
  );
}

function dicePriceSafe(total: number | null): number {
  return (total ?? 2) * 100;
}

function Row({
  label,
  value,
  strong,
  note,
  accent,
}: {
  label: string;
  value: string;
  strong?: boolean;
  note?: string;
  accent?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-dim">
        {label}
        {note && <span className="ml-1 text-[9px] text-dim/60">({note})</span>}
      </span>
      <span
        className={`font-display font-bold ${
          strong ? "text-lg text-bright" : accent ? "text-gold" : "text-bright"
        }`}
      >
        {value}
      </span>
    </div>
  );
}

function MarketCard({
  market,
  meta,
  trendLabel,
  trendUp,
  trendDown,
}: {
  market?: { product: string; name: string; market_fixed_price: number; market_supply: number; tax_rate: number; sell_entry_fee: number } | null;
  meta: ReturnType<typeof productMeta> | null;
  trendLabel: string;
  trendUp: boolean;
  trendDown: boolean;
}) {
  if (!market || !meta) {
    return (
      <div className="flex items-center justify-center rounded-2xl border border-dashed border-[rgba(100,180,255,0.12)] bg-board/30 p-4 text-[11px] text-dim">
        No market active this round
      </div>
    );
  }
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
      <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border text-2xl ${TONE_CLASSES[meta.tone]}`}>
        {meta.icon}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-bold">{market.product}</p>
        <p className="text-[10px] text-dim">{market.name}</p>
        <p className={`text-[10px] ${trendUp ? "text-buy" : trendDown ? "text-sell" : "text-dim"}`}>
          {trendLabel}
        </p>
      </div>
      <div className="shrink-0 text-right">
        <p className="font-display text-xl font-black text-cyan">{moneyShort(market.market_fixed_price)}</p>
        <p className="text-[10px] text-dim">
          {market.market_supply}u · tax {Math.round(market.tax_rate * 100)}% · fee {moneyShort(market.sell_entry_fee)}
        </p>
      </div>
    </div>
  );
}

function PlayerSideBar({
  game,
  actor,
  pc,
  balance,
}: {
  game: GameState;
  actor: string;
  pc: ReturnType<typeof playerColor>;
  balance: number;
}) {
  const player = game.players.find((p) => p.username === actor);
  return (
    <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
      <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">Trading</p>
      <div className={`mt-2 flex h-12 w-12 items-center justify-center rounded-full ${pc.avatar}`}>
        <span className="font-display text-lg font-black">{actor.slice(0, 1).toUpperCase()}</span>
      </div>
      <p className={`mt-2 truncate font-display text-sm font-bold ${pc.text}`}>{actor}</p>
      <p className="mt-1 text-[11px] text-dim">
        Balance <span className="font-display text-sm font-bold text-gold">{money(balance)}</span>
      </p>
      {player && player.inventory.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {player.inventory.map((it) => (
            <span
              key={it.product.name}
              className="inline-flex items-center gap-1 rounded-md border border-[rgba(100,180,255,0.12)] bg-board/50 px-1.5 py-0.5 text-[11px]"
            >
              {productMeta(it.product.name).icon}
              <b>{it.quantity}</b>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function PlayersSideBar({ game, actor }: { game: GameState; actor: string }) {
  const others = game.players.filter((p) => p.username !== actor);
  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
        <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">Players</p>
        <div className="mt-2 flex flex-col gap-1.5">
          {others.map((p) => {
            const c = playerColor(Math.max(0, game.players.findIndex((x) => x.username === p.username)));
            return (
              <div key={p.username} className="flex items-center gap-2 rounded-lg border border-[rgba(100,180,255,0.08)] bg-board/40 px-2 py-1.5 text-[11px]">
                <span className={`flex h-5 w-5 items-center justify-center rounded-full text-[9px] font-black ${c.avatar}`}>
                  {p.username.slice(0, 1).toUpperCase()}
                </span>
                <span className="truncate font-semibold text-bright">{p.username}</span>
                <span className="ml-auto font-display font-bold text-cyan">{moneyShort(p.balance)}</span>
              </div>
            );
          })}
        </div>
      </div>
      {game.markets
        .filter((m) => m.market_index !== game.current_market_index)
        .map((m) => {
          const meta = productMeta(m.product);
          return (
            <div key={m.market_index} className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
              <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">Market</p>
              <div className="mt-2 flex items-center gap-2">
                <span className={`flex h-9 w-9 items-center justify-center rounded-lg border text-lg ${TONE_CLASSES[meta.tone]}`}>
                  {meta.icon}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-xs font-semibold">{m.product}</p>
                  <p className="text-[10px] text-dim">{m.name}</p>
                </div>
                <p className="ml-auto font-display font-bold text-cyan">{moneyShort(m.market_fixed_price)}</p>
              </div>
            </div>
          );
        })}
    </div>
  );
}
