from pydantic import BaseModel
from typing import List, Any, Dict, Optional

class AgentState(BaseModel):
    x: int
    y: int
    direction: str
    battery: float
    inventory: List[str]
    status: str
    current_plan: List[str]
    money: float = 0.0
    nn_thought: str = "MINING 0.0% | CHARGE 0.0%"
    camera_matrix: List[int] = [0, 0, 0, 0, 0, 0, 0, 0, 0] # Matryca pikseli 3x3 w formie płaskiej [2]
    camera_feed_type: str = "SAND"
    
class EnvironmentState(BaseModel):
    step_counter: int
    time_of_day: float
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