from fastapi import APIRouter
from .models import GameState, Position
from .core.environment import Environment  # Импортируем заглушку
from .core.agent import Agent            # Импортируем заглушку

router = APIRouter()

# Создаем ОДИН раз объекты нашей "игры"
env = Environment(width=20, height=15)
agent = Agent(x=10, y=7)

@router.get("/state", response_model=GameState)
async def get_current_state():
    """Returns the current state of the world: the agent's position and the size of the field."""
    return GameState(
        agent_position=Position(x=agent.x, y=agent.y),
        grid_size=Position(x=env.width, y=env.height)
    )

@router.post("/step", response_model=GameState)
async def make_next_step():
    """Runs one simulation step (the agent moves) and returns the new state."""
    agent.move_randomly(env) # Вызываем метод из заглушки
    return await get_current_state()