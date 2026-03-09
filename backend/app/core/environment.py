class Environment:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    def is_within_bounds(self, x: int, y: int) -> bool:
        """
        Проверяет, находятся ли координаты (x, y) в пределах сетки.
        Сетка начинается с (0, 0) и заканчивается (width-1, height-1).
        """
        return 0 <= x < self.width and 0 <= y < self.height