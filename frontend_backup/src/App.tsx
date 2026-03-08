// src/App.tsx
import { useEffect, useState } from 'react';
import { Grid } from './components/Grid';
import { fetchGameState } from './api/client';
import type { EnvironmentState } from './types/index';

// --- Стили для UI элементов ---
const mainContainerStyle: React.CSSProperties = {
  display: 'flex', flexDirection: 'column', alignItems: 'center',
  gap: '1.5rem', padding: '2rem', animation: 'fadeIn 0.8s ease-out',
  backgroundColor: 'rgba(11, 11, 30, 0.7)', // Полупрозрачный фон для читаемости
  border: '1px solid var(--border-color)', borderRadius: '16px',
  boxShadow: '0 4px 30px rgba(0, 0, 0, 0.4)', backdropFilter: 'blur(5px)',
};
const headerStyle: React.CSSProperties = { textAlign: 'center' };
const titleStyle: React.CSSProperties = { fontSize: '2rem', textTransform: 'uppercase' };
const subtitleStyle: React.CSSProperties = { fontSize: '1rem', color: 'var(--text-secondary)', opacity: 0.8 };
const controlPanelStyle: React.CSSProperties = { display: 'flex', flexDirection: 'column', gap: '1rem', width: '100%', maxWidth: '350px' };
const buttonStyle: React.CSSProperties = { backgroundColor: 'var(--accent-primary)', color: '#fff', border: 'none', padding: '12px', borderRadius: '8px', cursor: 'pointer', fontSize: '1rem', fontWeight: 'bold', transition: 'transform 0.2s ease' };
const inputGroupStyle: React.CSSProperties = { display: 'flex', gap: '0.5rem', alignItems: 'center' };
const inputStyle: React.CSSProperties = { width: '100%', padding: '10px', backgroundColor: 'var(--mars-background)', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)', fontSize: '1rem', textAlign: 'center' };
const errorStyle: React.CSSProperties = { color: 'var(--error-color)', textAlign: 'center', minHeight: '24px', fontWeight: 'bold' };
// --- Конец стилей ---

function App() {
  // --- Состояния Компонента (State Hooks) ---
  
  // Хранит все данные о симуляции (размер поля, позиция агента)
  const [gameState, setGameState] = useState<EnvironmentState | null>(null);
  
  // Хранит текстовое значение из поля ввода для 'X'
  const [inputX, setInputX] = useState<string>('0');
  
  // Хранит текстовое значение из поля ввода для 'Y'
  const [inputY, setInputY] = useState<string>('0');
  
  // Хранит сообщение об ошибке, если ввод некорректен
  const [error, setError] = useState<string | null>(null);

  // --- Эффекты (Effects) ---

  // Этот хук выполняется один раз при загрузке приложения
  useEffect(() => {
    // Запрашиваем начальное состояние с "сервера" (нашей заглушки)
    fetchGameState().then(data => {
      setGameState(data);
      // Устанавливаем начальные значения в полях ввода
      setInputX(String(data.agent_position.x));
      setInputY(String(data.agent_position.y));
    });
  }, []);

  // --- Обработчики Событий (Event Handlers) ---

  // Функция для тестового хода по кнопке "NEXT STEP"
  // const handleStep = () => { /* ... логика хода останется прежней ... */ };

  // Функция для установки новой позиции ровера по координатам из полей ввода
  const handleSetPosition = () => {
    if (!gameState) return; // Защита, если состояние игры еще не загружено

    // 1. Преобразуем текст из полей ввода в целые числа
    const x = parseInt(inputX, 10);
    const y = parseInt(inputY, 10);

    // 2. Валидация (проверка) введенных данных
    if (isNaN(x) || isNaN(y)) {
      setError("Coordinates must be numbers."); // Ошибка, если введено не число
      return;
    }
    if (x < 0 || x >= gameState.grid_size.width || y < 0 || y >= gameState.grid_size.height) {
      setError("Coordinates are outside the grid."); // Ошибка, если вышли за пределы поля
      return;
    }

    // 3. Если все проверки пройдены
    setError(null); // Убираем сообщение об ошибке
    setGameState({ // Обновляем состояние игры
      ...gameState,
      agent_position: { x, y },
    });
  };

  // --- Логика Рендера ---

  // Показываем заглушку, пока данные не загрузились
  if (!gameState) {
    return <div style={subtitleStyle}>Awaiting Signal from Mars...</div>;
  }

  // Основной рендер компонента
  return (
    <main style={mainContainerStyle}>
      <header style={headerStyle}>
        <h1 style={titleStyle}>Mission Control</h1>
        <p style={subtitleStyle}>Mars Rover Position</p>
      </header>
      
      <Grid gameState={gameState} />
      
      <div style={controlPanelStyle}>
        {/* Сообщение об ошибке (отображается только если есть ошибка) */}
        <p style={errorStyle}>{error || ' '}</p>
        
        <div style={inputGroupStyle}>
          {/* Поле для ввода X */}
          <input type="number" value={inputX} style={inputStyle} onChange={(e) => { setInputX(e.target.value); setError(null); }} />
          {/* Поле для ввода Y */}
          <input type="number" value={inputY} style={inputStyle} onChange={(e) => { setInputY(e.target.value); setError(null); }} />
        </div>
        
        {/* Кнопка для применения координат */}
        <button style={buttonStyle} onClick={handleSetPosition}>
          Set Rover Position
        </button>
      </div>
    </main>
  );
}

export default App;