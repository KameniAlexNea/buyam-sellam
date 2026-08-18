"use client";

interface DiceProps {
  die1?: number | null;
  die2?: number | null;
  total?: number | null;
  label?: string;
  size?: "sm" | "md" | "lg";
  rolling?: boolean;
}

const SIZES = {
  sm: { die: "h-10 w-10 text-lg", tray: "gap-2" },
  md: { die: "h-14 w-14 text-2xl", tray: "gap-3" },
  lg: { die: "h-20 w-20 text-4xl", tray: "gap-4" },
};

function pips(n: number | null | undefined) {
  if (n == null) return "?";
  return Math.max(1, Math.min(6, n));
}

export default function Dice({
  die1,
  die2,
  total,
  label,
  size = "md",
  rolling = false,
}: DiceProps) {
  const s = SIZES[size];
  const hasRoll = die1 != null && die2 != null;
  const animationKey = `${die1}-${die2}`;

  return (
    <div className="flex items-center gap-3">
      <div className={`flex ${s.tray}`}>
        {[die1, die2].map((d, i) => (
          <div
            key={`${animationKey}-${i}`}
            className={`${s.die} flex items-center justify-center rounded-xl border-2 bg-gradient-to-br from-board to-card font-display font-bold text-gold shadow-glow ${
              hasRoll && rolling ? "animate-dice-roll" : ""
            } border-gold/30`}
            style={{ textShadow: "0 0 12px rgba(255,204,0,0.4)" }}
          >
            {pips(d)}
          </div>
        ))}
      </div>
      <div className="text-sm">
        {label && (
          <span className="block text-[11px] uppercase tracking-widest text-dim">
            {label}
          </span>
        )}
        {total != null && (
          <span className="font-display text-xl font-bold text-gold">
            {total}
          </span>
        )}
      </div>
    </div>
  );
}
