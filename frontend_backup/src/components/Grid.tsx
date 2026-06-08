// src/components/Grid.tsx
import type { GameState, GameObjectState } from '../types/index';

interface GridProps {
  gameState: GameState;
}

// Kolory terenu: 0 = piasek, 1 = skała, 2 = krater
const terrainColor = (t: number): string =>
  t === 0 ? '#c79a5b' : t === 1 ? '#7d7d7d' : '#241a12';

// Ikony obiektów na mapie
const OBJECT_ICONS: Record<string, string> = {
  ChargingStation: '⚡',
  ScienceBase: '🚀',
  Titanium: '🔘',
  'Water Ice': '💎',
  Hematite: '🔴',
};

const CELL = 26; // px

const gridContainerStyle: React.CSSProperties = {
  display: 'grid',
  gap: '2px',
  backgroundColor: '#1a1208',
  border: '2px solid var(--border-color)',
  borderRadius: '12px',
  padding: '10px',
  boxShadow: '0 0 30px rgba(0, 0, 0, 0.5)',
};

// Rysuje mapę Marsa: teren + obiekty + łazik
export const Grid = ({ gameState }: GridProps) => {
  const { grid, objects, agent } = gameState;
  const height = grid.length;
  const width = height > 0 ? grid[0].length : 0;

  // Indeks aktywnych obiektów po współrzędnych "x,y"
  const objMap = new Map<string, GameObjectState>();
  objects.forEach((o) => {
    if (o.is_active) objMap.set(`${o.x},${o.y}`, o);
  });

  return (
    <div
      style={{
        ...gridContainerStyle,
        gridTemplateColumns: `repeat(${width}, ${CELL}px)`,
        gridTemplateRows: `repeat(${height}, ${CELL}px)`,
      }}
    >
      {Array.from({ length: width * height }).map((_, index) => {
        const x = index % width;
        const y = Math.floor(index / width);
        const isRover = agent.x === x && agent.y === y;
        const obj = objMap.get(`${x},${y}`);

        return (
          <div
            key={index}
            title={obj ? obj.type : ''}
            style={{
              width: '100%',
              height: '100%',
              backgroundColor: terrainColor(grid[y][x]),
              borderRadius: '3px',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              fontSize: '15px',
              lineHeight: 1,
            }}
          >
            {isRover ? '🤖' : obj ? OBJECT_ICONS[obj.type] ?? '•' : ''}
          </div>
        );
      })}
    </div>
  );
};
