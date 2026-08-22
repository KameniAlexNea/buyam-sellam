import type { Metadata } from "next";
import { cookies } from "next/headers";
import { Orbitron, Chakra_Petch } from "next/font/google";
import { I18nProvider, type Locale } from "@/lib/i18n";
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

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Read the saved language from the cookie so the server-rendered HTML uses
  // the same locale as the client's first render (avoids hydration mismatch).
  const cookieStore = await cookies();
  const savedLocale = cookieStore.get("buyam.locale")?.value;
  const initialLocale: Locale = savedLocale === "fr" ? "fr" : "en";
  return (
    <html
      lang={initialLocale}
      className={`${orbitron.variable} ${chakra.variable}`}
    >
      <body className="font-body antialiased">
        <I18nProvider initialLocale={initialLocale}>{children}</I18nProvider>
      </body>
    </html>
  );
}
