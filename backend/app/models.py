from pydantic import BaseModel
from typing import List

class AgentState(BaseModel):
    x: int
    y: int
    direction: str
    battery: float
    inventory: List[str]
    status: str
    current_plan: List[str]

class EnvironmentState(BaseModel):
    is_night: bool
    weather: str

class GameObjectState(BaseModel):
    type: str
    x: int
    y: int

class GameState(BaseModel):
    agent: AgentState
    environment: EnvironmentState
    objects: List[GameObjectState]