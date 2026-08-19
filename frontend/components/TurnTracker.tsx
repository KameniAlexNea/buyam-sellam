"use client";

import { playerColor } from "@/lib/format";
import type { GameState } from "@/lib/types";

interface TurnTrackerProps {
  game: GameState;
  currentPlanner: string | null;
  humanPlayers: string[];
}

/**
 * A clear "whose turn is it" ribbon shown above the board: the active player's
 * name in their color, plus a chip per player so you always see who has
 * planned/acted and who is still to come.
 */
export default function TurnTracker({
  game,
  currentPlanner,
  humanPlayers,
}: TurnTrackerProps) {
  const colorOf = (name: string) => {
    const i = game.players.findIndex((p) => p.username === name);
    return playerColor(Math.max(0, i));
  };

  if (game.phase === "strategy") {
    const planner = currentPlanner;
    const c = planner ? colorOf(planner) : null;
    return (
      <TrackerShell>
        <div className="flex items-center gap-2">
          <span className="text-xl">🧠</span>
          {planner && c ? (
            <p className="text-sm sm:text-base">
              <span className={`font-display font-black uppercase tracking-wide ${c.text}`}>
                {planner}
              </span>{" "}
              — plan your moves
            </p>
          ) : (
            <p className="text-sm text-dim">Resolving plans…</p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {game.players.map((p) => {
            const submitted = game.strategies_submitted.includes(p.username);
            const isPlanner = p.username === planner;
            const isHuman = humanPlayers.includes(p.username);
            const pc = colorOf(p.username);
            return (
              <span
                key={p.username}
                className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-all ${
                  isPlanner
                    ? `${pc.badge} ${pc.glow} scale-105`
                    : submitted
                    ? "border-[rgba(100,180,255,0.12)] bg-board/60 text-dim"
                    : "border-[rgba(100,180,255,0.12)] bg-board/40 text-dim/70"
                }`}
              >
                <span
                  className={`flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-black ${pc.avatar}`}
                >
                  {p.username.slice(0, 1).toUpperCase()}
                </span>
                {p.username}
                {isHuman && !isPlanner && (
                  <span className="text-[9px] font-bold text-gold/80">YOU</span>
                )}
                <span className="font-bold">
                  {submitted ? "✓" : isPlanner ? "◌" : "…"}
                </span>
              </span>
            );
          })}
        </div>
      </TrackerShell>
    );
  }

  if (game.phase === "action") {
    const current = game.current_player;
    const isHuman = current ? humanPlayers.includes(current) : false;
    const c = current ? colorOf(current) : null;
    const order = game.turn_order ?? [];
    return (
      <TrackerShell>
        <div className="flex items-center gap-2">
          <span className="text-xl">⚡</span>
          {current && c ? (
            <p className="text-sm sm:text-base">
              <span className={`font-display font-black uppercase tracking-wide ${c.text}`}>
                {current}
              </span>{" "}
              {isHuman ? "— your move!" : "is trading…"}
            </p>
          ) : (
            <p className="text-sm text-dim">Resolving trades…</p>
          )}
        </div>
        {order.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            {order.map((t, i) => {
              const isCurrent = t.username === current;
              const isHuman = humanPlayers.includes(t.username);
              const pc = colorOf(t.username);
              return (
                <span
                  key={t.username}
                  className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-all ${
                    isCurrent
                      ? `${pc.badge} ${pc.glow} scale-105`
                      : "border-[rgba(100,180,255,0.12)] bg-board/40 text-dim/70"
                  }`}
                >
                  <span className="font-display font-bold">{i + 1}</span>
                  {t.username}
                  {isHuman && !isCurrent && (
                    <span className="text-[9px] font-bold text-gold/80">YOU</span>
                  )}
                  <span className="opacity-70">🎲{t.dice_total}</span>
                </span>
              );
            })}
          </div>
        )}
      </TrackerShell>
    );
  }

  return (
    <TrackerShell>
      <p className="text-sm text-dim">{game.message || "Stand by…"}</p>
    </TrackerShell>
  );
}

function TrackerShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-[rgba(100,180,255,0.14)] bg-card px-4 py-3 shadow-glow">
      {children}
    </div>
  );
}
