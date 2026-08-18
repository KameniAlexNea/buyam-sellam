"""CSS theme for the Buyam-Sellam Gradio UI."""

CSS = """

:root {
    --bg-deep: #0b0f1e;
    --bg-board: #121a2e;
    --bg-card: #182240;
    --bg-card-hover: #1e2d52;
    --border: rgba(100, 180, 255, 0.12);
    --border-glow: rgba(100, 180, 255, 0.35);
    --text: #d4daf0;
    --text-dim: #7a89aa;
    --text-bright: #f0f4ff;

    --red: #ff4d6a;
    --red-glow: rgba(255, 77, 106, 0.3);
    --orange: #ff9f1a;
    --orange-glow: rgba(255, 159, 26, 0.3);
    --green: #00e68a;
    --green-glow: rgba(0, 230, 138, 0.3);
    --blue: #4d94ff;
    --blue-glow: rgba(77, 148, 255, 0.3);
    --purple: #b366ff;
    --purple-glow: rgba(179, 102, 255, 0.3);
    --cyan: #00d4ff;
    --cyan-glow: rgba(0, 212, 255, 0.3);
    --gold: #ffcc00;
    --gold-glow: rgba(255, 204, 0, 0.4);
    --pink: #ff66b2;

    --font-game: 'Orbitron', 'Chakra Petch', 'Segoe UI', sans-serif;
    --font-ui: 'Chakra Petch', 'Segoe UI', sans-serif;

    --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.5);
    --shadow-glow: 0 0 30px rgba(77, 148, 255, 0.12);
    --radius: 16px;
}

/* ── Base ─────────────────────────────────────────── */

.gradio-container {
    background: var(--bg-deep) !important;
    background-image:
        radial-gradient(ellipse at 15% 5%, rgba(77, 148, 255, 0.07) 0%, transparent 45%),
        radial-gradient(ellipse at 85% 90%, rgba(179, 102, 255, 0.05) 0%, transparent 45%),
        radial-gradient(ellipse at 50% 50%, rgba(0, 212, 255, 0.03) 0%, transparent 55%),
        repeating-linear-gradient(0deg, transparent, transparent 60px,
            rgba(100, 180, 255, 0.015) 60px, rgba(100, 180, 255, 0.015) 61px),
        repeating-linear-gradient(90deg, transparent, transparent 60px,
            rgba(100, 180, 255, 0.015) 60px, rgba(100, 180, 255, 0.015) 61px) !important;
    color: var(--text) !important;
    font-family: var(--font-ui) !important;
    min-height: 100vh;
}
.gradio-container *:not(button):not(input):not(select):not(textarea) {
    font-family: var(--font-ui) !important;
}

/* ── App shell ───────────────────────────────────── */

.app-shell { max-width: 1320px; margin: 0 auto; }

/* ── Hero Banner ─────────────────────────────────── */

.hero-banner {
    position: relative;
    overflow: hidden;
    padding: 44px 48px 40px;
    border: 2px solid rgba(255, 204, 0, 0.2);
    border-radius: 24px;
    background: linear-gradient(135deg, #0d1228 0%, #162044 50%, #1a1540 100%);
    text-align: center;
    box-shadow: 0 0 60px rgba(255, 204, 0, 0.08), 0 0 120px rgba(77, 148, 255, 0.05),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
}
.hero-banner::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 20% 30%, rgba(255, 204, 0, 0.1) 0%, transparent 50%),
        radial-gradient(circle at 80% 70%, rgba(77, 148, 255, 0.08) 0%, transparent 50%);
    pointer-events: none;
}
.hero-banner h1 {
    position: relative;
    margin: 12px 0 16px;
    font-family: var(--font-game) !important;
    font-size: clamp(2.4rem, 6vw, 4.5rem);
    font-weight: 900;
    line-height: 1.1;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--gold) !important;
    text-shadow: 0 0 40px rgba(255, 204, 0, 0.5), 0 0 80px rgba(255, 204, 0, 0.2),
        0 2px 0 rgba(0, 0, 0, 0.3);
}
.hero-banner p {
    position: relative;
    max-width: 520px;
    margin: 0 auto;
    color: var(--text);
    font-size: 1.05rem;
    line-height: 1.6;
    opacity: 0.85;
}

.eyebrow {
    display: inline-block;
    position: relative;
    padding: 4px 14px;
    border-radius: 8px;
    background: rgba(255, 204, 0, 0.15);
    border: 1px solid rgba(255, 204, 0, 0.25);
    color: var(--gold) !important;
    font-family: var(--font-game) !important;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
}

/* ── Panel Base ──────────────────────────────────── */

.hud-panel, .side-panel, .action-panel,
.standings-panel, .board-empty, .trade-panel {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--bg-card) !important;
    color: var(--text) !important;
    box-shadow: var(--shadow-card);
}

/* ── Setup Panel ─────────────────────────────────── */

.setup-panel {
    padding: 24px 28px;
    margin-top: 20px;
    border: 2px solid rgba(77, 148, 255, 0.2) !important;
    border-radius: var(--radius) !important;
    background: linear-gradient(135deg, var(--bg-card) 0%, #0f1a33 100%) !important;
    box-shadow: var(--shadow-card), 0 0 40px rgba(77, 148, 255, 0.06);
    position: relative;
    overflow: hidden;
}
.setup-panel::before {
    content: "GAME LOBBY";
    position: absolute;
    top: 8px;
    left: 28px;
    font-family: var(--font-game) !important;
    font-size: 0.55rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    color: var(--cyan);
    opacity: 0.6;
}
.setup-panel .form, .setup-panel .block, .setup-panel .block-body,
.setup-panel .wrap, .setup-panel .container {
    background: transparent !important;
    color: var(--text) !important;
}
.setup-panel label, .setup-panel span, .setup-panel p {
    color: var(--text) !important;
    font-weight: 600;
}
.setup-panel input, .setup-panel textarea, .setup-panel select,
.setup-panel [role="spinbutton"], .setup-panel [role="combobox"] {
    background: rgba(255, 255, 255, 0.06) !important;
    color: var(--text-bright) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
.setup-panel input:focus, .setup-panel select:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 2px var(--gold-glow) !important;
}
.setup-panel input::placeholder {
    color: var(--text-dim) !important;
}
.setup-panel input[type="range"]::-webkit-slider-thumb {
    background: var(--gold) !important;
}
.setup-panel input[type="range"]::-webkit-slider-runnable-track {
    background: rgba(251, 191, 36, 0.2) !important;
}

/* ── HUD / Status Bar ────────────────────────────── */

.hud-panel {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 18px 24px;
    margin: 18px 0;
    background: linear-gradient(90deg, var(--bg-card) 0%, rgba(0, 230, 138, 0.06) 100%) !important;
    border: 2px solid var(--green) !important;
    border-radius: var(--radius) !important;
    box-shadow: 0 0 30px var(--green-glow), var(--shadow-card);
}
.hud-panel h2 {
    margin: 2px 0 0;
    font-family: var(--font-game) !important;
    font-size: 1.3rem;
    color: var(--text-bright) !important;
    letter-spacing: 0.04em;
}
.hud-stats {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: flex-end;
}
.hud-chip {
    display: inline-flex;
    align-items: center;
    min-height: 34px;
    padding: 6px 14px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid var(--border);
    color: var(--text) !important;
    font-weight: 700;
    font-size: 0.85rem;
}
.balance-chip {
    background: rgba(16, 185, 129, 0.12) !important;
    border-color: var(--green) !important;
    color: var(--green) !important;
    font-family: var(--font-game) !important;
    font-size: 0.9rem;
}

/* ── Market Cards ────────────────────────────────── */

.market-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 18px;
}
.market-card {
    min-height: 240px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 22px;
    border: 2px solid var(--border);
    border-radius: 20px;
    background: linear-gradient(160deg, var(--bg-card) 0%, rgba(10, 18, 40, 0.9) 100%);
    color: var(--text) !important;
    box-shadow: var(--shadow-card);
    transition: transform 0.25s ease, border-color 0.25s, box-shadow 0.25s;
    position: relative;
    overflow: hidden;
}
.market-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
}
.market-card:nth-child(1)::before { background: linear-gradient(90deg, var(--cyan), var(--blue)); }
.market-card:nth-child(2)::before { background: linear-gradient(90deg, var(--orange), var(--gold)); }
.market-card:nth-child(3)::before { background: linear-gradient(90deg, var(--green), var(--cyan)); }
.market-card:nth-child(4)::before { background: linear-gradient(90deg, var(--purple), var(--pink)); }
.market-card:hover {
    transform: translateY(-4px) scale(1.01);
    border-color: var(--border-glow);
    box-shadow: var(--shadow-card), 0 0 40px rgba(100, 180, 255, 0.1);
}
.market-topline {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}
.market-number {
    display: inline-grid;
    place-items: center;
    width: 54px;
    height: 54px;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--blue), var(--cyan));
    color: #fff !important;
    font-family: var(--font-game) !important;
    font-weight: 900;
    font-size: 1.2rem;
    box-shadow: 0 0 20px var(--blue-glow);
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}
.market-name {
    color: var(--text-dim) !important;
    font-weight: 700;
    text-align: right;
    font-size: 0.9rem;
}
.product-badge {
    display: inline-flex;
    align-items: center;
    width: fit-content;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.04);
    color: var(--text) !important;
    font-weight: 700;
}
.product-icon {
    display: inline-grid;
    place-items: center;
    min-width: 30px;
    height: 28px;
    padding: 0 6px;
    border-radius: 8px;
    font-size: 0.7rem;
    font-weight: 800;
    text-transform: uppercase;
}
.product-amber .product-icon { background: rgba(245, 158, 11, 0.2); color: var(--orange) !important; }
.product-mint .product-icon { background: rgba(16, 185, 129, 0.2); color: var(--green) !important; }
.product-gold .product-icon { background: rgba(251, 191, 36, 0.2); color: var(--gold) !important; }
.product-earth .product-icon { background: rgba(180, 83, 9, 0.2); color: #d97706 !important; }
.product-blue .product-icon { background: rgba(59, 130, 246, 0.2); color: var(--blue) !important; }
.product-amber { color: var(--orange) !important; }
.product-mint { color: var(--green) !important; }
.product-gold { color: var(--gold) !important; }
.product-earth { color: #d97706 !important; }
.product-blue { color: var(--blue) !important; }

.market-economy {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}
.market-economy div, .action-stat {
    padding: 10px 12px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.04);
}
.market-economy span, .action-stat span, .supply-line {
    color: var(--text-dim) !important;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.market-economy strong, .action-stat strong {
    display: block;
    margin-top: 3px;
    color: var(--text-bright) !important;
    font-family: var(--font-game) !important;
    font-size: 1rem;
}
.supply-line {
    display: flex;
    justify-content: space-between;
    margin-top: 4px;
}
.supply-meter {
    height: 10px;
    border-radius: 999px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.06);
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3);
}
.supply-meter span {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, var(--green), var(--cyan), var(--blue));
    box-shadow: 0 0 8px var(--green-glow);
}

/* ── Side Panels ─────────────────────────────────── */

.side-panel, .action-panel, .standings-panel, .board-empty { padding: 18px; }
.side-panel h3, .action-panel h3 {
    margin: 2px 0 0;
    color: var(--text-bright) !important;
    font-family: var(--font-game) !important;
    font-size: 1rem;
    letter-spacing: 0.03em;
}
.panel-heading { margin-bottom: 14px; }

.inventory-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 10px;
}
.inventory-card {
    padding: 14px;
    border: 1px solid var(--border);
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.03);
    color: var(--text) !important;
    transition: border-color 0.2s;
}
.inventory-card:hover {
    border-color: var(--border-glow);
}
.inventory-card strong {
    display: block;
    margin-top: 8px;
    color: var(--gold) !important;
    font-family: var(--font-game) !important;
    font-size: 1.8rem;
}
.inventory-card span:last-child {
    color: var(--text-dim) !important;
    font-size: 0.8rem;
}

.opponents-panel { margin-top: 14px; }
.opponent-card {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 0;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.avatar-token {
    display: grid;
    place-items: center;
    width: 42px;
    height: 42px;
    border-radius: 12px;
    font-weight: 900;
    font-size: 0.8rem;
    color: white !important;
}
.avatar-token:nth-child(1) { background: linear-gradient(135deg, var(--red), var(--pink)); box-shadow: 0 0 12px var(--red-glow); }
.opponent-card:nth-child(1) .avatar-token { background: linear-gradient(135deg, var(--red), var(--pink)); box-shadow: 0 0 12px var(--red-glow); }
.opponent-card:nth-child(2) .avatar-token { background: linear-gradient(135deg, var(--purple), var(--blue)); box-shadow: 0 0 12px var(--purple-glow); }
.opponent-card:nth-child(3) .avatar-token { background: linear-gradient(135deg, var(--cyan), var(--green)); box-shadow: 0 0 12px var(--cyan-glow); }
.opponent-card:nth-child(4) .avatar-token { background: linear-gradient(135deg, var(--orange), var(--red)); box-shadow: 0 0 12px var(--orange-glow); }
.opponent-card:nth-child(5) .avatar-token { background: linear-gradient(135deg, var(--blue), var(--cyan)); box-shadow: 0 0 12px var(--blue-glow); }

.opponent-body strong, .opponent-body span, .opponent-body small { display: block; }
.opponent-body strong { color: var(--text-bright) !important; font-weight: 700; }
.opponent-body span { color: var(--text-dim) !important; font-size: 0.85rem; }
.opponent-body small { color: var(--text-dim) !important; font-size: 0.78rem; opacity: 0.7; }
.empty-state, .next-copy { color: var(--text-dim) !important; }

/* ── Trade Panel ─────────────────────────────────── */

.trade-panel {
    padding: 20px 24px !important;
    margin: 14px 0 !important;
    border: 2px solid var(--gold) !important;
    border-radius: var(--radius) !important;
    background: linear-gradient(90deg, var(--bg-card) 0%, rgba(255, 204, 0, 0.04) 100%) !important;
    box-shadow: 0 0 30px var(--gold-glow), var(--shadow-card) !important;
    position: relative;
}
.trade-panel::before {
    content: "TRADE DESK";
    position: absolute;
    top: -10px;
    left: 24px;
    padding: 2px 12px;
    background: var(--bg-card);
    border: 1px solid var(--gold);
    border-radius: 6px;
    font-family: var(--font-game) !important;
    font-size: 0.55rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    color: var(--gold);
}
.trade-control, .deal-control { min-width: 0 !important; }
.trade-control label, .deal-control label {
    color: var(--text-bright) !important;
    font-weight: 700 !important;
    font-size: 0.85rem;
}
.trade-control .wrap, .deal-control .wrap {
    border-radius: 12px !important;
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid var(--border) !important;
}
.trade-control input[type="radio"] + label,
.trade-control .wrap label {
    color: var(--text) !important;
    min-width: 72px;
    justify-content: center;
    border-radius: 8px;
    transition: all 0.15s;
}
.trade-control input[type="radio"]:checked + label,
.trade-control .wrap label.selected {
    background: var(--gold) !important;
    color: var(--bg-deep) !important;
    font-weight: 700;
}
.deal-control input {
    color: var(--text-bright) !important;
    background: rgba(255, 255, 255, 0.06) !important;
    border-color: var(--border) !important;
}

/* ── Buttons ─────────────────────────────────────── */

.action-button button, button.action-button {
    width: auto !important;
    min-width: 120px !important;
    max-width: 180px !important;
    justify-self: start;
    font-family: var(--font-game) !important;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border-radius: 12px !important;
    transition: all 0.2s !important;
}
button.primary, .primary button,
.gradio-container button.lg.primary {
    background: linear-gradient(135deg, var(--gold), #e8a000) !important;
    border: 2px solid var(--gold) !important;
    color: var(--bg-deep) !important;
    font-family: var(--font-game) !important;
    font-weight: 800 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    box-shadow: 0 0 24px var(--gold-glow), 0 4px 16px rgba(0, 0, 0, 0.3) !important;
    border-radius: 14px !important;
    padding: 12px 24px !important;
}
button.primary:hover, .primary button:hover,
.gradio-container button.lg.primary:hover {
    background: linear-gradient(135deg, #ffe066, var(--gold)) !important;
    box-shadow: 0 0 40px var(--gold-glow), 0 0 80px rgba(255, 204, 0, 0.15),
        0 4px 16px rgba(0, 0, 0, 0.3) !important;
    transform: translateY(-2px);
}

/* ── Action Panel (dice / deals) ─────────────────── */

.action-panel {
    display: grid;
    gap: 16px;
    padding: 20px;
    margin-bottom: 14px;
    background: linear-gradient(135deg, var(--bg-card) 0%, rgba(77, 148, 255, 0.05) 100%) !important;
    border: 2px solid var(--blue) !important;
    box-shadow: 0 0 24px var(--blue-glow), var(--shadow-card);
}
.dice-tray {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 14px;
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid var(--border);
    color: var(--text);
    width: fit-content;
}
.dice-tray span, .dice-tray strong { color: var(--text) !important; }
.dice-tray strong { color: var(--gold) !important; font-family: var(--font-game) !important; }
.die-face {
    display: grid;
    place-items: center;
    width: 46px;
    height: 46px;
    border-radius: 12px;
    background: linear-gradient(145deg, #ffffff 0%, #e0e0e0 100%);
    color: var(--bg-deep) !important;
    font-family: var(--font-game) !important;
    font-weight: 900;
    font-size: 1.2rem;
    box-shadow: 0 4px 0 rgba(0, 0, 0, 0.25),
        inset 0 2px 0 rgba(255, 255, 255, 0.6),
        0 0 12px rgba(255, 255, 255, 0.1);
}
.is-waiting { opacity: 0.5; }
.is-waiting .die-face {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-dim) !important;
    box-shadow: none;
}
.dice-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}
.dice-strip .dice-tray { padding: 8px 10px; }
.dice-strip .die-face { width: 32px; height: 32px; border-radius: 8px; font-size: 0.9rem; }
.action-body { display: grid; gap: 10px; }
.action-callout {
    padding: 14px;
    border-radius: 12px;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.25);
    color: var(--green) !important;
    font-weight: 700;
    font-size: 0.95rem;
}

/* ── Events / log ────────────────────────────────── */

.event-list { margin: 0; padding-left: 18px; color: var(--text) !important; }
.event-list li { margin: 6px 0; color: var(--text) !important; }
.error-banner {
    padding: 12px 16px;
    margin-bottom: 12px;
    border-radius: 12px;
    background: rgba(239, 68, 68, 0.1);
    color: var(--red) !important;
    font-weight: 700;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

/* ── Standings Table ─────────────────────────────── */

.standings-panel {
    background: var(--bg-card) !important;
    border: 2px solid var(--gold) !important;
    box-shadow: 0 0 30px var(--gold-glow), var(--shadow-card);
    position: relative;
    overflow: hidden;
}
.standings-panel::before {
    content: "LEADERBOARD";
    position: absolute;
    top: 10px;
    right: 20px;
    font-family: var(--font-game) !important;
    font-size: 0.55rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    color: var(--gold);
    opacity: 0.5;
}
.game-table {
    width: 100%;
    border-collapse: collapse;
    border-radius: 14px;
    background: transparent;
    color: var(--text) !important;
}
.game-table th {
    padding: 14px 12px;
    color: var(--gold) !important;
    font-family: var(--font-game) !important;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-bottom: 1px solid var(--border);
    text-align: left;
}
.game-table td {
    padding: 14px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    color: var(--text) !important;
    text-align: left;
    font-weight: 600;
}
.game-table tr:first-child td {
    color: var(--gold) !important;
    font-weight: 800;
}
.game-table tr:hover td {
    background: rgba(255, 255, 255, 0.02);
}

/* ── Timeline / Log ──────────────────────────────── */

.timeline { margin: 0; padding: 0; list-style: none; }
.timeline li {
    padding: 8px 0 8px 18px;
    border-left: 2px solid rgba(59, 130, 246, 0.3);
    color: var(--text-dim) !important;
    font-size: 0.85rem;
    transition: border-color 0.2s;
}
.timeline li:hover {
    border-left-color: var(--blue);
    color: var(--text) !important;
}

/* ── Gradio overrides ────────────────────────────── */

.control-row { align-items: end; }

.gradio-container .gr-box, .gradio-container .gr-panel {
    background: var(--bg-card) !important;
    border-color: var(--border) !important;
}
.gradio-container .label-wrap {
    color: var(--text) !important;
}
.gradio-container button.lg.primary {
    background: linear-gradient(135deg, var(--gold), #e8a000) !important;
    border: 2px solid var(--gold) !important;
    color: var(--bg-deep) !important;
    font-family: var(--font-game) !important;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    box-shadow: 0 0 24px var(--gold-glow), 0 4px 16px rgba(0, 0, 0, 0.3) !important;
    border-radius: 14px !important;
    padding: 12px 24px !important;
}
.gradio-container button.lg.primary:hover {
    box-shadow: 0 0 40px var(--gold-glow), 0 0 80px rgba(255, 204, 0, 0.15) !important;
}
.gradio-container button.lg.secondary {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 2px solid rgba(100, 180, 255, 0.2) !important;
    color: var(--text) !important;
    border-radius: 14px !important;
    font-family: var(--font-game) !important;
    font-weight: 700;
    letter-spacing: 0.06em;
}
.gradio-container button.lg.secondary:hover {
    background: rgba(255, 255, 255, 0.1) !important;
    border-color: var(--cyan) !important;
    box-shadow: 0 0 20px var(--cyan-glow) !important;
}

/* Accordion overrides */
.gradio-container .gr-accordion {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
}
.gradio-container .gr-accordion .label-wrap {
    color: var(--gold) !important;
    font-family: var(--font-game) !important;
    font-weight: 700;
    letter-spacing: 0.04em;
}

/* ── Responsive ──────────────────────────────────── */

@media (max-width: 760px) {
    .hero-banner { padding: 24px; border-radius: 14px; }
    .hero-banner h1 { font-size: 2rem; }
    .hud-panel { align-items: flex-start; flex-direction: column; }
    .hud-stats { justify-content: flex-start; }
    .market-grid { grid-template-columns: 1fr; }
    .market-economy { grid-template-columns: 1fr; }
    .action-button button, button.action-button { max-width: none !important; }
}
"""


COLOR = dict(
    body_background_fill="#0b0f1e",
    body_background_fill_dark="#0b0f1e",
    body_text_color="#d4daf0",
    body_text_color_dark="#d4daf0",
    block_background_fill="#182240",
    block_background_fill_dark="#182240",
    block_border_color="rgba(100, 180, 255, 0.12)",
    block_border_color_dark="rgba(100, 180, 255, 0.12)",
    block_label_text_color="#d4daf0",
    block_label_text_color_dark="#d4daf0",
    block_title_text_color="#ffcc00",
    block_title_text_color_dark="#ffcc00",
    input_background_fill="rgba(255, 255, 255, 0.07)",
    input_background_fill_dark="rgba(255, 255, 255, 0.07)",
    input_border_color="rgba(100, 180, 255, 0.2)",
    input_border_color_dark="rgba(100, 180, 255, 0.2)",
    input_placeholder_color="#7a89aa",
    input_placeholder_color_dark="#7a89aa",
    button_primary_background_fill="linear-gradient(135deg, #ffcc00, #e8a000)",
    button_primary_background_fill_dark="linear-gradient(135deg, #ffcc00, #e8a000)",
    button_primary_text_color="#0b0f1e",
    button_primary_text_color_dark="#0b0f1e",
    button_primary_border_color="#ffcc00",
    button_primary_border_color_dark="#ffcc00",
    button_secondary_background_fill="rgba(255, 255, 255, 0.06)",
    button_secondary_background_fill_dark="rgba(255, 255, 255, 0.06)",
    button_secondary_text_color="#d4daf0",
    button_secondary_text_color_dark="#d4daf0",
    button_secondary_border_color="rgba(100, 180, 255, 0.2)",
    button_secondary_border_color_dark="rgba(100, 180, 255, 0.2)",
    slider_color="#ffcc00",
    slider_color_dark="#ffcc00",
    accordion_text_color="#ffcc00",
    accordion_text_color_dark="#ffcc00",
    checkbox_label_text_color="#d4daf0",
    checkbox_label_text_color_dark="#d4daf0",
    checkbox_label_text_color_selected="#0b0f1e",
    checkbox_label_text_color_selected_dark="#0b0f1e",
    table_text_color="#d4daf0",
    table_text_color_dark="#d4daf0",
)
