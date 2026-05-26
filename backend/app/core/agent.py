import random
import math
import torch
import numpy as np
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
        self.inventory: List[str] = []
        self.money: float = 0.0
        self.status: str = "IDLE"
        self.current_plan: List[str] = []

    def turn_left(self):
        dirs = ['N', 'E', 'S', 'W']
        self.direction = dirs[(dirs.index(self.direction) - 1) % 4]
        self.battery -= TURN_COST
        self.status = "TURNING"

    def turn_right(self):
        dirs = ['N', 'E', 'S', 'W']
        self.direction = dirs[(dirs.index(self.direction) + 1) % 4]
        self.battery -= TURN_COST
        self.status = "TURNING"

    def move_forward(self, env: Environment):
        offsets = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}
        dx, dy = offsets[self.direction]
        nx, ny = self.x + dx, self.y + dy

        if env.is_within_bounds(nx, ny) and env.get_terrain_type(nx, ny) != 2:
            terrain_type = env.get_terrain_type(nx, ny)
            self.x, self.y = nx, ny
            self.battery -= TERRAIN_COSTS.get(terrain_type, 1.0)
            
            if terrain_type == 1:
                self.status = "HEAVY_DRAIN"
            else:
                self.status = "MOVING"

        self._check_death()

    def follow_plan_or_search(self, env: Environment, trained_nn=None, scaler=None, reverse_mapping=None) -> None:
        if self.status == "DEAD":
            return
            
        if not self.current_plan:
            target_obj = None
            
            if trained_nn is not None and scaler is not None and reverse_mapping is not None:
                decision = self.decide_next_macro_action(env, trained_nn, scaler, reverse_mapping)
            else:
                decision = "CONTINUE_MINING"
            
            if len(self.inventory) >= 8:
                decision = "GO_TO_CHARGE"
                
            # ---- INTELIGENTNE KIEROWANIE DOSTAWAMI (Wymóg: rozdzielone stacje) ----
            if decision == "GO_TO_CHARGE":
                if self.battery < 45.0:
                    active_stations = [s for s in env.objects if s.is_active and s.type == "ChargingStation"]
                    if active_stations:
                        target_obj = min(active_stations, key=lambda s: abs(self.x - s.x) + abs(self.y - s.y))
                else:
                    active_bases = [b for b in env.objects if b.is_active and b.type == "ScienceBase"]
                    if active_bases:
                        target_obj = min(active_bases, key=lambda b: abs(self.x - b.x) + abs(self.y - b.y))
                    
            elif decision == "CONTINUE_MINING":
                active_minerals = [m for m in env.objects if m.is_active and m.type in ["Titanium", "Water Ice", "Hematite"]]
                if active_minerals:
                    prices = {"Titanium": 100.0, "Water Ice": 50.0, "Hematite": 30.0}
                    # WYBÓR CELU O NAJWYŻSZEJ WYDAJNOŚCI FINANSOWEJ
                    # Minimalizujemy (Dystans + 1) / (Cena / Max_Cena), co promuje droższe materiały
                    target_obj = min(
                        active_minerals, 
                        key=lambda m: (abs(self.x - m.x) + abs(self.y - m.y) + 1) / (prices.get(m.type, 10.0) / 100.0)
                    )
            
            if target_obj:
                plan = astar_find_path(self.x, self.y, self.direction, target_obj.x, target_obj.y, env)
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

        prices = {
            "Titanium": 100.0,
            "Water Ice": 50.0,
            "Hematite": 30.0
        }

        for obj in env.objects:
            if obj.is_active and obj.x == self.x and obj.y == self.y:
                # 1. ZDAWANIE MINERAŁÓW TYLKO W BAZIE NAUKOWEJ
                if obj.type == "ScienceBase":
                    if self.inventory:
                        for sample in self.inventory:
                            self.money += prices.get(sample, 10.0)
                        self.inventory = [] 
                        self.status = "UNLOADING"
                
                # 2. ŁADOWANIE TYLKO NA STACJI ŁADOWANIA
                elif obj.type == "ChargingStation":
                    charge_needed = 100.0 - self.battery
                    if charge_needed > 0 and obj.energy_pool > 0:
                        charge_amount = min(10.0, obj.energy_pool, charge_needed)
                        self.battery += charge_amount
                        obj.energy_pool -= charge_amount
                        self.status = "CHARGING"
                        is_charging_at_station = True
                        if obj.energy_pool <= 0:
                            obj.is_active = False
                            
                # 3. ZBIERANIE MINERAŁÓW (Wyeliminowano błąd pomijania obiektów)
                elif obj.type in ["Titanium", "Water Ice", "Hematite"]:
                    if len(self.inventory) < 8:
                        self.inventory.append(obj.type)
                        obj.is_active = False

        solar_efficiency = self._calculate_solar_efficiency(env.time_of_day)
        weather_multiplier = self.WEATHER_MULTIPLIERS.get(env.weather, 1.0)
        solar_charge = 1.0 * solar_efficiency * weather_multiplier
        self.battery = min(100.0, self.battery + solar_charge)

        if not is_charging_at_station and self.status not in ["MOVING", "HEAVY_DRAIN", "TURNING", "UNLOADING"]:
            self.status = "IDLE"

    def _get_dist_to_mineral(self, env: Environment) -> float:
        """
        Oblicza efektywną odległość do minerałów, skorygowaną o ich wartość rynkową.
        Im cenniejszy minerał, tym bliższy (bardziej atrakcyjny) wydaje się sieci neuronowej.
        """
        active_minerals = [m for m in env.objects if getattr(m, 'is_active', False) and m.type in ["Titanium", "Water Ice", "Hematite"]]
        if not active_minerals:
            return 100.0
            
        prices = {
            "Titanium": 100.0,
            "Water Ice": 50.0,
            "Hematite": 30.0
        }
        
        effective_distances = []
        for m in active_minerals:
            phys_dist = abs(self.x - m.x) + abs(self.y - m.y)
            # Im droższy minerał, tym większy wskaźnik ceny (max 1.0)
            price_factor = prices.get(m.type, 10.0) / 100.0
            # Dystans efektywny maleje dla droższych materiałów
            eff_dist = (phys_dist + 1) / price_factor
            effective_distances.append(eff_dist)
            
        return min(effective_distances)

    def _get_dist_to_station(self, env: Environment) -> float:
        active_stations = [s for s in env.objects if getattr(s, 'is_active', False) and s.type == "ChargingStation"]
        if not active_stations:
            return 100.0
        return min(abs(self.x - s.x) + abs(self.y - s.y) for s in active_stations)

    def decide_next_macro_action(self, env: Environment, trained_nn, scaler, reverse_mapping: dict) -> str:
        raw_features = np.array([[
            self.battery,
            env.time_of_day,
            self._calculate_solar_efficiency(env.time_of_day),
            self.WEATHER_MULTIPLIERS.get(env.weather, 1.0),
            env.get_terrain_type(self.x, self.y),
            self._get_dist_to_mineral(env), # Przekazywanie efektywnej odległości korygowanej ceną do sieci neuronowej
            self._get_dist_to_station(env),
            len(self.inventory)
        ]])
        
        scaled_features = scaler.transform(raw_features)
        input_tensor = torch.tensor(scaled_features, dtype=torch.float32)
        
        with torch.no_grad():
            outputs = trained_nn(input_tensor)
            class_idx = torch.argmax(outputs, dim=1).item()
            
        decision = reverse_mapping.get(class_idx, "CONTINUE_MINING")
        return decision

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
            "money": round(self.money, 2),
            "status": self.status,
            "current_plan": self.current_plan
        }