"use client";

import { useI18n, type Locale } from "@/lib/i18n";

const LOCALES: { code: Locale; label: string }[] = [
  { code: "en", label: "EN" },
  { code: "fr", label: "FR" },
];

/**
 * Minimal language switcher for the game shell. More locales are added by
 * extending lib/i18n.tsx — this component is locale-agnostic.
 */
export default function LangToggle() {
  const { locale, setLocale } = useI18n();
  return (
    <div
      role="group"
      aria-label="Language"
      className="flex items-center gap-0.5 rounded-lg border border-[rgba(100,180,255,0.2)] bg-card/60 p-0.5"
    >
      {LOCALES.map((l) => (
        <button
          key={l.code}
          type="button"
          onClick={() => setLocale(l.code)}
          aria-pressed={locale === l.code}
          className={`rounded-md px-2 py-1 text-[10px] font-black uppercase tracking-widest transition-colors ${
            locale === l.code
              ? "bg-gold text-deep"
              : "text-dim hover:text-gold"
          }`}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
