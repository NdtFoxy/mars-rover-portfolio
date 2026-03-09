// src/types/index.ts

// Описывает объект с координатами X и Y
export interface Position {
  x: number;
  y: number;
}

// Описывает объект с размерами по X и Y
export interface Size {
  x: number;
  y: number;
}

// Описывает полный объект состояния, который мы получаем от сервера
export interface GameState {
  agent_position: Position;
  grid_size: Size;
}