import type { Metadata } from "next";
import Link from "next/link";
import HelpContent from "@/components/HelpContent";

export const metadata: Metadata = {
  title: "How to Play — Buyam-Sellam",
  description: "A structured guide to the Buyam-Sellam marketplace trading game.",
};

export default function HelpPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6">
      <header className="flex items-center justify-between gap-3">
        <div>
          <span className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-gold">
            Buyam-Sellam
          </span>
          <h1 className="text-shimmer mt-1 font-display text-2xl font-black uppercase tracking-wide sm:text-3xl">
            How to play
          </h1>
        </div>
        <Link
          href="/"
          className="shrink-0 rounded-lg border border-[rgba(100,180,255,0.2)] bg-card/60 px-4 py-2 text-xs font-semibold uppercase tracking-widest text-dim transition-colors hover:border-gold/40 hover:text-gold"
        >
          ← Back
        </Link>
      </header>

      <HelpContent />

      <footer className="flex justify-center pb-6">
        <Link
          href="/"
          className="rounded-xl bg-gold px-8 py-3 font-display text-sm font-black uppercase tracking-widest text-deep shadow-glow-gold transition-all hover:brightness-110 active:scale-95"
        >
          🎲 Back to the game
        </Link>
      </footer>
    </div>
  );
}
