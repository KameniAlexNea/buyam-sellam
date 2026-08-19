"use client";

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
  return (
    <div className="space-y-4">
      <Section icon="🎯" title="Goal">
        <p>
          Finish the game with the <b className="text-bright">highest balance</b> to win.
          Each round you roll the dice, read the markets, and trade —{" "}
          <b className="text-buy">buy low</b>, <b className="text-sell">sell high</b>, and
          don't forget the taxes and entry fees.
        </p>
      </Section>

      <Section icon="🎲" title="Dice & prices">
        <p>
          You roll two dice (2d6, total 2–12) every round. Your{" "}
          <b className="text-cyan">dice price</b> is the total × 100 FCFA, and it decides
          what you can do at each market:
        </p>
        <ul className="space-y-1.5">
          <Bullet>
            High roll → higher dice price → good for <b className="text-sell">selling</b>{" "}
            (the market pays more).
          </Bullet>
          <Bullet>
            Low roll → lower dice price → good for <b className="text-buy">buying</b>{" "}
            (you pay less).
          </Bullet>
        </ul>
      </Section>

      <Section icon="🌐" title="Markets">
        <p>
          Each round a few markets are active on the board's edges. Every market trades{" "}
          <b className="text-bright">one product</b> at a <b className="text-cyan">fixed price</b>,
          with a supply, a <b className="text-amberc">tax rate</b> and a{" "}
          <b className="text-sell">sell entry fee</b>.
        </p>
        <ul className="space-y-1.5">
          <Bullet>Products: 🍚 Cooked Rice · 🥘 Fufu · 🌽 Corn Flour · 🥜 Peanut Butter · 🐟 Smoked Fish</Bullet>
          <Bullet>
            Tax is added on buys and taken from sells — a 10% tax on a 1,000 FCFA sale costs you 100 FCFA.
          </Bullet>
          <Bullet>
            Selling in a market costs a fixed entry fee, paid no matter what happens.
          </Bullet>
        </ul>
      </Section>

      <Section icon="🧠" title="Strategy phase — plan your moves">
        <p>
          Each player, in turn, picks an action for every active market:
        </p>
        <ul className="space-y-1.5">
          <Bullet>
            <b className="text-buy">⬇ Buy</b> — plan to buy that product.
          </Bullet>
          <Bullet>
            <b className="text-sell">⬆ Sell</b> — plan to sell it (only possible if you own some).
          </Bullet>
          <Bullet>
            <b className="text-dim">— Skip</b> — do nothing there.
          </Bullet>
        </ul>
        <p>
          On the board, <b className="text-bright">tap a market space</b> to cycle
          Skip → Buy → Sell, or use the buttons in the centre. Bots finalize their own plans
          automatically.
        </p>
      </Section>

      <Section icon="⚡" title="Action phase — trades resolve">
        <p>
          Players act in <b className="text-bright">dice-roll turn order</b> (highest first).
          When it's your turn, the board's centre shows your dice and a prompt:
        </p>
        <ul className="space-y-1.5">
          <Bullet>
            <b className="text-buy">Buy</b>: if your dice price ≥ the market price, you buy at the
            market price — cheapest sell orders first, then market supply. Quantity is limited by
            your dice roll, the stock, and your balance.
          </Bullet>
          <Bullet>
            <b className="text-sell">Sell</b>: if your dice price ≤ the market price, the market
            buys your stock at <b className="text-cyan">your</b> dice price (minus tax), after the
            entry fee.
          </Bullet>
          <Bullet>If the condition isn't met, the action is skipped automatically.</Bullet>
        </ul>
      </Section>

      <Section icon="👥" title="Multi-player (hot-seat)">
        <p>
          Several humans can sit at the same table and share the screen. The{" "}
          <b className="text-gold">turn ribbon</b> above the board always shows whose turn it is:
          who has planned (✓), who's planning now (◌), and the action turn order with dice.
          AI bots fill the remaining seats and play on their own.
        </p>
      </Section>

      <Section icon="🤖" title="Bot strategies">
        <ul className="space-y-1.5">
          <Bullet>
            <b className="text-bright">BuyLowSellHigh</b> — hunts profit margins (classic arbitrage).
          </Bullet>
          <Bullet>
            <b className="text-bright">AggressiveBuyer</b> — buys everything, hoards stock.
          </Bullet>
          <Bullet>
            <b className="text-bright">ConservativeTrader</b> — only trades on very favorable conditions.
          </Bullet>
          <Bullet>
            <b className="text-bright">MarketSniper</b> — targets high-supply, low-price markets.
          </Bullet>
          <Bullet>
            <b className="text-bright">Random</b> — picks at random (baseline).
          </Bullet>
        </ul>
      </Section>

      <Section icon="🗺️" title="Reading the board">
        <ul className="space-y-1.5">
          <Bullet>
            <b className="text-bright">Corners</b> = each player's home base (token + balance).
          </Bullet>
          <Bullet>
            <b className="text-bright">Edges</b> = the active market spaces (icon, name, price).
          </Bullet>
          <Bullet>
            <b className="text-bright">Centre</b> = the dice, the message, and the controls.
          </Bullet>
          <Bullet>
            The active player gets a <b className="text-gold">PLANNING / TRADING</b> badge on their
            corner, and their token moves onto the market they're trading at.
          </Bullet>
        </ul>
      </Section>

      <Section icon="💾" title="Save & resume">
        <p>
          Your game is saved in your browser. If you leave and come back, the lobby offers{" "}
          <b className="text-bright">▶ Continue</b> for a running game (or{" "}
          <b className="text-bright">View results</b> after it ends). When it's over you can{" "}
          <b className="text-bright">♻️ Rematch</b> with the same table or start a{" "}
          <b className="text-bright">🏠 New Game</b>.
        </p>
      </Section>
    </div>
  );
}
