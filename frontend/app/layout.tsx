import type { Metadata } from "next";
import { Orbitron, Chakra_Petch } from "next/font/google";
import "./globals.css";

const orbitron = Orbitron({
  subsets: ["latin"],
  variable: "--font-orbitron",
  display: "swap",
});

const chakra = Chakra_Petch({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-chakra",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Buyam-Sellam — Marketplace Trading Game",
  description:
    "A marketplace trading game. Roll the dice, buy low, sell high, and out-trade your rivals.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${orbitron.variable} ${chakra.variable}`}>
      <body className="font-body antialiased">{children}</body>
    </html>
  );
}
