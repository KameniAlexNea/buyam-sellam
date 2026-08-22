"use client";

import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import HelpLink from "./HelpLink";
import LangToggle from "./LangToggle";

interface GameHeaderProps {
  /** Left-side badge(s), e.g. Round / difficulty / phase. Shown next to the back link. */
  badges?: React.ReactNode;
  /** Optional right-side trailing controls (e.g. the Log toggle). */
  actions?: React.ReactNode;
  /** Show the ← Lobby back link (default true). */
  back?: boolean;
  /** Show the ❓ Help link (default true; hide on the help page itself). */
  help?: boolean;
  /** Small subtitle under the title (e.g. the phase). */
  subtitle?: string;
}

/**
 * A game-style header: back link on the left, the game title centered and
 * prominent, and status badges + controls on the right. Used across pages so
 * the whole app feels like one game shell.
 */
export default function GameHeader({
  badges,
  actions,
  back = true,
  help = true,
  subtitle,
}: GameHeaderProps) {
  const { t } = useI18n();
  return (
    <header className="relative flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[rgba(100,180,255,0.14)] bg-gradient-to-r from-card via-board to-card px-4 py-3 shadow-card">
      {/* Left: back */}
      <div className="flex min-w-0 items-center gap-2">
        {back && (
          <Link
            href="/"
            className="rounded-lg border border-[rgba(100,180,255,0.2)] bg-card/60 px-3 py-1.5 text-xs font-semibold uppercase tracking-widest text-dim transition-colors hover:border-gold/40 hover:text-gold"
          >
            {t("back.lobby")}
          </Link>
        )}
        {badges && <div className="flex min-w-0 flex-wrap items-center gap-2">{badges}</div>}
      </div>

      {/* Center: title */}
      <div className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
        <span className="font-display text-lg font-black uppercase tracking-[0.25em] text-shimmer sm:text-xl">
          Buyam-Sellam
        </span>
        {subtitle && (
          <span className="block text-[9px] font-bold uppercase tracking-[0.4em] text-gold/70">
            {subtitle}
          </span>
        )}
      </div>

      {/* Right: controls */}
      <div className="flex items-center gap-2">
        {actions}
        <LangToggle />
        {help && <HelpLink />}
      </div>
    </header>
  );
}
