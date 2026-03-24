import random
import math
from typing import List, Dict, Any

# Магическая ТОЧКА перед environment решает всё:
from .environment import Environment, ChargingStation, Mineral

class Agent:
    """Автономный агент (Марсоход) с физикой батареи и State Machine."""
    
    WEATHER_MULTIPLIERS = {
        "Clear_Skies": 1.0,
        "Partly_Cloudy": 0.8,
        "Cloudy": 0.5,
        "Foggy": 0.3,
        "Sand_Dust_Calm": 0.2,
        "Sand_Dust_Storm": 0.1
    }

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.battery: float = 100.0
        self.inventory: List[str] =[]
        self.status: str = "IDLE"  # Возможные: IDLE, MOVING, HEAVY_DRAIN, CHARGING, DEAD

    def move_randomly(self, env: Environment) -> None:
        """Попытка перемещения агента с учетом стоимости рельефа."""
        if self.status == "DEAD":
            return
            
        # Возможные шаги: вверх, вниз, вправо, влево
        possible_steps = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        dx, dy = random.choice(possible_steps)
        
        nx, ny = self.x + dx, self.y + dy

        # Проверяем границы карты
        if not env.is_within_bounds(nx, ny):
            return  # Уперся в край карты, остается на месте

        # Получаем тип рельефа и двигаемся
        terrain_type = env.get_terrain_type(nx, ny)
        self.x, self.y = nx, ny

        # Штрафы рельефа
        if terrain_type == 0:  # Песок
            self.battery -= 2.0
            self.status = "MOVING"
        elif terrain_type == 1:  # Гора
            self.battery -= 6.0
            self.status = "HEAVY_DRAIN"

        self._check_death()
        
    def move(self, dx: int, dy: int, env: Environment) -> None:
        """Попытка перемещения агента с учетом стоимости рельефа."""
        if self.status == "DEAD":
            return

        nx, ny = self.x + dx, self.y + dy

        if not env.is_within_bounds(nx, ny):
            return  # Уперся в границу карты, остался на месте (можно добавить статус BLOCKED)

        terrain_type = env.get_terrain_type(nx, ny)
        self.x, self.y = nx, ny

        # Штрафы рельефа
        if terrain_type == 0:  # Sand
            self.battery -= 2.0
            self.status = "MOVING"
        elif terrain_type == 1:  # Mountain
            self.battery -= 6.0
            self.status = "HEAVY_DRAIN"

        self._check_death()

    def interact_and_recharge(self, env: Environment) -> None:
        """Взаимодействие с объектами на текущей клетке и расчет солнечной зарядки."""
        if self.status == "DEAD":
            return

        is_charging_at_station = False

        # 1. Активное взаимодействие с объектами на клетке
        for obj in env.objects:
            if obj.is_active and obj.x == self.x and obj.y == self.y:
                
                # Медленная зарядка от станции
                if isinstance(obj, ChargingStation):
                    charge_needed = 100.0 - self.battery
                    if charge_needed > 0 and obj.energy_pool > 0:
                        # Забираем до 10.0 энергии за 1 шаг
                        charge_amount = min(10.0, obj.energy_pool, charge_needed)
                        self.battery += charge_amount
                        obj.energy_pool -= charge_amount
                        self.status = "CHARGING"
                        is_charging_at_station = True
                        
                        # Если станция истощена
                        if obj.energy_pool <= 0:
                            obj.is_active = False
                            
                # Сбор минералов
                elif isinstance(obj, Mineral):
                    self.inventory.append(obj.type)
                    obj.is_active = False  # Удаляем с карты (UE5 перестанет рендерить)

        # 2. Пассивная солнечная зарядка (только если живой)
        # Если агент заряжался от станции, мы всё равно позволяем солнцу немного помочь
        solar_efficiency = self._calculate_solar_efficiency(env.time_of_day)
        weather_multiplier = self.WEATHER_MULTIPLIERS.get(env.weather, 1.0)
        
        solar_charge = 1.0 * solar_efficiency * weather_multiplier
        self.battery = min(100.0, self.battery + solar_charge)

        # Если не двигался в этот ход и не заряжался на станции - меняем статус на IDLE
        if not is_charging_at_station and self.status not in ["MOVING", "HEAVY_DRAIN"]:
            self.status = "IDLE"

    def _calculate_solar_efficiency(self, time_of_day: int) -> float:
        """
        Физика солнечных панелей на основе синусоиды.
        С 06:00 до 20:00: синусоида от 0.0 до 1.0 (пик в 13:00).
        С 20:00 до 06:00: 0.0 (солнца нет).
        """
        if 6 <= time_of_day <= 20:
            # Маппинг часов (6..20) в радианы (0..PI)
            # t=6 -> sin(0)=0.0 | t=13 -> sin(pi/2)=1.0 | t=20 -> sin(pi)=0.0
            return math.sin((time_of_day - 6) / 14.0 * math.pi)
        return 0.0

    def _check_death(self) -> None:
        """Проверка на Permadeath."""
        if self.battery <= 0:
            self.battery = 0.0
            self.status = "DEAD"

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация данных агента для FastAPI JSON Response."""
        return {
            "x": self.x,
            "y": self.y,
            "battery": round(self.battery, 2),
            "inventory": self.inventory,
            "status": self.status
        }