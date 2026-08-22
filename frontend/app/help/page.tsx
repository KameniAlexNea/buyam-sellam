import type { Metadata } from "next";
import { cookies } from "next/headers";
import HelpContent from "@/components/HelpContent";

export async function generateMetadata(): Promise<Metadata> {
  const cookieStore = await cookies();
  const fr = cookieStore.get("buyam.locale")?.value === "fr";
  return {
    title: fr ? "Comment jouer — Buyam-Sellam" : "How to Play — Buyam-Sellam",
    description: fr
      ? "Un guide structuré du jeu de trading de marché Buyam-Sellam."
      : "A structured guide to the Buyam-Sellam marketplace trading game.",
  };
}

export default function HelpPage() {
  return <HelpContent />;
}
