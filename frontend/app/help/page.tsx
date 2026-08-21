import type { Metadata } from "next";
import Link from "next/link";
import HelpContent from "@/components/HelpContent";
import GameHeader from "@/components/GameHeader";

export const metadata: Metadata = {
  title: "How to Play — Buyam-Sellam",
  description: "A structured guide to the Buyam-Sellam marketplace trading game.",
};

export default function HelpPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6">
      <GameHeader subtitle="How to play" help={false} />

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
