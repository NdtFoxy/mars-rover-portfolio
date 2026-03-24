from fastapi import APIRouter
from .models import GameState
from .core.environment import Environment
from .core.agent import Agent

router = APIRouter()

# 1. Инициализируем среду и получаем безопасные координаты для агента
env = Environment(width=20, height=15)
start_x, start_y = env.reset()

# 2. Спавним агента на Песке
agent = Agent(x=start_x, y=start_y)

@router.get("/state", response_model=GameState)
async def get_current_state():
    """Возвращает полную Семантическую Сеть: агента, среду, карту и объекты."""
    
    # Берем готовые словари прямо из классов Саши
    env_dict = env.to_dict()
    
    return GameState(
        agent=agent.to_dict(),
        environment={
            "step_counter": env_dict["step_counter"],
            "time_of_day": env_dict["time_of_day"],
            "weather": env_dict["weather"]
        },
        grid=env_dict["grid"],
        objects=env_dict["objects"]
    )

@router.post("/step", response_model=GameState)
async def make_next_step():
    """Выполняет один логический шаг (1 час) и возвращает новый статус."""
    
    # 1. Агент пытается сделать шаг
    agent.move_randomly(env)
    
    # 2. Агент взаимодействует с минералами/станциями и солнцем
    agent.interact_and_recharge(env)
    
    # 3. Мир обновляет время (1 час) и погоду
    env.update_time_and_weather()
    
    return await get_current_state()

@router.post("/restart", response_model=GameState)
async def restart_simulation():
    """Сбрасывает всю симуляцию (Генерирует новую карту и ресурсы)"""
    global env, agent
    
    # Пересоздаем карту и получаем новые координаты
    start_x, start_y = env.reset()
    
    # Возрождаем агента
    agent = Agent(x=start_x, y=start_y)
    
    return await get_current_state()