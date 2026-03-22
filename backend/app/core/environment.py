import random

# Базовый класс для всех объектов на карте (Семантический узел)
class GameObject:
    def __init__(self, obj_type: str, x: int, y: int):
        self.type = obj_type
        self.x = x
        self.y = y

# Фрейм "Минерал"
class Mineral(GameObject):
    def __init__(self, name: str, x: int, y: int):
        super().__init__(name, x, y)

# Фрейм "Зарядная станция"
class ChargingStation(GameObject):
    def __init__(self, x: int, y: int):
        super().__init__("ChargingStation", x, y)

class Environment:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        
        # Глобальный стан среды
        self.step_counter = 0
        self.is_night = False
        self.weather = "Clear"
        
        # Список всех объектов на карте
        self.objects =[]
        self._populate_grid()

    def _populate_grid(self):
        """Заполняет карту минералами и зарядными станциями в случайных координатах."""
        mineral_types = ["Titanium", "Water Ice", "Hematite"]
        
        # Добавляем 15 случайных минералов
        for _ in range(15):
            m_type = random.choice(mineral_types)
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            self.objects.append(Mineral(m_type, x, y))
            
        # Добавляем 3 зарядные станции
        for _ in range(3):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            self.objects.append(ChargingStation(x, y))

    def is_within_bounds(self, x: int, y: int) -> bool:
        """Проверяет, находятся ли координаты (x, y) в пределах сетки."""
        return 0 <= x < self.width and 0 <= y < self.height

    def update_time_and_weather(self):
        """Логика изменения времени суток и погоды (вызывается каждый шаг)"""
        self.step_counter += 1
        
        # Каждые 20 шагов меняем день на ночь и обратно
        if self.step_counter % 20 == 0:
            self.is_night = not self.is_night
            
        # Каждые 50 шагов переключаем бурю
        if self.step_counter % 50 == 0:
            self.weather = "Storm" if self.weather == "Clear" else "Clear"