import random
import math
from typing import List, Dict, Any
from .environment import Environment, ChargingStation, Mineral
from .search import astar_find_path, TERRAIN_COSTS, TURN_COST

class Agent:
    
    WEATHER_MULTIPLIERS = {
        "Clear_Skies": 1.0, "Partly_Cloudy": 0.8, "Cloudy": 0.5,
        "Foggy": 0.3, "Sand_Dust_Calm": 0.2, "Sand_Dust_Storm": 0.1
    }

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.direction = "N"
        self.battery: float = 100.0
        self.inventory: List[str] =[]
        self.status: str = "IDLE"
        self.current_plan: List[str] =[]

    def turn_left(self):
        dirs =['N', 'E', 'S', 'W']
        self.direction = dirs[(dirs.index(self.direction) - 1) % 4]
        self.battery -= TURN_COST
        self.status = "TURNING"

    def turn_right(self):
        dirs =['N', 'E', 'S', 'W']
        self.direction = dirs[(dirs.index(self.direction) + 1) % 4]
        self.battery -= TURN_COST
        self.status = "TURNING"

    def move_forward(self, env: Environment):
        offsets = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}
        dx, dy = offsets[self.direction]
        nx, ny = self.x + dx, self.y + dy

        # Agent może wchodzić tylko na 0 (Piasek) i 1 (Skały)
        if env.is_within_bounds(nx, ny) and env.get_terrain_type(nx, ny) != 2:
            terrain_type = env.get_terrain_type(nx, ny)
            self.x, self.y = nx, ny
            self.battery -= TERRAIN_COSTS.get(terrain_type, 1.0)
            
            if terrain_type == 1:
                self.status = "HEAVY_DRAIN"
            else:
                self.status = "MOVING"

        self._check_death()

    def follow_plan_or_search(self, env: Environment) -> None:
        if self.status == "DEAD":
            return
            
        if not self.current_plan:
            active_minerals =[obj for obj in env.objects if obj.is_active and isinstance(obj, Mineral)]
            if active_minerals:
                target = active_minerals[0]
                plan = astar_find_path(self.x, self.y, self.direction, target.x, target.y, env)
                
                if plan:
                    self.current_plan = plan
                else:
                    self.status = "IDLE" 
                    return
            else:
                self.status = "IDLE"
                return
                
        if self.current_plan:
            action = self.current_plan.pop(0)
            if action == "TURN_LEFT":
                self.turn_left()
            elif action == "TURN_RIGHT":
                self.turn_right()
            elif action == "MOVE_FORWARD":
                self.move_forward(env)

    def interact_and_recharge(self, env: Environment) -> None:
        if self.status == "DEAD":
            return

        is_charging_at_station = False

        for obj in env.objects:
            if obj.is_active and obj.x == self.x and obj.y == self.y:
                if isinstance(obj, ChargingStation):
                    charge_needed = 100.0 - self.battery
                    if charge_needed > 0 and obj.energy_pool > 0:
                        charge_amount = min(10.0, obj.energy_pool, charge_needed)
                        self.battery += charge_amount
                        obj.energy_pool -= charge_amount
                        self.status = "CHARGING"
                        is_charging_at_station = True
                        if obj.energy_pool <= 0:
                            obj.is_active = False
                            
                elif isinstance(obj, Mineral):
                    self.inventory.append(obj.type)
                    obj.is_active = False

        solar_efficiency = self._calculate_solar_efficiency(env.time_of_day)
        weather_multiplier = self.WEATHER_MULTIPLIERS.get(env.weather, 1.0)
        solar_charge = 1.0 * solar_efficiency * weather_multiplier
        self.battery = min(100.0, self.battery + solar_charge)

        if not is_charging_at_station and self.status not in["MOVING", "HEAVY_DRAIN", "TURNING"]:
            self.status = "IDLE"

    def _calculate_solar_efficiency(self, time_of_day: int) -> float:
        if 6 <= time_of_day <= 20:
            return math.sin((time_of_day - 6) / 14.0 * math.pi)
        return 0.0

    def _check_death(self) -> None:
        if self.battery <= 0:
            self.battery = 0.0
            self.status = "DEAD"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "direction": self.direction,
            "battery": round(self.battery, 2),
            "inventory": self.inventory,
            "status": self.status,
            "current_plan": self.current_plan
        }