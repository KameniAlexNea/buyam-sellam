"use client";

import Link from "next/link";

interface HelpLinkProps {
  className?: string;
}

/** A small "Help" button that opens the how-to-play page. */
export default function HelpLink({ className }: HelpLinkProps) {
  return (
    <Link
      href="/help"
      className={`inline-flex items-center gap-1.5 rounded-lg border border-[rgba(100,180,255,0.2)] bg-card/60 px-3 py-1.5 text-xs font-semibold uppercase tracking-widest text-dim transition-colors hover:border-gold/40 hover:text-gold ${className ?? ""}`}
    >
      ❓ Help
    </Link>
  );
}
