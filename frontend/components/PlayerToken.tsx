"use client";

import { playerColor } from "@/lib/format";

interface PlayerTokenProps {
  username: string;
  balance?: number;
  color: number;
  active?: boolean;
  isHuman?: boolean;
  compact?: boolean;
  showBalance?: boolean;
}

/**
 * A compact player token (avatar + optional name/balance), used for the
 * board's home corners and for tokens standing on market tiles.
 */
export default function PlayerToken({
  username,
  balance,
  color,
  active = false,
  isHuman = false,
  compact = false,
  showBalance = true,
}: PlayerTokenProps) {
  const c = playerColor(color);

  const avatar = (
    <span
      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full font-display text-lg font-black ring-2 ring-offset-2 ring-offset-board transition-all ${
        c.avatar
      } ${active ? `${c.ring} ${c.glow}` : "ring-transparent"}`}
    >
      {username.slice(0, 1).toUpperCase()}
    </span>
  );

  if (compact) {
    return (
      <div className={`flex flex-col items-center gap-1 ${active ? "opacity-100" : "opacity-90"}`}>
        {avatar}
        <span className={`max-w-[4.5rem] truncate text-[10px] font-semibold ${active ? c.text : "text-dim"}`}>
          {username}
        </span>
        {showBalance && balance != null && (
          <span className={`font-mono text-[10px] ${balance >= 0 ? "text-buy" : "text-sell"}`}>
            {Math.round(balance).toLocaleString()}
          </span>
        )}
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col items-center gap-1 text-center ${active ? "opacity-100" : "opacity-90"}`}
    >
      <div className="relative">
        {avatar}
        {isHuman && (
          <span className="absolute -bottom-1 -right-1 rounded-full border border-gold/40 bg-deep px-1 text-[9px] font-bold text-gold">
            YOU
          </span>
        )}
      </div>
      <span className={`max-w-full truncate text-xs font-bold ${active ? c.text : "text-dim"}`}>
        {username}
      </span>
      {showBalance && balance != null && (
        <span className={`font-mono text-sm font-bold ${balance >= 0 ? "text-buy" : "text-sell"}`}>
          {Math.round(balance).toLocaleString()} FCFA
        </span>
      )}
    </div>
  );
}
