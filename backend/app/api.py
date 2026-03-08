from fastapi import APIRouter
from .models import GameState, Position
from .core.environment import Environment  # Импортируем заглушку
from .core.agent import Agent            # Импортируем заглушку

router = APIRouter()

# Создаем ОДИН раз объекты нашей "игры"
env = Environment(width=20, height=15)
agent = Agent(start_x=10, start_y=7)

@router.get("/state", response_model=GameState)
async def get_current_state():
    """Отдает текущее состояние мира: позицию агента и размер поля."""
    return GameState(
        agent_position=Position(x=agent.x, y=agent.y),
        grid_size=Position(x=env.width, y=env.height)
    )

@router.post("/step", response_model=GameState)
async def make_next_step():
    """Запускает один шаг симуляции (агент двигается) и возвращает новое состояние."""
    agent.move_randomly(env.width, env.height) # Вызываем метод из заглушки
    return await get_current_state()