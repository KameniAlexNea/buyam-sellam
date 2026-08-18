"use client";

import type {
  GamePhase,
  MarketAction,
  MarketInfo,
  PlayerInfo,
  PlayerRole,
} from "@/lib/types";
import PlayerToken from "./PlayerToken";
import MarketTile from "./MarketTile";

interface BoardProps {
  players: PlayerInfo[];
  playerRoles: Record<string, PlayerRole>;
  markets: MarketInfo[];
  phase: GamePhase;
  humanPlayers: string[];
  currentPlayer?: string | null;
  currentPlanner?: string | null;
  currentMarketIndex?: number | null;
  choices?: Record<number, MarketAction>;
  onMarketTap?: (index: number) => void;
  center: React.ReactNode;
}

/**
 * A Ludo-King style plus board: markets on the four edges, players' tokens in
 * the four corner home bases, and the game centre in the middle.
 */
export default function Board({
  players,
  playerRoles,
  markets,
  phase,
  humanPlayers,
  currentPlayer,
  currentPlanner,
  currentMarketIndex,
  choices,
  onMarketTap,
  center,
}: BoardProps) {
  const indexOf = (name: string) => players.findIndex((p) => p.username === name);
  const colorOf = (name: string) => Math.max(0, indexOf(name));

  const strategyPhase = phase === "strategy";

  // 4 corners: TL, TR, BL, BR (player order).
  const corners = [players[0], players[1], players[2], players[3]];

  // 4 edges: top, right, bottom, left (market order).
  const edgeMarkets = [markets[0], markets[1], markets[2], markets[3]];
  const edgeOrientations: ("horizontal" | "vertical")[] = [
    "horizontal",
    "vertical",
    "horizontal",
    "vertical",
  ];

  const homeCorner = (player: PlayerInfo | undefined, key: string) => {
    if (!player) {
      return (
        <div
          key={key}
          className="flex items-center justify-center rounded-xl border border-dashed border-[rgba(100,180,255,0.12)] bg-board/30"
        >
          <span className="text-xl text-[rgba(100,180,255,0.15)]">＋</span>
        </div>
      );
    }
    const isHuman = humanPlayers.includes(player.username);
    const isActive = player.username === currentPlayer || player.username === currentPlanner;
    return (
      <div
        key={key}
        className="flex items-center justify-center rounded-xl border border-[rgba(100,180,255,0.1)] bg-card p-2"
      >
        <PlayerToken
          username={player.username}
          balance={player.balance}
          color={colorOf(player.username)}
          active={isActive}
          isHuman={isHuman}
        />
      </div>
    );
  };

  const marketTile = (
    market: MarketInfo | undefined,
    orientation: "horizontal" | "vertical",
    key: string
  ) => {
    if (!market) {
      return (
        <MarketTile
          key={key}
          placeholder
          orientation={orientation}
        />
      );
    }
    const active = phase === "action" && market.market_index === currentMarketIndex;
    const token =
      active && currentPlayer ? { username: currentPlayer, color: colorOf(currentPlayer) } : null;
    return (
      <MarketTile
        key={key}
        market={market}
        orientation={orientation}
        badge={strategyPhase ? (choices?.[market.market_index] ?? null) : null}
        active={active}
        token={token}
        onClick={strategyPhase ? () => onMarketTap?.(market.market_index) : undefined}
        dimmed={phase === "game_over"}
      />
    );
  };

  return (
    <>
      {/* Desktop plus board */}
      <div className="hidden gap-2 lg:grid lg:grid-cols-[minmax(7rem,1fr)_minmax(0,1.6fr)_minmax(7rem,1fr)] lg:grid-rows-[minmax(7rem,auto)_minmax(0,1fr)_minmax(7rem,auto)]">
        {homeCorner(corners[0], "tl")}
        {marketTile(edgeMarkets[0], edgeOrientations[0], "top")}
        {homeCorner(corners[1], "tr")}

        {marketTile(edgeMarkets[1], edgeOrientations[1], "left")}
        <div
          className="relative flex min-h-[18rem] flex-col items-center justify-center gap-3 overflow-hidden rounded-2xl border border-[rgba(100,180,255,0.14)] bg-gradient-to-br from-board to-deep p-4 shadow-card"
          style={{
            backgroundImage:
              "radial-gradient(ellipse at 50% 0%, rgba(255,204,0,0.06), transparent 55%)",
          }}
        >
          {center}
        </div>
        {marketTile(edgeMarkets[2], edgeOrientations[2], "right")}

        {homeCorner(corners[2], "bl")}
        {marketTile(edgeMarkets[3], edgeOrientations[3], "bottom")}
        {homeCorner(corners[3], "br")}
      </div>

      {/* Mobile stack */}
      <div className="space-y-4 lg:hidden">
        <div className="flex flex-wrap items-center justify-center gap-4 rounded-2xl border border-[rgba(100,180,255,0.1)] bg-card p-3">
          {players.map((p) => (
            <PlayerToken
              key={p.username}
              username={p.username}
              balance={p.balance}
              color={colorOf(p.username)}
              active={p.username === currentPlayer || p.username === currentPlanner}
              isHuman={humanPlayers.includes(p.username)}
            />
          ))}
        </div>
        <div className="grid grid-cols-2 gap-2">
          {markets.map((m) => marketTile(m, "horizontal", `m${m.market_index}`))}
        </div>
        <div className="rounded-2xl border border-[rgba(100,180,255,0.14)] bg-gradient-to-br from-board to-deep p-4 shadow-card">
          {center}
        </div>
      </div>

      {/* Overflow players (more than 4) — bench row */}
      {players.length > 4 && (
        <div className="mt-3 flex flex-wrap items-center justify-center gap-5 rounded-2xl border border-[rgba(100,180,255,0.1)] bg-card/60 px-4 py-3">
          {players.slice(4).map((p) => (
            <PlayerToken
              key={p.username}
              username={p.username}
              balance={p.balance}
              color={colorOf(p.username)}
              active={p.username === currentPlayer || p.username === currentPlanner}
              isHuman={humanPlayers.includes(p.username)}
            />
          ))}
        </div>
      )}
    </>
  );
}
