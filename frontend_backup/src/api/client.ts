// src/api/client.ts
import type { EnvironmentState } from '../types/index';

// В будущем здесь будет: axios.get('http://localhost:8000/api/state')
export const fetchGameState = async (): Promise<EnvironmentState> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        grid_size: { width: 10, height: 10 },
        agent_position: { x: 0, y: 0 } // Стартуем в левом верхнем углу
      });
    }, 500); // Имитация задержки сети
  });
};