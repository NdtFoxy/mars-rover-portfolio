# Это временная заглушка. Саша напишет тут нормальный код.
import random

class Agent:
    def __init__(self, start_x: int = 0, start_y: int = 0):
        self.x = start_x
        self.y = start_y

    def move_randomly(self, env_width, env_height):
        """Супер-простое случайное движение. Не выходит за рамки 0..width-1."""
        self.x = random.randint(0, env_width - 1)
        self.y = random.randint(0, env_height - 1)
        print(f"Агент (заглушка) переместился на ({self.x}, {self.y})")