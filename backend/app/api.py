from fastapi import APIRouter
from typing import List
from .models import GameState, AgentState, EnvironmentState, GameObjectState
from .core.environment import Environment
from .core.agent import Agent

router = APIRouter()

# Создаем ОДИН раз объекты нашей симуляции (Размер карты 20х15)
env = Environment(width=20, height=15)
agent = Agent(x=10, y=7)

@router.get("/state", response_model=GameState)
async def get_current_state():
    """Возвращает текущее состояние мира (Семантическую сеть): агента, погоду и объекты."""
    
    # 1. Собираем все объекты (минералы и базы) с карты в список для JSON
    objects_list = []
    for obj in env.objects:
        objects_list.append(GameObjectState(type=obj.type, x=obj.x, y=obj.y))

    # 2. Формируем итоговый JSON (GameState)
    return GameState(
        agent=AgentState(
            x=agent.x, 
            y=agent.y, 
            battery=agent.battery, 
            inventory=agent.inventory
        ),
        environment=EnvironmentState(
            is_night=env.is_night, 
            weather=env.weather
        ),
        objects=objects_list
    )

@router.post("/step", response_model=GameState)
async def make_next_step():
    """Выполняет один шаг симуляции и возвращает новый статус."""
    
    # 1. Агент делает шаг (и тратит батарею)
    agent.move_randomly(env)
    
    # 2. Агент взаимодействует со средой (собирает минералы, заряжается)
    agent.interact_and_recharge(env)
    
    # 3. Мир обновляет время суток и погоду
    env.update_time_and_weather()
    
    return await get_current_state()