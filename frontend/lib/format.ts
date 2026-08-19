import type { InventoryItem } from "./types";

/** Product icon + accent tone metadata used across the UI. */
export const PRODUCT_META: Record<string, { icon: string; tone: string }> = {
  "Cooked Rice": { icon: "🍚", tone: "amber" },
  Fufu: { icon: "🥘", tone: "mint" },
  "Corn Flour": { icon: "🌽", tone: "gold" },
  "Peanut Butter": { icon: "🥜", tone: "earth" },
  "Smoked Fish": { icon: "🐟", tone: "blue" },
};

export function productMeta(name: string): { icon: string; tone: string } {
  return PRODUCT_META[name] ?? { icon: "📦", tone: "slate" };
}

/** Tone → Tailwind classes for badges. */
export const TONE_CLASSES: Record<string, string> = {
  amber: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  mint: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  gold: "bg-yellow-500/15 text-yellow-300 border-yellow-500/30",
  earth: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  blue: "bg-blue-500/15 text-blue-300 border-blue-500/30",
  slate: "bg-slate-500/15 text-slate-300 border-slate-500/30",
};

export function money(value: number): string {
  return `${Math.round(value).toLocaleString("en-US")} FCFA`;
}

export function moneyShort(value: number): string {
  const v = Math.round(value);
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(v % 1000 === 0 ? 0 : 1)}k`;
  return `${v}`;
}

export function inventorySummary(items: InventoryItem[]): string {
  if (items.length === 0) return "empty";
  return items
    .map((it) => `${productMeta(it.product.name).icon} ${it.quantity}×${it.product.name}`)
    .join(", ");
}

/**
 * Player token color palette (indexed by player position). Full literal class
 * strings so Tailwind can statically pick them up.
 */
export const PLAYER_COLORS: {
  avatar: string;
  text: string;
  ring: string;
  badge: string;
  glow: string;
}[] = [
  {
    avatar: "bg-gold text-deep",
    text: "text-gold",
    ring: "ring-gold",
    badge: "bg-gold/15 text-gold border-gold/40",
    glow: "shadow-[0_0_18px_rgba(255,204,0,0.55)]",
  },
  {
    avatar: "bg-cyan text-deep",
    text: "text-cyan",
    ring: "ring-cyan",
    badge: "bg-cyan/15 text-cyan border-cyan/40",
    glow: "shadow-[0_0_18px_rgba(0,212,255,0.55)]",
  },
  {
    avatar: "bg-violet text-white",
    text: "text-violet",
    ring: "ring-violet",
    badge: "bg-violet/15 text-violet border-violet/40",
    glow: "shadow-[0_0_18px_rgba(179,102,255,0.55)]",
  },
  {
    avatar: "bg-buy text-deep",
    text: "text-buy",
    ring: "ring-buy",
    badge: "bg-buy/15 text-buy border-buy/40",
    glow: "shadow-[0_0_18px_rgba(0,230,138,0.55)]",
  },
  {
    avatar: "bg-accent text-white",
    text: "text-accent",
    ring: "ring-accent",
    badge: "bg-accent/15 text-accent border-accent/40",
    glow: "shadow-[0_0_18px_rgba(77,148,255,0.55)]",
  },
  {
    avatar: "bg-sell text-white",
    text: "text-sell",
    ring: "ring-sell",
    badge: "bg-sell/15 text-sell border-sell/40",
    glow: "shadow-[0_0_18px_rgba(255,77,106,0.55)]",
  },
];

export function playerColor(index: number) {
  return PLAYER_COLORS[index % PLAYER_COLORS.length];
}

/** Human-readable label for a game phase. */
export const PHASE_LABELS: Record<string, string> = {
  created: "⚙️ Created",
  setup: "🛠️ Lobby",
  round_start: "🎲 Round Start",
  strategy: "🧠 Strategy",
  turn_order: "🎲 Turn Order",
  action: "⚡ Action",
  end_round: "📊 Round End",
  game_over: "🏆 Game Over",
};

export function phaseLabel(phase: string): string {
  return PHASE_LABELS[phase] ?? phase.replace(/_/g, " ").toUpperCase();
}

export const DIFFICULTY_META: Record<
  string,
  { label: string; description: string; tone: string }
> = {
  easy: {
    label: "Easy",
    description: "Generous starting cash, low taxes, calm markets.",
    tone: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  },
  medium: {
    label: "Medium",
    description: "The standard Buyam-Sellam experience.",
    tone: "bg-yellow-500/15 text-yellow-300 border-yellow-500/30",
  },
  hard: {
    label: "Hard",
    description: "Tight budget, heavy taxes, ruthless competition.",
    tone: "bg-red-500/15 text-red-300 border-red-500/30",
  },
};
