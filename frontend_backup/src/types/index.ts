// src/types/index.ts

export interface Position {
  x: number;
  y: number;
}

export interface EnvironmentState {
  grid_size: { width: number; height: number };
  agent_position: Position;
}