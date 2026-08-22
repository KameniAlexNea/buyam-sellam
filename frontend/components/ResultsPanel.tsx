"use client";

import type { Results, Standing } from "@/lib/types";
import { money, playerColor, productMeta, TONE_CLASSES } from "@/lib/format";
import { useI18n } from "@/lib/i18n";

interface ResultsPanelProps {
  results: Results | null;
  humanPlayers?: string[];
  onRematch?: () => void;
  onNewGame?: () => void;
}

const MEDALS: Record<number, string> = {
  1: "🥇",
  2: "🥈",
  3: "🥉",
};

/** How high each podium slot stands (relative bar height). */
const PODIUM_HEIGHT: Record<number, string> = {
  1: "h-32",
  2: "h-24",
  3: "h-16",
};

const PODIUM_TONE: Record<number, string> = {
  1: "from-gold/90 to-gold/40 text-deep border-gold/60 shadow-glow-gold",
  2: "from-slate-300/80 to-slate-400/30 text-white border-slate-300/50",
  3: "from-orange-400/70 to-orange-500/20 text-white border-orange-400/50",
};

export default function ResultsPanel({
  results,
  humanPlayers,
  onRematch,
  onNewGame,
}: ResultsPanelProps) {
  const { t } = useI18n();
  if (!results) {
    return (
      <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-8 text-center shadow-card">
        <p className="text-dim">{t("res.fetching")}</p>
        {(onRematch || onNewGame) && <NavButtons onRematch={onRematch} onNewGame={onNewGame} />}
      </div>
    );
  }

  const standings = [...results.standings].sort((a, b) => b.final_balance - a.final_balance);
  const winner = standings[0];
  const maxBalance = Math.max(...standings.map((s) => s.final_balance), 1);
  // Podium order: 2nd, 1st, 3rd (1st tallest in the middle); pad to 3 slots.
  const podiumOrder: (Standing | null)[] = [
    standings[1] ?? null,
    standings[0] ?? null,
    standings[2] ?? null,
  ];
  // Whose perspective is the game summary from? Prefer the first human.
  const focusName = humanPlayers?.length
    ? standings.find((s) => humanPlayers.includes(s.username))?.username
    : winner.username;
  const focus = focusName ? standings.find((s) => s.username === focusName) ?? winner : winner;
  const focusStats = focus ? results.stats?.[focus.username] : null;

  return (
    <div className="animate-fade-in-up w-full">
      {/* Winner banner */}
      <div className="relative mb-6 overflow-hidden rounded-2xl border-2 border-gold/30 bg-gradient-to-br from-card via-board to-deep p-8 text-center shadow-glow-gold">
        <div className="pointer-events-none absolute -top-10 left-1/2 -translate-x-1/2 select-none text-[10rem] leading-none text-gold/10">
          👑
        </div>
        <span className="font-display text-[11px] font-bold uppercase tracking-[0.3em] text-gold">
          {t("res.winner")}
        </span>
        <h2 className="mt-2 font-display text-4xl font-black uppercase tracking-wider text-shimmer">
          {results.winner}
        </h2>
        <p className="mt-2 text-sm text-dim">
          {t("res.finalBalance")}{" "}
          <span className="font-semibold text-buy">{money(winner.final_balance)}</span>{" "}
          ·{" "}
          <span className={winner.profit_loss >= 0 ? "text-buy" : "text-sell"}>
            {winner.profit_loss >= 0 ? "▲ +" : "▼ −"}
            {money(Math.abs(winner.profit_loss))}
          </span>{" "}
          {t("res.vsStarting", { amount: money(results.starting_balance) })}
        </p>
      </div>

      {/* Podium (top 3, with empty slot) */}
      <div className="mb-5 rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-5 shadow-card">
        <h3 className="mb-4 text-center font-display text-lg font-bold uppercase tracking-wide">
          {t("res.podium")}
        </h3>
        <div className="flex items-end justify-center gap-3">
          {podiumOrder.map((s, i) => {
            const rank = i === 0 ? 2 : i === 1 ? 1 : 3;
            const is1st = rank === 1;
            if (!s) {
              return (
                <div
                  key={`empty-${rank}`}
                  className="flex w-24 flex-col items-center gap-1.5 opacity-45 sm:w-28"
                >
                  <div className="flex flex-col items-center">
                    <span className="text-2xl grayscale">{MEDALS[rank]}</span>
                    <p className="mt-1 w-full truncate text-center text-[11px] font-black uppercase tracking-wide text-dim">
                      {t("res.noPlayer")}
                    </p>
                  </div>
                  <div className={`flex w-full flex-col items-center justify-end rounded-t-xl border border-dashed bg-board/30 px-1 pt-2 ${PODIUM_HEIGHT[rank]}`}>
                    <p className="font-display text-sm font-black text-dim/60">— FCFA</p>
                  </div>
                </div>
              );
            }
            const tone = PODIUM_TONE[rank];
            const pc = playerColor(
              Math.max(0, standings.findIndex((x) => x.username === s.username))
            );
            return (
              <div
                key={s.username}
                className={`flex w-24 flex-col items-center gap-1.5 sm:w-28 ${
                  is1st ? "scale-105" : ""
                }`}
              >
                {/* Medal + name */}
                <div className="flex flex-col items-center">
                  <span className="text-2xl">{MEDALS[rank]}</span>
                  <p
                    className={`mt-1 w-full truncate text-center text-[11px] font-black uppercase tracking-wide ${pc.text}`}
                  >
                    {s.username}
                  </p>
                </div>
                {/* Podium block */}
                <div
                  className={`flex w-full flex-col items-center justify-end rounded-t-xl border bg-gradient-to-b px-1 pt-2 ${PODIUM_HEIGHT[rank]} ${tone}`}
                >
                  <p className="font-display text-sm font-black leading-tight">
                    {money(Math.round(s.final_balance))}
                  </p>
                  <p
                    className={`text-[10px] font-bold ${
                      s.profit_loss >= 0 ? "text-buy/90" : "text-sell"
                    }`}
                  >
                    {s.profit_loss >= 0 ? "▲ +" : "▼ −"}
                    {money(Math.abs(s.profit_loss))}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Standings table + game summary */}
      <div className="mb-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Standings */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-4 shadow-card">
          <h3 className="mb-3 font-display text-base font-bold uppercase tracking-wide">
            {t("res.standings")}
          </h3>
          <table className="w-full text-left text-[11px]">
            <thead>
              <tr className="border-b border-[rgba(100,180,255,0.12)] text-[9px] uppercase tracking-wider text-dim">
                <th className="pb-1.5 pr-2">#</th>
                <th className="pb-1.5 pr-2">{t("res.playerHead")}</th>
                <th className="pb-1.5 pr-2 text-right">{t("res.finalHead")}</th>
                <th className="pb-1.5 pr-2 text-right">{t("res.changeHead")}</th>
                <th className="pb-1.5 text-right">{t("res.winsHead")}</th>
              </tr>
            </thead>
            <tbody>
              {standings.map((s) => {
                const pc = playerColor(Math.max(0, standings.findIndex((x) => x.username === s.username)));
                const st = results.stats?.[s.username];
                return (
                  <tr key={s.username} className="border-b border-[rgba(100,180,255,0.06)] last:border-0">
                    <td className="py-2 pr-2 font-display text-sm font-black text-gold">
                      {MEDALS[s.rank] ?? s.rank}
                    </td>
                    <td className="py-2 pr-2">
                      <div className="flex items-center gap-1.5">
                        <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-black ${pc.avatar}`}>
                          {s.username.slice(0, 1).toUpperCase()}
                        </span>
                        <span className="truncate font-semibold text-bright">
                          {s.username}
                        </span>
                      </div>
                      <div className="mt-0.5 flex flex-wrap gap-1">
                        {s.spoiled && s.spoiled.length > 0 ? (
                          <>
                            <span className="text-[9px] font-bold uppercase tracking-wider text-dim/70">
                              {t("res.spoiled")}
                            </span>
                            {s.spoiled.map((it) => {
                              const meta = productMeta(it.product.name);
                              return (
                                <span
                                  key={it.product.name}
                                  title={t("res.spoiledTitle")}
                                  className={`inline-flex items-center gap-1 rounded border px-1 py-0.5 text-[9px] line-through opacity-70 ${TONE_CLASSES[meta.tone]}`}
                                >
                                  {meta.icon} {it.quantity}
                                </span>
                              );
                            })}
                          </>
                        ) : (
                          <span className="text-[10px] italic text-dim">{t("res.noInventory")}</span>
                        )}
                      </div>
                    </td>
                    <td className="py-2 pr-2 text-right font-display font-bold text-bright">
                      {money(s.final_balance)}
                    </td>
                    <td className={`py-2 pr-2 text-right font-semibold ${s.profit_loss >= 0 ? "text-buy" : "text-sell"}`}>
                      {s.profit_loss >= 0 ? "▲ +" : "▼ −"}
                      {money(Math.abs(s.profit_loss))}
                    </td>
                    <td className="py-2 text-right font-display font-bold text-cyan">
                      {st ? `${st.wins}/${st.rounds_played ?? "–"}` : "–"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Game summary */}
        <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card p-4 shadow-card">
          <h3 className="mb-3 font-display text-base font-bold uppercase tracking-wide">
            {t("res.summary")}
          </h3>
          <div className="flex flex-col gap-1.5 text-[11px]">
            <SummaryRow label={t("res.roundsPlayed")} value={`${results.rounds_played ?? standings.length} / ${results.total_rounds ?? "–"}`} />
            <SummaryRow label={t("res.startingBalance")} value={money(results.starting_balance)} />
            <SummaryRow label={t("res.finalBalance")} value={money(focus.final_balance)} strong />
            <SummaryRow
              label={t("res.totalChange")}
              value={`${focus.profit_loss >= 0 ? "▲ +" : "▼ −"}${money(Math.abs(focus.profit_loss))}`}
              tone={focus.profit_loss >= 0 ? "text-buy" : "text-sell"}
            />
            <div className="my-1 border-t border-[rgba(100,180,255,0.1)]" />
            <SummaryRow
              label={t("res.bestRound")}
              value={focusStats?.best_round != null ? `${t("res.round", { round: focusStats.best_round })} · ▲ +${money(focusStats.best_gain)}` : "—"}
              tone="text-buy"
            />
            <SummaryRow
              label={t("res.worstRound")}
              value={focusStats?.worst_round != null ? `${t("res.round", { round: focusStats.worst_round })} · ▼ −${money(Math.abs(focusStats.worst_loss))}` : "—"}
              tone="text-sell"
            />
            <div className="my-1 border-t border-[rgba(100,180,255,0.1)]" />
            <div className="grid grid-cols-2 gap-2 pt-1">
              <div className="rounded-lg bg-board/50 p-2 text-center">
                <p className="text-[9px] uppercase tracking-wider text-dim">{t("res.winRate")}</p>
                <p className="font-display text-lg font-black text-gold">
                  {focusStats ? `${Math.round(focusStats.win_rate * 100)}%` : "—"}
                </p>
                <p className="text-[9px] text-dim">
                  {focusStats ? `${focusStats.wins} / ${focusStats.rounds_played}` : ""}
                </p>
              </div>
              <div className="rounded-lg bg-board/50 p-2 text-center">
                <p className="text-[9px] uppercase tracking-wider text-dim">{t("res.biggestGain")}</p>
                <p className="font-display text-lg font-black text-buy">
                  {focusStats ? `+${money(focusStats.best_gain)}` : "—"}
                </p>
                <p className="text-[9px] text-dim">
                  {focusStats?.best_round != null ? t("res.round", { round: focusStats.best_round }) : ""}
                </p>
              </div>
            </div>
            <p className="mt-2 rounded-lg border border-[rgba(100,180,255,0.08)] bg-board/40 px-2 py-1.5 text-center text-[9px] text-dim">
              {t("res.spoilNote")}
            </p>
          </div>
        </div>
      </div>

      <NavButtons onRematch={onRematch} onNewGame={onNewGame} />
    </div>
  );
}

function SummaryRow({
  label,
  value,
  tone = "text-bright",
  strong = false,
}: {
  label: string;
  value: string;
  tone?: string;
  strong?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-dim">{label}</span>
      <span className={`font-display ${strong ? "text-base font-black" : "text-xs font-bold"} ${tone}`}>
        {value}
      </span>
    </div>
  );
}

function NavButtons({
  onRematch,
  onNewGame,
}: {
  onRematch?: () => void;
  onNewGame?: () => void;
}) {
  const { t } = useI18n();
  if (!onRematch && !onNewGame) return null;
  return (
    <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
      {onRematch && (
        <button
          type="button"
          onClick={onRematch}
          className="rounded-xl bg-gold px-6 py-2.5 font-display text-sm font-bold uppercase tracking-widest text-deep shadow-glow-gold transition-all hover:brightness-110 active:scale-95"
        >
          {t("res.rematch")}
        </button>
      )}
      {onNewGame && (
        <button
          type="button"
          onClick={onNewGame}
          className="rounded-xl border border-[rgba(100,180,255,0.25)] bg-card/60 px-6 py-2.5 font-display text-sm font-bold uppercase tracking-widest text-bright transition-all hover:border-gold/40 hover:text-gold active:scale-95"
        >
          {t("res.newGame")}
        </button>
      )}
    </div>
  );
}
