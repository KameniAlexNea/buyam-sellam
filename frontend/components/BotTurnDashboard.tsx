"use client";

import type { GameState, MoveFeedEntry } from "@/lib/types";
import { money, moneyShort, playerColor, productMeta, TONE_CLASSES } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import Dice from "./Dice";

interface BotTurnDashboardProps {
  game: GameState;
}

/** Render one move-feed entry as a compact "what happened" row. */
function MoveRow({ move, index }: { move: MoveFeedEntry; index: number }) {
  const { t } = useI18n();
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
    label = t("move.rolled", { dice: move.dice_total, price: money(move.dice_price ?? 0) });
  } else if (move.action === "buy") {
    label = t("move.bought", {
      qty: move.quantity,
      product: move.product,
      price: money(move.unit_price ?? 0),
      cost: money(move.total ?? 0),
    });
  } else if (move.action === "sell") {
    label = t("move.sold", {
      qty: move.quantity,
      product: move.product,
      price: money(move.unit_price ?? 0),
      revenue: money(move.total ?? 0),
    });
  } else if (move.action === "skip") {
    label = t("move.skipped", { reason: move.reason ?? t("move.noTrade") });
  } else {
    label = t("move.failed", { reason: move.reason ?? t("move.condition") });
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
 * Bot's action turn as a 3-column dashboard (mirrors the human ActionDashboard):
 * left = the trading bot's card, center = dice + live move replay, right =
 * the other players' balances.
 */
export default function BotTurnDashboard({ game }: BotTurnDashboardProps) {
  const feed = game.move_feed ?? [];
  const recent = feed.slice(-6).reverse();

  const dieTotal = game.dice_total;
  const die1 = dieTotal ? Math.ceil(dieTotal / 2) : null;
  const die2 = dieTotal && die1 != null ? dieTotal - die1 : null;
  const dicePrice = game.dice_price ?? (dieTotal ?? 2) * 100;
  const actor = game.current_player ?? "The market";
  const player = game.players.find((p) => p.username === actor);
  const pc = playerColor(Math.max(0, game.players.findIndex((p) => p.username === actor)));

  const market = game.markets.find((m) => m.market_index === game.current_market_index);
  const meta = market ? productMeta(market.product) : null;
  const hist = market?.price_history ?? [];
  const last = hist.length > 0 ? hist[hist.length - 1] : market?.market_fixed_price ?? 0;
  const prev = hist.length > 1 ? hist[hist.length - 2] : last;
  const pct = prev ? ((last - prev) / prev) * 100 : 0;
  const trendUp = pct > 0.1;
  const trendDown = pct < -0.1;
  const trendLabel = trendUp
    ? `▲ ${Math.abs(pct).toFixed(1)}%`
    : trendDown
    ? `▼ ${Math.abs(pct).toFixed(1)}%`
    : "—";

  return (
    <div className="grid w-full grid-cols-1 gap-4 lg:h-full lg:min-h-0 lg:grid-cols-[17rem_minmax(0,1fr)_17rem]">
      {/* LEFT: trading bot */}
      <div className="flex min-h-0 flex-col gap-4 lg:overflow-y-auto">
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            {t("bot.turn")}
          </p>
          <div className={`mt-2 flex h-12 w-12 items-center justify-center rounded-full ${pc.avatar}`}>
            <span className="font-display text-lg font-black">{actor.slice(0, 1).toUpperCase()}</span>
          </div>
          <p className={`mt-2 truncate font-display text-sm font-bold ${pc.text}`}>{actor}</p>
          <p className="mt-1 text-[11px] text-dim">
            {t("bot.balance")}{" "}
            <span className="font-display text-sm font-bold text-gold">
              {money(player?.balance ?? 0)}
            </span>
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

      {/* CENTER: dice + replay */}
      <div className="flex min-h-0 flex-col gap-4 lg:overflow-y-auto">
        {/* Active market */}
        {market && meta && (
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
              <p className="font-display text-xl font-black text-cyan">
                {moneyShort(market.market_fixed_price)}
              </p>
              <p className="text-[10px] text-dim">
                {t("action.marketInfo", {
                  supply: market.market_supply,
                  tax: Math.round(market.tax_rate * 100),
                  fee: moneyShort(market.sell_entry_fee),
                })}
              </p>
            </div>
          </div>
        )}

        {/* Dice */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            {t("bot.isTrading", { actor })}
          </p>
          <div className="mt-2 flex flex-wrap items-center justify-center gap-4">
            <Dice die1={die1} die2={die2} total={dieTotal} size="lg" rolling />
            <div className="text-center">
              <p className="font-display text-2xl font-black text-gold">{dieTotal ?? "—"}</p>
              <p className="text-[10px] text-dim">{t("bot.dicePrice")}</p>
              <p className="font-display text-base font-bold text-cyan">{money(dicePrice)}</p>
            </div>
          </div>
        </div>

        {/* Replay feed */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            {t("bot.actionReplay")}
          </p>
          <div className="mt-2 flex flex-col gap-1.5">
            {recent.length === 0 ? (
              <div className="flex items-center gap-3 rounded-2xl border border-[rgba(100,180,255,0.1)] bg-board/50 px-6 py-4">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-gold/30 border-t-gold" />
                <p className="text-sm text-dim">{t("bot.resolving")}</p>
              </div>
            ) : (
              <>
                {recent.map((m, i) => (
                  <MoveRow key={`${m.round}-${m.player}-${i}`} move={m} index={i} />
                ))}
                <div className="mt-1 flex items-center justify-center gap-2 text-[10px] uppercase tracking-widest text-dim/70">
                  <span className="h-3 w-3 animate-pulse rounded-full bg-gold/60" />
                  {t("bot.automatic")}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* RIGHT: other players */}
      <div className="flex min-h-0 flex-col gap-4 lg:overflow-y-auto">
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            {t("players")}
          </p>
          <div className="mt-2 flex flex-col gap-1.5">
            {[...game.players]
              .sort((a, b) => b.balance - a.balance)
              .map((p) => {
                const c = playerColor(Math.max(0, game.players.findIndex((x) => x.username === p.username)));
                const active = p.username === actor;
                return (
                  <div
                    key={p.username}
                    className={`flex items-center gap-2 rounded-lg border px-2 py-1.5 text-[11px] ${
                      active
                        ? "border-gold/40 bg-gold/5"
                        : "border-[rgba(100,180,255,0.08)] bg-board/40"
                    }`}
                  >
                    <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[9px] font-black ${c.avatar}`}>
                      {p.username.slice(0, 1).toUpperCase()}
                    </span>
                    <span className={`truncate font-semibold ${active ? c.text : "text-bright"}`}>
                      {p.username}
                    </span>
                    {active && <span className="text-[8px] font-bold text-gold/80">{t("bot.tradingTag")}</span>}
                    <span className="ml-auto shrink-0 font-display font-bold text-cyan">
                      {moneyShort(p.balance)}
                    </span>
                  </div>
                );
              })}
          </div>
        </div>
      </div>
    </div>
  );
}
