// src/api/client.ts
import axios from 'axios';
import type { GameState } from '../types/index';

// Создаем "экземпляр" axios с базовым URL твоего сервера.
// Это удобно, чтобы не писать 'http://localhost:8000' каждый раз.
// Убедись, что порт 8000 совпадает с тем, на котором запущен твой backend.
const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  }
});

/**
 * Функция для получения начального состояния симуляции.
 * Отправляет GET-запрос на эндпоинт /state.
 * @returns Promise, который разрешается с объектом GameState.
 */
export const fetchInitialState = async (): Promise<GameState> => {
  // Отправляем GET-запрос и ждем ответ
  const response = await apiClient.get<GameState>('/state');
  // Возвращаем данные из ответа
  return response.data;
};

/**
 * Функция для выполнения одного шага симуляции.
 * Отправляет POST-запрос на эндпоинт /step.
 * @returns Promise, который разрешается с НОВЫМ объектом GameState после хода.
 */
export const makeStep = async (): Promise<GameState> => {
  // Отправляем POST-запрос и ждем ответ
  const response = await apiClient.post<GameState>('/step');
  // Возвращаем обновленные данные из ответа
  return response.data;
};