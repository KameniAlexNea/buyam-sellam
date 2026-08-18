"use client";

import type { PlayerInfo } from "@/lib/types";
import { money } from "@/lib/format";

interface LeaderboardProps {
  players: PlayerInfo[];
  currentPlayer?: string | null;
}

export default function Leaderboard({ players, currentPlayer }: LeaderboardProps) {
  const sorted = [...players].sort((a, b) => b.balance - a.balance);

  return (
    <div className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card shadow-card">
      <div className="border-b border-[rgba(100,180,255,0.08)] px-4 py-3">
        <h3 className="font-display text-sm font-bold uppercase tracking-widest">
          🏅 Leaderboard
        </h3>
      </div>
      <div className="space-y-1.5 p-3">
        {sorted.map((p, i) => {
          const isCurrent = p.username === currentPlayer;
          return (
            <div
              key={p.username}
              className={`flex items-center gap-3 rounded-xl border px-3 py-2 ${
                isCurrent
                  ? "border-gold/40 bg-gold/10"
                  : "border-[rgba(100,180,255,0.06)] bg-board/40"
              }`}
            >
              <span className="w-5 text-center font-display font-bold text-gold">
                {i + 1}
              </span>
              <span className="flex-1 truncate text-sm font-semibold">
                {p.username}
              </span>
              <span
                className={`font-mono text-sm font-bold ${
                  p.balance >= 0 ? "text-buy" : "text-sell"
                }`}
              >
                {money(p.balance)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
