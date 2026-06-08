// src/api/client.ts
import axios from 'axios';
import type { GameState, BuyResult } from '../types/index';

// Egzemplarz axios z bazowym URL serwera FastAPI.
const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  }
});

/** GET /state -- pełny stan symulacji (agent, mapa, obiekty, sklep). */
export const fetchInitialState = async (): Promise<GameState> => {
  const response = await apiClient.get<GameState>('/state');
  return response.data;
};

/** POST /step -- jeden krok symulacji. */
export const makeStep = async (): Promise<GameState> => {
  const response = await apiClient.post<GameState>('/step');
  return response.data;
};

/** POST /step_multiple/{n} -- wykonaj n kroków na raz. */
export const makeSteps = async (count: number): Promise<GameState> => {
  const response = await apiClient.post<GameState>(`/step_multiple/${count}`);
  return response.data;
};

/** POST /restart -- restart symulacji (nowy łazik, ten sam typ mapy). */
export const restartSim = async (): Promise<GameState> => {
  const response = await apiClient.post<GameState>('/restart');
  return response.data;
};

/** POST /shop/buy/{id} -- ręczny zakup ulepszenia (pieniądze + materiały). */
export const buyUpgrade = async (upgradeId: string): Promise<BuyResult> => {
  const response = await apiClient.post<BuyResult>(`/shop/buy/${upgradeId}`);
  return response.data;
};
