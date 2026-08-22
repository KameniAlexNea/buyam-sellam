"use client";

import { Fragment } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import GameHeader from "./GameHeader";

const COLOR_CLS: Record<string, string> = {
  buy: "text-buy",
  sell: "text-sell",
  gold: "text-gold",
  cyan: "text-cyan",
  dim: "text-dim",
  amber: "text-amberc",
  bright: "text-bright",
  b: "text-bright",
};

/** Renders [color:text] inline segments as colored bold text. */
function Rich({ text }: { text: string }) {
  const parts = text.split(/(\[(?:buy|sell|gold|cyan|dim|amber|bright|b):[^\]]*\])/g);
  return (
    <>
      {parts.map((p, i) => {
        const m = /^\[(buy|sell|gold|cyan|dim|amber|bright|b):(.*)\]$/.exec(p);
        if (!m) return <Fragment key={i}>{p}</Fragment>;
        return (
          <b key={i} className={COLOR_CLS[m[1]]}>
            {m[2]}
          </b>
        );
      })}
    </>
  );
}

function Section({
  icon,
  title,
  children,
}: {
  icon: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-[rgba(100,180,255,0.12)] bg-card/70 p-5">
      <h3 className="flex items-center gap-2 font-display text-sm font-bold uppercase tracking-wider text-gold">
        <span className="text-lg">{icon}</span> {title}
      </h3>
      <div className="mt-3 space-y-2 text-sm leading-relaxed text-dim">
        {children}
      </div>
    </section>
  );
}

function Bullet({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-start gap-2">
      <span className="mt-0.5 text-gold/70">▸</span>
      <span>{children}</span>
    </li>
  );
}

export default function HelpContent() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6">
      <GameHeader subtitle={t("help.subtitle")} help={false} />

      <div className="space-y-4">
        <Section icon="🎯" title={t("help.goal.title")}>
          <p>
            <Rich text={t("help.goal.body")} />
          </p>
        </Section>

        <Section icon="🎲" title={t("help.dice.title")}>
          <p>
            <Rich text={t("help.dice.body")} />
          </p>
          <ul className="space-y-1.5">
            <Bullet>
              <Rich text={t("help.dice.high")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.dice.low")} />
            </Bullet>
          </ul>
        </Section>

        <Section icon="🌐" title={t("help.markets.title")}>
          <p>
            <Rich text={t("help.markets.body")} />
          </p>
          <ul className="space-y-1.5">
            <Bullet>
              <Rich text={t("help.markets.products")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.markets.tax")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.markets.fee")} />
            </Bullet>
          </ul>
        </Section>

        <Section icon="🧠" title={t("help.strategy.title")}>
          <p>
            <Rich text={t("help.strategy.body")} />
          </p>
          <ul className="space-y-1.5">
            <Bullet>
              <Rich text={t("help.strategy.buy")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.strategy.sell")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.strategy.skip")} />
            </Bullet>
          </ul>
          <p>
            <Rich text={t("help.strategy.board")} />
          </p>
        </Section>

        <Section icon="⚡" title={t("help.action.title")}>
          <p>
            <Rich text={t("help.action.body")} />
          </p>
          <ul className="space-y-1.5">
            <Bullet>
              <Rich text={t("help.action.buy")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.action.sell")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.action.condition")} />
            </Bullet>
          </ul>
        </Section>

        <Section icon="👥" title={t("help.multi.title")}>
          <p>
            <Rich text={t("help.multi.body")} />
          </p>
        </Section>

        <Section icon="🤖" title={t("help.bots.title")}>
          <p className="mb-2">
            <Rich text={t("help.bots.body")} />
          </p>
          <ul className="space-y-1.5">
            <Bullet>
              <Rich text={t("help.bots.random")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.bots.conservative")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.bots.blsh")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.bots.aggressive")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.bots.sniper")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.bots.ev")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.bots.arb")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.bots.endgame")} />
            </Bullet>
          </ul>
        </Section>

        <Section icon="🗺️" title={t("help.board.title")}>
          <ul className="space-y-1.5">
            <Bullet>
              <Rich text={t("help.board.corners")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.board.edges")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.board.centre")} />
            </Bullet>
            <Bullet>
              <Rich text={t("help.board.badge")} />
            </Bullet>
          </ul>
        </Section>

        <Section icon="💾" title={t("help.save.title")}>
          <p>
            <Rich text={t("help.save.body")} />
          </p>
        </Section>
      </div>

      <footer className="flex justify-center pb-6">
        <Link
          href="/"
          className="rounded-xl bg-gold px-8 py-3 font-display text-sm font-black uppercase tracking-widest text-deep shadow-glow-gold transition-all hover:brightness-110 active:scale-95"
        >
          {t("help.back")}
        </Link>
      </footer>
    </div>
  );
}
