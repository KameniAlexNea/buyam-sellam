export type Difficulty = "easy" | "medium" | "hard";

export type GamePhase =
  | "created"
  | "setup"
  | "round_start"
  | "strategy"
  | "turn_order"
  | "action"
  | "end_round"
  | "game_over";

export type MarketAction = "buy" | "sell" | "skip";

export interface ProductInfo {
  name: string;
  price: number;
}

export interface InventoryItem {
  product: ProductInfo;
  quantity: number;
  avg_cost: number;
}

export interface PlayerInfo {
  username: string;
  balance: number;
  inventory: InventoryItem[];
}

export interface PlayerRole {
  role: "human" | "bot";
  strategy: string | null;
}

export interface MarketInfo {
  market_index: number;
  name: string;
  product: string;
  market_fixed_price: number;
  market_supply: number;
  tax_rate: number;
  sell_entry_fee: number;
  price_history: number[];
}

export interface TurnOrderEntry {
  username: string;
  dice_total: number;
}

export interface MoveFeedEntry {
  round: number;
  player: string;
  action: "plan" | "roll" | "buy" | "sell" | "skip" | "failed_buy" | "failed_sell";
  market?: number | null;
  product?: string;
  dice_total?: number | null;
  dice_price?: number | null;
  can_buy?: boolean;
  can_sell?: boolean;
  max_affordable?: number;
  seller_qty?: number;
  quantity?: number;
  unit_price?: number;
  total?: number;
  balance?: number;
  reason?: string;
}

export interface GameState {
  game_id: string;
  phase: GamePhase;
  round_number: number;
  total_rounds: number;
  difficulty: string;
  players: PlayerInfo[];
  player_roles: Record<string, PlayerRole>;
  markets: MarketInfo[];
  turn_order: TurnOrderEntry[] | null;
  current_player: string | null;
  current_market_index: number | null;
  strategies_submitted: string[];
  dice_total: number | null;
  dice_price: number | null;
  can_buy: boolean | null;
  can_sell: boolean | null;
  max_affordable: number | null;
  seller_qty: number | null;
  action_failed: boolean | null;
  action_fail_reason: string | null;
  move_feed: MoveFeedEntry[];
  round_recap: RoundRecap | null;
  news: NewsItem[];
  message: string;
}

export interface RoundRecapPlayer {
  username: string;
  balance: number;
  change: number;
  role: string;
}

export interface RoundRecap {
  round: number;
  players: RoundRecapPlayer[];
  news: NewsItem[];
  is_last: boolean;
}

export interface NewsItem {
  product: string | null;
  market: string | null;
  pct: number;
  tone: "up" | "down" | "flat";
  text: string;
}

export interface ActionResult {
  success: boolean;
  action: string;
  details: Record<string, unknown>;
  next_state: GameState | null;
  message: string;
}

export interface StrategyInfo {
  name: string;
  label: string;
  description: string;
}

export interface DifficultyInfo {
  label: string;
  description: string;
  starting_balance: number;
  /** Strategies allowed at this level (the bot roster pool). */
  bot_pool: StrategyInfo[];
  /** True when the user cannot change bot strategies (Easy = fixed roster). */
  bot_pool_locked: boolean;
}

export type Difficulties = Record<Difficulty, DifficultyInfo>;

export interface Standing {
  rank: number;
  username: string;
  final_balance: number;
  profit_loss: number;
  inventory: InventoryItem[];
  /** Unsold stock at the end of the game — spoiled, worth nothing. */
  spoiled?: InventoryItem[];
}

export interface PlayerRoundStats {
  rounds_played: number;
  wins: number;
  win_rate: number;
  best_round: number | null;
  best_gain: number;
  worst_round: number | null;
  worst_loss: number;
}

export interface Results {
  game_id: string;
  winner: string;
  standings: Standing[];
  starting_balance: number;
  total_rounds?: number;
  rounds_played?: number;
  stats?: Record<string, PlayerRoundStats>;
}

export interface HistoryEntry {
  timestamp: string;
  action: string;
  details: Record<string, unknown>;
}

export interface History {
  game_id: string;
  history: HistoryEntry[];
}
