"use client";

import type { PlayerInfo, PlayerRole } from "@/lib/types";
import { money, productMeta, TONE_CLASSES } from "@/lib/format";

interface PlayerHUDProps {
  players: PlayerInfo[];
  playerRoles: Record<string, PlayerRole>;
  currentPlayer?: string | null;
  humanUsername?: string | null;
}

export default function PlayerHUD({
  players,
  playerRoles,
  currentPlayer,
  humanUsername,
}: PlayerHUDProps) {
  if (players.length === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {players.map((p) => {
        const role = playerRoles[p.username]?.role ?? "human";
        const isCurrent = p.username === currentPlayer;
        const isHuman = p.username === humanUsername;
        return (
          <div
            key={p.username}
            className={`rounded-2xl border p-4 transition-all ${
              isCurrent
                ? "border-gold/50 bg-card shadow-glow-gold ring-1 ring-gold/30"
                : "border-[rgba(100,180,255,0.12)] bg-card"
            }`}
          >
            <div className="flex items-center gap-3">
              <div
                className={`flex h-11 w-11 items-center justify-center rounded-xl font-display text-lg font-bold ${
                  isHuman
                    ? "bg-gold text-deep"
                    : "bg-gradient-to-br from-accent to-violet text-white"
                }`}
              >
                {p.username.slice(0, 1).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="truncate font-display text-sm font-bold uppercase tracking-wide">
                    {p.username}
                  </h4>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                      isHuman
                        ? "bg-gold/15 text-gold border border-gold/30"
                        : "bg-violet/15 text-violet border border-violet/30"
                    }`}
                  >
                    {isHuman ? "You" : "Bot"}
                  </span>
                </div>
                <p
                  className={`font-display text-lg font-bold ${
                    p.balance >= 0 ? "text-buy" : "text-sell"
                  }`}
                >
                  {money(p.balance)}
                </p>
              </div>
            </div>

            <div className="mt-3 flex flex-wrap gap-1.5">
              {p.inventory.length === 0 ? (
                <span className="text-xs italic text-dim">No inventory</span>
              ) : (
                p.inventory.map((it) => {
                  const meta = productMeta(it.product.name);
                  return (
                    <span
                      key={it.product.name}
                      className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[11px] ${TONE_CLASSES[meta.tone]}`}
                    >
                      {meta.icon} {it.quantity}
                    </span>
                  );
                })
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
