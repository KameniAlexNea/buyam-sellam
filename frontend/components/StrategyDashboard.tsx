"use client";

import { useMemo } from "react";
import type {
  GameState,
  MarketAction,
  MarketInfo,
  PlayerInfo,
} from "@/lib/types";
import { money, moneyShort, playerColor, productMeta, TONE_CLASSES } from "@/lib/format";
import {
  probAtLeast,
  probAtMost,
  probLabel,
  rollForBuy,
  rollForSell,
} from "@/lib/dice";
import { useI18n } from "@/lib/i18n";

interface StrategyDashboardProps {
  game: GameState;
  planner: string;
  plannerPlayer?: PlayerInfo | null;
  humanPlayers: string[];
  choices: Record<number, MarketAction>;
  onChoice: (index: number, action: MarketAction) => void;
  busy?: boolean;
  canSubmit?: boolean;
  onConfirm: () => void;
}

const ACTIONS: MarketAction[] = ["buy", "sell", "skip"];
const CYCLE: MarketAction[] = ["skip", "buy", "sell"];

/** 2d6 distribution: roll → count out of 36. */
const DIST: { roll: number; prob: number }[] = [
  { roll: 2, prob: 1 },
  { roll: 3, prob: 2 },
  { roll: 4, prob: 3 },
  { roll: 5, prob: 4 },
  { roll: 6, prob: 5 },
  { roll: 7, prob: 6 },
  { roll: 8, prob: 5 },
  { roll: 9, prob: 4 },
  { roll: 10, prob: 3 },
  { roll: 11, prob: 2 },
  { roll: 12, prob: 1 },
].map((d) => ({ roll: d.roll, prob: d.prob / 36 }));

export default function StrategyDashboard({
  game,
  planner,
  plannerPlayer,
  humanPlayers,
  choices,
  onChoice,
  busy,
  canSubmit = true,
  onConfirm,
}: StrategyDashboardProps) {
  const markets = game.markets;
  const players = game.players;
  const { t } = useI18n();

  const ownedProducts = useMemo(() => {
    const map: Record<string, number> = {};
    plannerPlayer?.inventory.forEach((it) => {
      map[it.product.name] = it.quantity;
    });
    return map;
  }, [plannerPlayer]);

  // Average price paid per unit, per product (cost basis for sells).
  const avgCosts = useMemo(() => {
    const map: Record<string, number> = {};
    plannerPlayer?.inventory.forEach((it) => {
      map[it.product.name] = it.avg_cost;
    });
    return map;
  }, [plannerPlayer]);

  const chosen = markets.filter(
    (m) => (choices[m.market_index] ?? "skip") !== "skip"
  ).length;

  const planSellFees = markets
    .filter((m) => (choices[m.market_index] ?? "skip") === "sell")
    .reduce((sum, m) => sum + m.sell_entry_fee, 0);

  const chosenActions = markets
    .map((m) => {
      const a = choices[m.market_index] ?? "skip";
      if (a === "skip") return null;
      const buyProb = probAtLeast(rollForBuy(m.market_fixed_price));
      const sellProb = probAtMost(rollForSell(m.market_fixed_price));
      return a === "buy" ? buyProb : sellProb;
    })
    .filter((p): p is number => p != null);

  const avgProb =
    chosenActions.length > 0
      ? chosenActions.reduce((s, p) => s + p, 0) / chosenActions.length
      : 0;
  const risk =
    chosenActions.length === 0
      ? "—"
      : avgProb >= 0.6
      ? t("plan.riskLow")
      : avgProb >= 0.35
      ? t("plan.riskMedium")
      : t("plan.riskHigh");
  const riskCls =
    risk === "LOW"
      ? "text-buy"
      : risk === "MEDIUM"
      ? "text-amberc"
      : risk === "HIGH"
      ? "text-sell"
      : "text-dim";

  // --- Left panel helpers ---
  const planBtn = (m: MarketInfo) => {
    const sel = choices[m.market_index] ?? "skip";
    const cls =
      sel === "buy"
        ? "bg-buy/20 border-buy text-buy"
        : sel === "sell"
        ? "bg-sell/20 border-sell text-sell"
        : "border-[rgba(100,180,255,0.15)] text-dim";
    return (
      <button
        key={m.market_index}
        type="button"
        onClick={() => onChoice(m.market_index, CYCLE[(CYCLE.indexOf(sel) + 1) % 3])}
        className={`flex w-full items-center justify-between gap-2 rounded-lg border bg-card/50 px-2.5 py-2 text-left transition-colors hover:border-gold/40 ${cls}`}
      >
        <span className="min-w-0">
          <span className="block truncate text-[11px] font-bold uppercase tracking-wide">
            {productMeta(m.product).icon} {m.product}
          </span>
          <span className="block text-[9px] text-dim">{m.name}</span>
        </span>
        <span className="shrink-0 rounded-md bg-board/70 px-1.5 py-0.5 font-display text-[9px] font-black tracking-wider">
          {sel === "buy" ? t("plan.buyBadge") : sel === "sell" ? t("plan.sellBadge") : t("plan.skipBadge")}
        </span>
      </button>
    );
  };

  // --- Right panel helpers ---
  const colorOf = (name: string) =>
    playerColor(Math.max(0, players.findIndex((p) => p.username === name)));

  const tradeCard = (m: MarketInfo) => {
    const meta = productMeta(m.product);
    const owned = ownedProducts[m.product] ?? 0;
    const avgCost = avgCosts[m.product] ?? 0;
    const canSell = owned > 0;
    const profit = canSell && avgCost > 0 ? m.market_fixed_price - avgCost : null;
    const sel = choices[m.market_index] ?? "skip";
    const buyRoll = rollForBuy(m.market_fixed_price);
    const sellRoll = rollForSell(m.market_fixed_price);
    const buyProb = probAtLeast(buyRoll);
    const sellProb = probAtMost(sellRoll);
    return (
      <div
        key={m.market_index}
        className={`rounded-xl border p-3 transition-colors ${
          sel === "buy"
            ? "border-buy/50 bg-buy/5"
            : sel === "sell"
            ? "border-sell/50 bg-sell/5"
            : "border-[rgba(100,180,255,0.12)] bg-card/60"
        }`}
      >
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
          <p className="shrink-0 text-right font-display text-sm font-bold text-cyan">
            {moneyShort(m.market_fixed_price)}
          </p>
        </div>

        {/* Buy / sell windows */}
        <div className="mt-2.5 grid grid-cols-2 gap-2">
          <div className="rounded-lg border border-buy/20 bg-buy/5 p-2">
            <p className="font-display text-[9px] font-black uppercase tracking-wider text-buy">
              {t("plan.buySucceedsOn")}
            </p>
            <p className="mt-0.5 font-display text-base font-bold text-bright">
              {buyRoll}–12
            </p>
            <p className="text-[9px] text-dim">
              {t("plan.dicePriceGte", { price: moneyShort(m.market_fixed_price) })}
            </p>
            <p className="mt-1 font-display text-sm font-black text-buy">
              {probLabel(buyProb)}
            </p>
          </div>
          <div className="rounded-lg border border-sell/20 bg-sell/5 p-2">
            <p className="font-display text-[9px] font-black uppercase tracking-wider text-sell">
              {t("plan.sellSucceedsOn")}
            </p>
            <p className="mt-0.5 font-display text-base font-bold text-bright">
              2–{sellRoll}
            </p>
            <p className="text-[9px] text-dim">
              {t("plan.dicePriceLte", { price: moneyShort(m.market_fixed_price) })}
            </p>
            <p className="mt-1 font-display text-sm font-black text-sell">
              {probLabel(sellProb)}
            </p>
          </div>
        </div>

        {sel === "sell" && (
          <p className="mt-1.5 text-[10px] text-amberc">
            {t("plan.entryFeeWarn", { fee: moneyShort(m.sell_entry_fee) })}
          </p>
        )}

        {/* Action buttons */}
        <div className="mt-2.5 grid grid-cols-3 gap-1.5">
          {ACTIONS.map((a) => {
            const selected = sel === a;
            const disabled = a === "sell" && !canSell;
            const base =
              a === "buy"
                ? "bg-buy text-deep border-buy"
                : a === "sell"
                ? "bg-sell text-white border-sell"
                : "bg-dim/70 text-white border-dim/70";
            return (
              <button
                key={a}
                type="button"
                disabled={disabled}
                onClick={() => onChoice(m.market_index, a)}
                title={disabled ? `${planner} doesn't have ${m.product} in inventory` : undefined}
                className={`rounded-lg border py-1.5 text-[11px] font-black uppercase tracking-wide transition-all ${
                  selected
                    ? `${base} shadow-[0_0_12px_rgba(0,0,0,0.25)]`
                    : "border-[rgba(100,180,255,0.12)] bg-card text-dim hover:text-bright"
                } ${disabled ? "cursor-not-allowed opacity-30" : ""}`}
              >
                {selected ? "✓ " : ""}
                {a === "buy" ? t("plan.buy") : a === "sell" ? t("plan.sell") : t("plan.skip")}
              </button>
            );
          })}
        </div>
        {sel === "sell" && (
          <p className="mt-1 text-[10px] text-dim">
            {t("plan.youOwn", { qty: owned, product: m.product })}
          </p>
        )}
        {canSell && (
          <p className="mt-1.5 flex items-center justify-between rounded-md border border-[rgba(100,180,255,0.08)] bg-board/40 px-2 py-1 text-[10px]">
            <span className="text-dim">
              {t("plan.costBasis", { cost: money(avgCost) })}
            </span>
            <span className={profit != null && profit >= 0 ? "text-buy" : "text-sell"}>
              {profit != null
                ? t("plan.vsMarket", { signed: `${profit >= 0 ? "+" : ""}${money(profit)}` })
                : t("plan.noCost")}
            </span>
          </p>
        )}
      </div>
    );
  };

  return (
    <div className="grid w-full grid-cols-1 gap-4 lg:h-full lg:min-h-0 lg:grid-cols-[17rem_minmax(0,1fr)_17rem]">
      {/* ---------- LEFT: player + markets ---------- */}
      <div className="flex min-h-0 flex-col gap-4 lg:overflow-y-auto">
        {/* You */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            {t("plan.you")}
          </p>
          <div className="mt-1 flex flex-wrap gap-1.5">
            {plannerPlayer?.inventory.map((it) => (
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
          <p className="mt-2 text-[11px] text-dim">
            {t("plan.cash")}{" "}
            <span className="font-display text-sm font-bold text-gold">
              {money(plannerPlayer?.balance ?? 0)}
            </span>
          </p>
        </div>

        {/* Active markets */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            {t("plan.activeMarkets", { count: markets.length })}
          </p>
          <div className="mt-2 flex flex-col gap-1.5">
            {markets.map((m) => (
              <div key={m.market_index} className="rounded-lg border border-[rgba(100,180,255,0.08)] bg-board/40 p-2">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="truncate font-semibold text-bright">
                    {productMeta(m.product).icon} {m.product}
                  </span>
                  <span className="font-display font-bold text-cyan">{moneyShort(m.market_fixed_price)}</span>
                </div>
                <div className="mt-0.5 text-[9px] text-dim">
                  {t("plan.supply", {
                    supply: m.market_supply,
                    tax: Math.round(m.tax_rate * 100),
                    fee: moneyShort(m.sell_entry_fee),
                  })}
                </div>
                {planBtn(m)}
              </div>
            ))}
          </div>
        </div>

        {/* Inventory */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            {t("plan.inventory", { count: plannerPlayer?.inventory.length ?? 0 })}
          </p>
          <div className="mt-2 flex flex-col gap-1">
            {plannerPlayer?.inventory.map((it) => {
              const totalVal = it.quantity * it.avg_cost;
              return (
                <div key={it.product.name} className="flex items-center justify-between rounded-md bg-board/40 px-2 py-1 text-[11px]">
                  <span className="truncate text-bright">
                    {productMeta(it.product.name).icon} {it.product.name}
                  </span>
                  <span className="flex shrink-0 items-center gap-2">
                    <span className="font-display font-bold text-cyan">× {it.quantity}</span>
                    <span className="text-[9px] text-dim" title={`avg cost ${money(it.avg_cost)}/u · value ${money(totalVal)}`}>
                      @ {moneyShort(it.avg_cost)}
                    </span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ---------- CENTER: trades + summary ---------- */}
      <div className="flex min-h-0 flex-col gap-4 lg:overflow-y-auto">
        {/* Trade cards */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            {t("plan.title")}
          </p>
          <p className="mt-0.5 text-[10px] text-dim">
            {t("plan.subtitle")}
          </p>
          <div className="mt-2 flex flex-col gap-2">
            {markets.map(tradeCard)}
          </div>
        </div>

        {/* Plan summary + confirm */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            {t("plan.summary")}
          </p>
          <div className="mt-2 flex flex-col gap-1.5">
            {markets.map((m) => {
              const a = choices[m.market_index] ?? "skip";
              const buyRoll = rollForBuy(m.market_fixed_price);
              const sellRoll = rollForSell(m.market_fixed_price);
              return (
                <div
                  key={m.market_index}
                  className={`flex items-center justify-between rounded-lg border px-2 py-1.5 text-[11px] ${
                    a === "buy"
                      ? "border-buy/25 bg-buy/5 text-buy"
                      : a === "sell"
                      ? "border-sell/25 bg-sell/5 text-sell"
                      : "border-[rgba(100,180,255,0.08)] bg-board/40 text-dim"
                  }`}
                >
                  <span className="truncate font-semibold">
                    {productMeta(m.product).icon} {m.product}
                  </span>
                  <span className="shrink-0 font-black uppercase">
                    {a === "buy"
                      ? t("plan.buyNeeds", { roll: buyRoll })
                      : a === "sell"
                      ? t("plan.sellNeeds", { roll: sellRoll })
                      : t("plan.skipAction")}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="mt-2.5 grid grid-cols-3 gap-2 text-center text-[10px]">
            <div className="rounded-lg bg-board/50 p-1.5">
              <p className="text-dim">{t("plan.estFees")}</p>
              <p className="font-display font-bold text-bright">{moneyShort(planSellFees)}</p>
            </div>
            <div className="rounded-lg bg-board/50 p-1.5">
              <p className="text-dim">{t("plan.risk")}</p>
              <p className={`font-display font-bold ${riskCls}`}>{risk}</p>
            </div>
            <div className="rounded-lg bg-board/50 p-1.5">
              <p className="text-dim">{t("plan.actions")}</p>
              <p className="font-display font-bold text-gold">{chosen}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onConfirm}
            disabled={busy || !canSubmit}
            className="mt-2.5 w-full rounded-xl bg-gold py-2.5 font-display text-sm font-bold uppercase tracking-widest text-deep shadow-glow-gold transition-all hover:brightness-110 active:scale-[0.99] disabled:opacity-50"
          >
            {busy
              ? t("plan.resolving")
              : !canSubmit
              ? t("plan.waiting")
              : t("plan.confirm", { count: Math.max(1, markets.length) })}
          </button>
          <p className="mt-1 text-center text-[9px] text-dim">
            {t("plan.planned", { chosen, total: markets.length })}
          </p>
        </div>
      </div>

      {/* ---------- RIGHT: players + rules + inventory ---------- */}
      <div className="flex min-h-0 flex-col gap-4 lg:overflow-y-auto">
        {/* Players — ranked by cash so you can see who's winning */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            {t("players")}
          </p>
          <div className="mt-2 flex flex-col gap-1">
            {[...players]
              .sort((a, b) => b.balance - a.balance)
              .map((p, i) => {
                const c = colorOf(p.username);
                const submitted = game.strategies_submitted.includes(p.username);
                const isPlanner = p.username === planner;
                const isHuman = humanPlayers.includes(p.username);
                const rank = i + 1;
                const rankCls =
                  rank === 1
                    ? "bg-gold text-deep"
                    : rank === 2
                    ? "bg-dim/80 text-white"
                    : rank === 3
                    ? "bg-amberc/70 text-deep"
                    : "bg-board text-dim";
                return (
                  <div
                    key={p.username}
                    className={`flex items-center gap-2 rounded-lg border px-2 py-1.5 text-[11px] ${
                      isPlanner
                        ? "border-gold/40 bg-gold/5"
                        : "border-[rgba(100,180,255,0.08)] bg-board/40"
                    }`}
                  >
                    <span className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[9px] font-black ${rankCls}`}>
                      {rank}
                    </span>
                    <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[9px] font-black ${c.avatar}`}>
                      {p.username.slice(0, 1).toUpperCase()}
                    </span>
                    <span className={`truncate font-semibold ${isPlanner ? c.text : "text-bright"}`}>
                      {p.username}
                    </span>
                    {isHuman && <span className="text-[8px] font-bold text-gold/80">{t("plan.youTag")}</span>}
                    <span className="ml-auto shrink-0 font-display font-bold text-cyan">
                      {moneyShort(p.balance)}
                    </span>
                    <span className="shrink-0 font-black">
                      {submitted ? "✓" : isPlanner ? "◌" : "…"}
                    </span>
                  </div>
                );
              })}
          </div>
        </div>

        {/* Your next roll + probability guide */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-3 text-center">
          <p className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            {t("plan.nextRoll")}
          </p>
          <p className="mt-1 font-display text-xl font-black text-gold">{t("plan.rollRange")}</p>
          <p className="text-[11px] text-bright">{t("plan.rollPrice")}</p>
          <p className="text-[10px] text-dim">{t("plan.rollFormula")}</p>

          {/* Probability guide bars */}
          <p className="mt-3 font-display text-[9px] font-bold uppercase tracking-[0.3em] text-dim">
            {t("plan.probGuide")}
          </p>
          <div className="mt-1.5 flex items-end justify-center gap-0.5">
            {DIST.map((d) => (
              <div key={d.roll} className="flex flex-col items-center gap-0.5">
                <span className="text-[8px] font-bold text-dim">
                  {Math.round(d.prob * 100).toFixed(1).replace(".0", "")}%
                </span>
                <div
                  className={`w-4 rounded-sm ${d.roll === 7 ? "bg-gold" : "bg-cyan/50"}`}
                  style={{ height: `${Math.max(4, d.prob * 110)}px` }}
                />
                <span className={`text-[8px] font-bold ${d.roll === 7 ? "text-gold" : "text-dim"}`}>
                  {d.roll}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
