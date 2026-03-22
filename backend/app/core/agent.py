import random
from .environment import Environment

class Agent:
    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y
        self.battery: float = 100.0
        self.inventory: list =[]

    def move(self, dx: int, dy: int, env: Environment) -> None:
        """Перемещение стоит батареи. Если батарея на нуле - марсоход мертв."""
        if self.battery <= 0:
            return  # Dead state

        new_x = self.x + dx
        new_y = self.y + dy

        if env.is_within_bounds(new_x, new_y):
            self.x = new_x
            self.y = new_y
            self.battery -= 2.0  # Трата энергии на движение
            self.battery = max(0.0, self.battery) # Батарея не может уйти в минус

    def move_randomly(self, env: Environment) -> None:
        if self.battery <= 0:
            return
            
        possible_steps =[(0, 1), (0, -1), (1, 0), (-1, 0)]
        dx, dy = random.choice(possible_steps)
        self.move(dx, dy, env)

    def interact_and_recharge(self, env: Environment) -> None:
        """Взаимодействие со средой и предметами (вызывается в конце каждого шага)"""
        if self.battery <= 0:
            return

        # 1. Пассивная зарядка от солнечных панелей
        if not env.is_night and env.weather == 'Clear':
            self.battery += 1.0
            self.battery = min(100.0, self.battery)

        # 2. Семантическое взаимодействие с объектами на текущей клетке
        objects_to_remove =[]
        for obj in env.objects:
            if obj.x == self.x and obj.y == self.y:
                if obj.type == "ChargingStation":
                    self.battery = 100.0
                else:
                    # Это минерал
                    self.inventory.append(obj.type)
                    objects_to_remove.append(obj)
        
        # 3. Удаляем собранные минералы с карты
        for obj in objects_to_remove:
            env.objects.remove(obj)