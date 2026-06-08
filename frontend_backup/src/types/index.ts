// src/types/index.ts
// Typy odzwierciedlają realny payload backendu (FastAPI /state).

export interface AgentState {
  x: number;
  y: number;
  direction: string;
  battery: number;
  max_battery: number;
  inventory: string[];
  capacity: number;          // pojemność plecaka (kg) -- limit problemu plecakowego
  current_weight: number;    // aktualna waga ładunku (kg)
  status: string;
  current_plan: string[];
  money: number;
  upgrade_levels: Record<string, number>;
  nn_thought: string;
  camera_matrix: number[];
  camera_feed_type: string;
}

export interface EnvironmentState {
  step_counter: number;
  time_of_day: number;
  weather: string;
}

export interface GameObjectState {
  type: string;
  x: number;
  y: number;
  is_active: boolean;
  energy_pool?: number | null;
  value?: number | null;     // wartość minerału ($)
  weight?: number | null;    // waga minerału (kg)
}

export interface ShopItemState {
  id: string;
  name: string;
  description: string;
  level: number;
  max_level: number;
  is_maxed: boolean;
  next_cost_money?: number | null;
  next_cost_materials?: Record<string, number> | null;
  affordable: boolean;
}

export interface GameState {
  agent: AgentState;
  environment: EnvironmentState;
  grid: number[][];          // grid[y][x]: 0=piasek, 1=skała, 2=krater
  objects: GameObjectState[];
  shop: ShopItemState[];
}

export interface BuyResult {
  success: boolean;
  message: string;
  money?: number;
  items?: ShopItemState[];
}
