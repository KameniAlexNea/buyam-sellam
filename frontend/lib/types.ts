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
  message: string;
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

export interface Standing {
  rank: number;
  username: string;
  final_balance: number;
  profit_loss: number;
  inventory: InventoryItem[];
}

export interface Results {
  game_id: string;
  winner: string;
  standings: Standing[];
  starting_balance: number;
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
