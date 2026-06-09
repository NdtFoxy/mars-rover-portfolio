import random
from typing import List, Tuple, Dict, Any, Set
from .genetic_map import generate_optimal_map

# =====================================================================
# SPECYFIKACJA MATERIAŁÓW -- podstawa WIELOWYMIAROWEGO problemu plecakowego.
# Każdy minerał ma WARTOŚĆ ($), WAGĘ (kg) oraz OBJĘTOŚĆ (l). Plecak ma DWA
# limity: maksymalną wagę I maksymalną objętość -- trzeba zmieścić się w obu
# naraz (multidimensional knapsack). Stąd ciekawe kompromisy: lód jest lekki,
# ale objętościowy; tytan ciężki, lecz kompaktowy.
# =====================================================================
MATERIAL_SPECS: Dict[str, Dict[str, float]] = {
    "Titanium":  {"value": 100.0, "weight": 8.0, "volume": 2.0},  # ciężki, ale kompaktowy
    "Water Ice": {"value": 50.0,  "weight": 3.0, "volume": 6.0},  # lekki, ale objętościowy
    "Hematite":  {"value": 30.0,  "weight": 5.0, "volume": 4.0},  # średni w obu
}
MINERAL_TYPES: List[str] = list(MATERIAL_SPECS.keys())

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
        spec = MATERIAL_SPECS.get(name, {"value": 10.0, "weight": 1.0, "volume": 1.0})
        self.value: float = spec["value"]
        self.weight: float = spec["weight"]
        self.volume: float = spec.get("volume", 1.0)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["value"] = self.value
        data["weight"] = self.weight
        data["volume"] = self.volume
        return data

class ChargingStation(GameObject):
    def __init__(self, x: int, y: int):
        super().__init__("ChargingStation", x, y)
        self.energy_pool: float = 500.0

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["energy_pool"] = round(self.energy_pool, 2)
        return data

# ---- NOWY KLASA OBIEKTU: BAZA NAUKOWA ----
class ScienceBase(GameObject):
    """
    Dedykowana stacja na Marsie przeznaczona wyłącznie do zdawania i sprzedaży minerałów.
    Nie oferuje ładowania energii.
    """
    def __init__(self, x: int, y: int):
        super().__init__("ScienceBase", x, y)

class Environment:
    WEATHER_CONDITIONS = ["Clear_Skies", "Cloudy", "Partly_Cloudy", "Foggy", "Sand_Dust_Calm", "Sand_Dust_Storm"]
    WEATHER_WEIGHTS = [40, 15, 20, 10, 10, 5]

    # Regeneracja energii stacji ładujących na krok (na stację). Reguluje TRUDNOŚĆ:
    # 0.0 = hardcore (stacje wyczerpują się na stałe), ~1.5+ = łatwo (energia odnawialna).
    # 0.5 = energia jest deficytowa, śmierć jest realna, ale nie ma wiecznego lockoutu.
    CHARGER_REGEN: float = 0.5

    # Глобальный кэш класса для хранения сгенерированных карт определенных размеров
    _cached_grids: Dict[Tuple[int, int], List[List[int]]] = {}

    def __init__(self, width: int = 20, height: int = 15, force_new_map: bool = False):
        self.width = width
        self.height = height
        
        self.step_counter: int = 0
        self.time_of_day: int = 0
        self.weather: str = "Clear_Skies"
        
        self.grid: List[List[int]] = []
        self.objects: List[GameObject] = []
        
        self.reset(force_new_map=force_new_map)

    def reset(self, force_new_map: bool = False) -> Tuple[int, int]:
        self.step_counter = 0
        self.time_of_day = 0
        self.weather = "Clear_Skies"
        self.objects.clear()
        
        # Генерируем или загружаем из кэша карту
        if force_new_map or not self.grid:
            self._generate_terrain(force_new=force_new_map)
            
        self._populate_objects()
        
        return self._get_free_sand_position()    

    def is_within_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def update_time_and_weather(self) -> None:
        """Jeden 'tik' swiata: postep czasu, pogoda, regeneracja stacji i minerałów.
        To stad bierze sie 'trudnosc zalezna od krokow' (dzien/noc + pogoda)."""
        self.step_counter += 1
        self.time_of_day = (self.step_counter * 0.25) % 24   # 1 krok = 0.25h -> pelna doba co 96 krokow

        if self.step_counter % 8 == 0:                       # co 8 krokow losujemy nowa pogode
            self.weather = self._get_smooth_weather_transition(self.weather)

        self._regenerate_chargers()          # stacje powoli odnawiaja energie
        self._respawn_minerals_if_needed()   # dosypujemy mineraly, gdy jest ich za malo

    def _regenerate_chargers(self, cap: float = 500.0) -> None:
        # Stacje ładujące powoli odnawiają energię (regulowane przez CHARGER_REGEN).
        amount = self.CHARGER_REGEN
        if amount <= 0:
            return
        for obj in self.objects:
            if obj.type == "ChargingStation":
                obj.energy_pool = min(cap, obj.energy_pool + amount)
                if obj.energy_pool > 0:
                    obj.is_active = True

    def _respawn_minerals_if_needed(self) -> None:
        active_minerals = [obj for obj in self.objects if obj.type in ["Titanium", "Water Ice", "Hematite"] and obj.is_active]
        
        if len(active_minerals) < 5:
            needed = 10 - len(active_minerals)
            mineral_names = ["Titanium", "Water Ice", "Hematite"]
            occupied = set((obj.x, obj.y) for obj in self.objects if obj.is_active)
            
            for _ in range(needed):
                x, y = self._get_free_sand_position(occupied)
                occupied.add((x, y))
                mineral_name = random.choice(mineral_names)
                self.objects.append(Mineral(mineral_name, x, y))

    def _get_smooth_weather_transition(self, current_weather: str) -> str:
        """Pogoda jako lancuch Markowa: z biezacego stanu losujemy nastepny wg wag
        (np. z 'Clear_Skies' najczesciej zostajemy przy czystym niebie). Dzieki temu
        pogoda zmienia sie PLYNNIE, a nie skacze losowo (np. slonce -> burza -> slonce)."""
        transitions = {
            "Clear_Skies": ["Clear_Skies", "Partly_Cloudy", "Sand_Dust_Calm"],
            "Partly_Cloudy": ["Clear_Skies", "Partly_Cloudy", "Cloudy"],
            "Cloudy": ["Partly_Cloudy", "Cloudy", "Foggy"],
            "Foggy": ["Cloudy", "Foggy", "Clear_Skies"],
            "Sand_Dust_Calm": ["Clear_Skies", "Sand_Dust_Calm", "Sand_Dust_Storm"],
            "Sand_Dust_Storm": ["Sand_Dust_Calm", "Sand_Dust_Storm"]
        }

        weights = {
            "Clear_Skies": [60, 30, 10],
            "Partly_Cloudy": [40, 40, 20],
            "Cloudy": [30, 50, 20],
            "Foggy": [30, 60, 10],
            "Sand_Dust_Calm": [40, 40, 20],
            "Sand_Dust_Storm": [70, 30]
        }

        possible_next_states = transitions.get(current_weather, ["Clear_Skies"])
        state_weights = weights.get(current_weather, [100])

        return random.choices(possible_next_states, weights=state_weights, k=1)[0]

    def get_terrain_type(self, x: int, y: int) -> int:
        return self.grid[y][x]

    def _generate_terrain(self, force_new: bool = False) -> None:
        """Teren mapy generowany ALGORYTMEM GENETYCZNYM (zad. 7 -> genetic_map.py).
        Wynik jest CACHE'OWANY, by nie uruchamiac GA przy kazdym restarcie (kosztowne)."""
        key = (self.width, self.height)

        # Nowa mapa tylko gdy wymuszono LUB nie ma jej jeszcze w cache -> wtedy odpalamy GA.
        if force_new or key not in Environment._cached_grids:
            Environment._cached_grids[key] = generate_optimal_map(self.width, self.height)

        # Kopiujemy mape z cache (lista list), by przypadkiem nie nadpisac wspolnej pamieci.
        self.grid = [list(row) for row in Environment._cached_grids[key]]

    def _get_free_sand_position(self, occupied: Set[Tuple[int, int]] = None) -> Tuple[int, int]:
        if occupied is None:
            occupied = set((obj.x, obj.y) for obj in self.objects if obj.is_active)
            
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if self.grid[y][x] == 0 and (x, y) not in occupied:
                return x, y

    def _populate_objects(self) -> None:
        mineral_names = ["Titanium", "Water Ice", "Hematite"]
        occupied_positions: Set[Tuple[int, int]] = set()

        # 10 minerałów
        for _ in range(10):
            x, y = self._get_free_sand_position(occupied_positions)
            occupied_positions.add((x, y))
            mineral_name = random.choice(mineral_names)
            self.objects.append(Mineral(mineral_name, x, y))

        # 2 stacje ładowania
        for _ in range(2):
            x, y = self._get_free_sand_position(occupied_positions)
            occupied_positions.add((x, y))
            self.objects.append(ChargingStation(x, y))

        # 1 Dedykowana Baza Naukowa (ScienceBase)
        x, y = self._get_free_sand_position(occupied_positions)
        occupied_positions.add((x, y))
        self.objects.append(ScienceBase(x, y))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_counter": self.step_counter,
            "time_of_day": self.time_of_day,
            "weather": self.weather,
            "grid": self.grid,
            "objects": [obj.to_dict() for obj in self.objects if obj.is_active]
        }