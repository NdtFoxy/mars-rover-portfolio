// src/App.tsx
import { useEffect, useState } from 'react';
import { Grid } from './components/Grid';
// Импортируем наши НОВЫЕ функции для работы с реальным API
import { fetchInitialState, makeStep } from './api/client';
// Импортируем наш обновленный тип GameState
import type { GameState } from './types/index';

// --- Стили для UI элементов (остаются прежними) ---
const mainContainerStyle: React.CSSProperties = {
  display: 'flex', flexDirection: 'column', alignItems: 'center',
  gap: '1.5rem', padding: '2rem', animation: 'fadeIn 0.8s ease-out',
  backgroundColor: 'rgba(11, 11, 30, 0.7)',
  border: '1px solid var(--border-color)', borderRadius: '16px',
  boxShadow: '0 4px 30px rgba(0, 0, 0, 0.4)', backdropFilter: 'blur(5px)',
};
const headerStyle: React.CSSProperties = { textAlign: 'center' };
const titleStyle: React.CSSProperties = { fontSize: '2rem', textTransform: 'uppercase' };
const subtitleStyle: React.CSSProperties = { fontSize: '1rem', color: 'var(--text-secondary)', opacity: 0.8 };
const controlPanelStyle: React.CSSProperties = { display: 'flex', flexDirection: 'column', gap: '1rem', width: '100%', maxWidth: '350px', minHeight: '60px' };
const buttonStyle: React.CSSProperties = { backgroundColor: 'var(--accent-primary)', color: '#fff', border: 'none', padding: '12px', borderRadius: '8px', cursor: 'pointer', fontSize: '1rem', fontWeight: 'bold', transition: 'all 0.2s ease' };
// --- Конец стилей ---

function App() {
  // --- Состояния Компонента (State Hooks) ---
  
  // Хранит все данные о симуляции. Имя типа обновлено на GameState.
  const [gameState, setGameState] = useState<GameState | null>(null);

  // Состояние для отслеживания загрузки. Пока true, кнопка будет неактивна.
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // --- Эффекты (Effects) ---

  // Этот хук выполняется один раз при загрузке приложения
  useEffect(() => {
    console.log("Fetching initial state...");
    fetchInitialState()
      .then(data => {
        console.log("Data received:", data); // Проверим, что пришло
        setGameState(data);
      })
      .catch(err => {
        console.error("CORS or Network Error:", err);
      });
  }, []);// Пустой массив означает "выполнить один раз"

  // --- Обработчики Событий (Event Handlers) ---

  // Функция для выполнения шага по кнопке "Make Step"
  const handleStep = async () => {
    if (isLoading) return; // Если уже идет загрузка, ничего не делаем

    setIsLoading(true); // Блокируем кнопку
    
    try {
      // Вызываем нашу API-функцию, которая делает POST-запрос на /step
      const newState = await makeStep();
      // Обновляем состояние на фронтенде данными, пришедшими с бэкенда
      setGameState(newState);
    } catch (error) {
      console.error("Failed to make a step:", error);
      // Здесь можно добавить обработку ошибок, если сервер недоступен
    } finally {
      setIsLoading(false); // Разблокируем кнопку в любом случае (успех или ошибка)
    }
  };

  // --- Логика Рендера ---

  // Показываем заглушку, пока данные не загрузились с сервера
  if (!gameState) {
    return <div style={subtitleStyle}>Awaiting Signal from Mars...</div>;
  }
  
  // Исправляем названия полей с width/height на x/y в компоненте Grid
  const gridStateForComponent = {
    grid_size: {
        width: gameState.grid_size.x,
        height: gameState.grid_size.y
    },
    agent_position: gameState.agent_position
  };


  // Основной рендер компонента
  return (
    <main style={mainContainerStyle}>
      <header style={headerStyle}>
        <h1 style={titleStyle}>Mission Control</h1>
        <p style={subtitleStyle}>Mars Rover Simulation</p>
      </header>
      
      {/* Передаем в Grid данные в ожидаемом им формате */}
      <Grid gameState={gridStateForComponent} />
      
      <div style={controlPanelStyle}>
        {/* Кнопка для выполнения шага */}
        <button 
          style={{ ...buttonStyle, opacity: isLoading ? 0.6 : 1 }} // Кнопка становится прозрачной во время загрузки
          onClick={handleStep}
          disabled={isLoading} // Кнопка отключается во время загрузки
        >
          {isLoading ? 'Executing...' : 'Make Step'}
        </button>
      </div>
    </main>
  );
}

export default App;