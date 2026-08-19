/**
 * 2d6 probability helpers.
 *
 * dice_price = roll_total × 100 FCFA (rolls 2–12).
 *   Buy  succeeds when dice_price ≥ market_price  →  roll ≥ ceil(price / 100)
 *   Sell succeeds when dice_price ≤ market_price  →  roll ≤ floor(price / 100)
 */

/** P(roll >= x) for 2d6 (out of 36). */
const AT_LEAST: Record<number, number> = {
  2: 36 / 36,
  3: 35 / 36,
  4: 33 / 36,
  5: 30 / 36,
  6: 26 / 36,
  7: 21 / 36,
  8: 15 / 36,
  9: 10 / 36,
  10: 6 / 36,
  11: 3 / 36,
  12: 1 / 36,
  13: 0,
};

export function probAtLeast(roll: number): number {
  const r = Math.max(2, Math.min(13, Math.ceil(roll)));
  return AT_LEAST[r] ?? 0;
}

export function probAtMost(roll: number): number {
  return 1 - probAtLeast(roll + 1);
}

export function probLabel(p: number): string {
  return `${Math.round(p * 100)}%`;
}

/** Smallest roll such that dice_price >= market price (buy condition). */
export function rollForBuy(marketPrice: number): number {
  return Math.ceil(marketPrice / 100);
}

/** Largest roll such that dice_price <= market price (sell condition). */
export function rollForSell(marketPrice: number): number {
  return Math.floor(marketPrice / 100);
}
