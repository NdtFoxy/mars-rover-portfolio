from pydantic import BaseModel

class Position(BaseModel):
    x: int
    y: int

class GameState(BaseModel):
    agent_position: Position
    grid_size: Position