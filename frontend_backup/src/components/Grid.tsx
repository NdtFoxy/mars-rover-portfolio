// src/components/Grid.tsx
import type { EnvironmentState } from '../types/index';
import { Bot } from 'lucide-react'; // Иконка нашего ровера

// Типизация пропсов (входных данных) для компонента
interface GridProps {
  gameState: EnvironmentState;
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
  // Извлекаем нужные данные из состояния игры
  const { grid_size, agent_position } = gameState;
  const totalCells = grid_size.width * grid_size.height;

  return (
    <div 
      style={{
        ...gridContainerStyle,
        // Динамически задаем количество колонок и рядов
        gridTemplateColumns: `repeat(${grid_size.width}, 40px)`,
        gridTemplateRows: `repeat(${grid_size.height}, 40px)`,
      }}
    >
      {/* Создаем массив нужной длины и рендерим ячейку для каждого элемента */}
      {Array.from({ length: totalCells }).map((_, index) => {
        // Высчитываем X и Y координаты для каждой ячейки по ее индексу
        const x = index % grid_size.width;
        const y = Math.floor(index / grid_size.width);
        
        // Проверяем, находится ли ровер в текущей ячейке
        const isRoverHere = agent_position.x === x && agent_position.y === y;

        return (
          <div key={index} style={cellStyle}>
            {/* Если ровер здесь - рисуем его иконку */}
            {isRoverHere && <Bot color="var(--accent-secondary)" size={30} />}
          </div>
        );
      })}
    </div>
  );
};