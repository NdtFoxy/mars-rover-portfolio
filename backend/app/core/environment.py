import random
from typing import List, Tuple, Dict, Any, Set

class GameObject:
    def __init__(self, obj_type: str, x: int, y: int):
        self.type = obj_type
        self.x = x
        self.y = y
        self.is_active = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "is_active": self.is_active
        }
    
class Mineral(GameObject):
    def __init__(self, name: str, x: int, y: int):
        super().__init__(name, x, y)

class ChargingStation(GameObject):
    def __init__(self, x: int, y: int):
        super().__init__("ChargingStation", x, y)
        self.energy_pool: float = 200.0

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["energy_pool"] = round(self.energy_pool, 2)
        return data

class Environment:
    WEATHER_CONDITIONS =["Clear_Skies", "Cloudy", "Partly_Cloudy", "Foggy", "Sand_Dust_Calm", "Sand_Dust_Storm"]
    WEATHER_WEIGHTS =[40, 15, 20, 10, 10, 5]

    def __init__(self, width: int = 20, height: int = 15):
        self.width = width
        self.height = height
        
        self.step_counter: int = 0
        self.time_of_day: int = 0
        self.weather: str = "Clear_Skies"
        
        self.grid: List[List[int]] =[]
        self.objects: List[GameObject] =[]
        
        self.reset()

    def reset(self) -> Tuple[int, int]:
        self.step_counter = 0
        self.time_of_day = 0
        self.weather = "Clear_Skies"
        self.objects.clear()
        
        self._generate_terrain()
        self._populate_objects()
        
        return self._get_free_sand_position()    

    def is_within_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def update_time_and_weather(self) -> None:
        """
        Обновляет внутриигровое время и погодные условия.
        Одно логическое действие (шаг) теперь равно 15 минутам (0.25 часа),
        что делает смену дня и ночи более плавной.
        """
        self.step_counter += 1
        
        # 1 шаг = 0.25 часа. Цикл дня и ночи замедлен в 4 раза.
        self.time_of_day = (self.step_counter * 0.25) % 24
        
        # Обновляем погоду каждые 8 шагов (раз в 2 игровых часа)
        if self.step_counter % 8 == 0:
            self.weather = self._get_smooth_weather_transition(self.weather)

    def _get_smooth_weather_transition(self, current_weather: str) -> str:
        """
        Рассчитывает следующее погодное состояние на основе текущего (Цепи Маркова).
        Предотвращает резкие визуальные скачки (например, 'Ясно' -> 'Буря') для Unreal Engine.
        """
        # Карта допустимых переходов: из ключа можно попасть только в значения списка
        transitions = {
            "Clear_Skies": ["Clear_Skies", "Partly_Cloudy", "Sand_Dust_Calm"],
            "Partly_Cloudy": ["Clear_Skies", "Partly_Cloudy", "Cloudy"],
            "Cloudy": ["Partly_Cloudy", "Cloudy", "Foggy"],
            "Foggy": ["Cloudy", "Foggy", "Clear_Skies"],  # Туман может рассеяться в ясное небо
            "Sand_Dust_Calm": ["Clear_Skies", "Sand_Dust_Calm", "Sand_Dust_Storm"],
            "Sand_Dust_Storm": ["Sand_Dust_Calm", "Sand_Dust_Storm"] # Буря обязана сначала стихнуть
        }

        # Вероятности (веса) для каждого перехода (сумма должна быть логичной)
        weights = {
            "Clear_Skies": [60, 30, 10],       # 60% остаться ясным, 30% облачка, 10% легкая пыль
            "Partly_Cloudy": [40, 40, 20],
            "Cloudy": [30, 50, 20],
            "Foggy": [30, 60, 10],
            "Sand_Dust_Calm": [40, 40, 20],    # 40% прояснится, 40% останется, 20% усилится до бури
            "Sand_Dust_Storm": [70, 30]        # 70% стихнуть, 30% продолжаться
        }

        possible_next_states = transitions.get(current_weather, ["Clear_Skies"])
        state_weights = weights.get(current_weather, [100])

        # Выбираем одно состояние на основе весов
        return random.choices(possible_next_states, weights=state_weights, k=1)[0]

    def get_terrain_type(self, x: int, y: int) -> int:
        return self.grid[y][x]

    def _generate_terrain(self) -> None:
        """Generuje siatkę: 0 (Piasek ~70%), 1 (Skały ~20%), 2 (Kratery ~10%)"""
        self.grid =[]
        for _ in range(self.height):
            row = [random.choices([0, 1, 2], weights=[70, 20, 10], k=1)[0] for _ in range(self.width)]
            self.grid.append(row)

    def _get_free_sand_position(self, occupied: Set[Tuple[int, int]] = None) -> Tuple[int, int]:
        """Szuka wolnego pola tylko na piasku (0)"""
        if occupied is None:
            occupied = set((obj.x, obj.y) for obj in self.objects if obj.is_active)
            
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if self.grid[y][x] == 0 and (x, y) not in occupied:
                return x, y

    def _populate_objects(self) -> None:
        mineral_names =["Titanium", "Water Ice", "Hematite"]
        occupied_positions: Set[Tuple[int, int]] = set()

        for _ in range(10):
            x, y = self._get_free_sand_position(occupied_positions)
            occupied_positions.add((x, y))
            mineral_name = random.choice(mineral_names)
            self.objects.append(Mineral(mineral_name, x, y))

        for _ in range(3):
            x, y = self._get_free_sand_position(occupied_positions)
            occupied_positions.add((x, y))
            self.objects.append(ChargingStation(x, y))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_counter": self.step_counter,
            "time_of_day": self.time_of_day,
            "weather": self.weather,
            "grid": self.grid,
            "objects":[obj.to_dict() for obj in self.objects if obj.is_active]
        }