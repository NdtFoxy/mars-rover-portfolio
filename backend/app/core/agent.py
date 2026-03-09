import random
from .environment import Environment  # Импортируем соседний файл в модуле core

class Agent:
    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y

    def move(self, dx: int, dy: int, env: Environment) -> None:
        """
        Пытается переместить агента на заданное смещение (dx, dy).
        Если новая позиция валидна (внутри границ мира), обновляет координаты.
        """
        new_x = self.x + dx
        new_y = self.y + dy

        # Просим "мир" проверить, можно ли туда наступить
        if env.is_within_bounds(new_x, new_y):
            self.x = new_x
            self.y = new_y

    def move_randomly(self, env: Environment) -> None:
        """
        Выбирает случайное направление и пытается сделать шаг,
        передавая объект среды в метод move.
        """
        # Возможные шаги: вверх, вниз, вправо, влево
        possible_steps =[(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        dx, dy = random.choice(possible_steps)
        self.move(dx, dy, env)