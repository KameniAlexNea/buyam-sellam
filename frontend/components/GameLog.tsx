"use client";

import type { HistoryEntry } from "@/lib/types";
import { money } from "@/lib/format";

interface GameLogProps {
  history: HistoryEntry[];
}

function actionMeta(action: string): { icon: string; tone: string } {
  switch (action) {
    case "game_created":
      return { icon: "🎮", tone: "text-dim" };
    case "player_added":
      return { icon: "👤", tone: "text-accent" };
    case "game_started":
      return { icon: "🚀", tone: "text-gold" };
    case "strategy_submitted":
      return { icon: "🧠", tone: "text-violet" };
    case "bot_strategy_submitted":
      return { icon: "🤖", tone: "text-cyan" };
    case "buy":
      return { icon: "⬇", tone: "text-buy" };
    case "sell":
      return { icon: "⬆", tone: "text-sell" };
    case "round_ended":
      return { icon: "📊", tone: "text-gold" };
    default:
      return { icon: "•", tone: "text-dim" };
  }
}

function detailText(entry: HistoryEntry): string {
  const d = entry.details as Record<string, any>;
  switch (entry.action) {
    case "buy": {
      const r = (d.result ?? {}) as Record<string, any>;
      return `${d.player} bought ${d.quantity}×${r.product ?? "?"} for ${money(
        r.total_with_tax ?? 0
      )}`;
    }
    case "sell": {
      const r = (d.result ?? {}) as Record<string, any>;
      return `${d.player} sold ${d.quantity}×${r.product ?? "?"} → net ${money(
        r.net_revenue ?? 0
      )}`;
    }
    case "strategy_submitted":
    case "bot_strategy_submitted": {
      const choices = (d.choices ?? d.strategy ?? []) as unknown[];
      return `${d.username} ${d.strategy_name ? `(${d.strategy_name})` : ""} — ${choices.length} market choices`;
    }
    case "player_added":
      return `${d.username} joined`;
    case "game_started":
      return `Players: ${(d.players ?? []).join(", ")}`;
    case "round_ended":
      return `Round ${d.round} complete`;
    default:
      return "";
  }
}

export default function GameLog({ history }: GameLogProps) {
  const items = [...history].reverse();

  return (
    <div className="flex h-full flex-col rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card shadow-card">
      <div className="border-b border-[rgba(100,180,255,0.08)] px-4 py-3">
        <h3 className="font-display text-sm font-bold uppercase tracking-widest">
          📜 Event Feed
        </h3>
      </div>
      <div className="scroll-slim max-h-[26rem] flex-1 space-y-1 overflow-y-auto p-3">
        {items.length === 0 ? (
          <p className="py-6 text-center text-xs text-dim">No events yet.</p>
        ) : (
          items.map((h, i) => {
            const meta = actionMeta(h.action);
            return (
              <div
                key={`${h.timestamp}-${i}`}
                className="flex items-start gap-2.5 rounded-lg px-2 py-1.5 text-sm hover:bg-board/50"
              >
                <span className={`mt-0.5 ${meta.tone}`}>{meta.icon}</span>
                <div className="min-w-0 flex-1">
                  <p className={`truncate ${meta.tone}`}>
                    {h.action.replace(/_/g, " ")}
                  </p>
                  {detailText(h) && (
                    <p className="truncate text-xs text-dim">{detailText(h)}</p>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
