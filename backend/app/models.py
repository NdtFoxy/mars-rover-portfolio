from pydantic import BaseModel
from typing import List, Any, Dict, Optional

class AgentState(BaseModel):
    x: int
    y: int
    battery: float
    inventory: List[str]
    status: str

class EnvironmentState(BaseModel):
    step_counter: int
    time_of_day: int
    weather: str

class GameObjectState(BaseModel):
    type: str
    x: int
    y: int
    is_active: bool
    energy_pool: Optional[float] = None

class GameState(BaseModel):
    agent: AgentState
    environment: EnvironmentState
    grid: List[List[int]]          # <-- Массив массивов (Песок и Горы)
    objects: List[GameObjectState]