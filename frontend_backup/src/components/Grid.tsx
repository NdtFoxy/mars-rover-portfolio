// src/components/Grid.tsx
import type { GameState } from '../types/index';
import { Bot } from 'lucide-react';

interface GridProps {
  gameState: GameState;
}

// Стили, вынесенные в константы для чистоты кода
const gridContainerStyle: React.CSSProperties = {
  display: 'grid',
  gap: '3px',
  backgroundColor: 'var(--mars-background)',
  border: '2px solid var(--border-color)',
  borderRadius: '12px',
  padding: '10px',
  boxShadow: '0 0 30px rgba(0, 0, 0, 0.5)',
};

const cellStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
  backgroundColor: 'var(--mars-surface)',
  borderRadius: '4px',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  transition: 'background-color 0.2s ease',
};

// Компонент Grid отвечает за отрисовку поля и положения ровера
export const Grid = ({ gameState }: GridProps) => {
  const { grid_size, agent_position } = gameState;
  const totalCells = grid_size.x * grid_size.y;

  return (
    <div 
      style={{
        ...gridContainerStyle,
        gridTemplateColumns: `repeat(${grid_size.x}, 40px)`,
        gridTemplateRows: `repeat(${grid_size.y}, 40px)`,
      }}
    >
      {Array.from({ length: totalCells }).map((_, index) => {
        const x = index % grid_size.x;
        const y = Math.floor(index / grid_size.x);
        
        const isRoverHere = agent_position.x === x && agent_position.y === y;

        return (
          <div key={index} style={cellStyle}>
            {isRoverHere && <Bot color="var(--accent-secondary)" size={30} />}
          </div>
        );
      })}
    </div>
  );
};