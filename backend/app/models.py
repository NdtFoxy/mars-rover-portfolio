from pydantic import BaseModel
from typing import List, Any, Dict, Optional

class AgentState(BaseModel):
    x: int
    y: int
    direction: str
    battery: float
    max_battery: float = 100.0
    inventory: List[str]
    capacity: float = 20.0          # limit WAGI plecaka (kg)
    current_weight: float = 0.0     # aktualna waga ładunku (kg)
    volume_capacity: float = 16.0   # limit OBJĘTOŚCI plecaka (l)
    current_volume: float = 0.0     # aktualna objętość ładunku (l)
    status: str
    current_plan: List[str]
    money: float = 0.0
    upgrade_levels: Dict[str, int] = {}
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
    value: Optional[float] = None    # wartość minerału ($)
    weight: Optional[float] = None   # waga minerału (kg)
    volume: Optional[float] = None   # objętość minerału (l)

class ShopItemState(BaseModel):
    id: str
    name: str
    description: str
    level: int
    max_level: int
    is_maxed: bool
    next_cost_money: Optional[float] = None
    next_cost_materials: Optional[Dict[str, int]] = None
    affordable: bool

class GameState(BaseModel):
    agent: AgentState
    environment: EnvironmentState
    grid: List[List[int]]          # <-- Массив массивов (Песок и Горы)
    objects: List[GameObjectState]
    shop: List[ShopItemState] = []
    mission: Dict[str, Any] = {}   # aktywne zadanie (dla Unreal Engine)