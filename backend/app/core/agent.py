import os
import random
import math
import torch
import numpy as np
from typing import List, Dict, Any, Optional
from PIL import Image
import torchvision.transforms as transforms
from .environment import Environment, ChargingStation, Mineral, MATERIAL_SPECS, MINERAL_TYPES
from zadania.zadanie_4_Astar.astar import astar_find_path, TERRAIN_COSTS, TURN_COST
from zadania.zadanie_3_BFS.bfs import bfs_find_path
from zadania.zadanie_5_DrzewoDecyzyjne.drzewo import predict_with_tree
from .mission import get_active_task
from zadania.zadanie_7_AlgorytmGenetyczny.genetyczny import items_from_minerals, solve_knapsack_ga, solve_knapsack_dp
from . import shop

# Najlżejszy/najmniejszy minerał -- jeśli wolnego miejsca jest mniej, plecak jest "pełny".
# Najlżejszy/minimalny minerał -- jeśli miejsca jest mniej, plecak uznajemy za pełny.
# Самый лёгкий/малый минерал -- если свободного места меньше, рюкзак считаем полным.
MIN_MINERAL_WEIGHT = min(spec["weight"] for spec in MATERIAL_SPECS.values())
MIN_MINERAL_VOLUME = min(spec["volume"] for spec in MATERIAL_SPECS.values())
BASE_CAPACITY = 20.0       # bazowy limit WAGI plecaka (kg)
BASE_VOLUME = 16.0         # bazowy limit OBJĘTOŚCI plecaka (l)
BASE_MAX_BATTERY = 100.0   # bazowa pojemność baterii

# Transformacja obrazu kamery dla wnioskowania (musi być identyczna jak w api.py).
# Transformacja obrazu kamery do wnioskowania musi być taka sama jak w `api.py`.
# Преобразование изображения камеры для инференса musi być identyczne jak w `api.py`.
agent_img_transform = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.ToTensor()
])


class Agent:

    WEATHER_MULTIPLIERS = {
        "Clear_Skies": 1.0, "Partly_Cloudy": 0.8, "Cloudy": 0.5,
        "Foggy": 0.3, "Sand_Dust_Calm": 0.2, "Sand_Dust_Storm": 0.1
    }

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.direction = "N"

        # --- Parametry modyfikowane przez sklep (ulepszenia) ---
        # --- Parametry zmieniane przez sklep (ulepszenia) ---
        # --- Параметры, изменяемые магазинem (улучшения) ---
        self.max_battery: float = BASE_MAX_BATTERY
        self.battery: float = self.max_battery
        self.capacity: float = BASE_CAPACITY        # limit WAGI plecaka (kg)
        self.volume_capacity: float = BASE_VOLUME   # limit OBJĘTOŚCI plecaka (l)
        self.solar_bonus: float = 1.0               # mnożnik ładowania słonecznego
        self.motor_efficiency: float = 1.0          # mnożnik kosztu ruchu (mniej = taniej)
        self.volume_factor: float = 1.0             # mnożnik objętości minerałów (kompresor: mniej=lepiej)
        self.sell_bonus: float = 0.0                # premia do ceny sprzedaży (wiertło)
        self.upgrade_levels: Dict[str, int] = {
            "solar": 0, "compressor": 0, "cargo": 0, "motor": 0, "battery": 0, "drill": 0
        }

        self.inventory: List[str] = []
        self.money: float = 0.0
        self.status: str = "IDLE"
        self.current_plan: List[str] = []
        self.nn_confidence = {"MINING": 0.0, "CHARGE": 0.0}
        self.decision_system = "HEURISTIC"
        self.last_decision = "CONTINUE_MINING"

        # --- Stan związany z problemem plecakowym ---
        # --- Stan związany z problemem plecakowym i wyborem minerałów ---
        # --- Состояние, связанное с задачą рюкзака i wyborem minerałów ---
        self.mining_manifest: List[Mineral] = []    # zestaw minerałów wybrany przez GA
        self.last_knapsack: Optional[Dict[str, Any]] = None
        self.last_purchase: str = ""
        self.charging_mode: bool = False            # histereza ładowania (ładuj do pełna)
        self.current_upgrade_target: Optional[str] = None  # aktualny INTELIGENTNY cel zakupów

    # ---- Aktualna waga / objętość ładunku w plecaku ----
    # ---- Aktualna waga i objętość ładunku w plecaku ----
    # ---- Текущий вес i объём груза в рюкзакu ----
    def current_weight(self) -> float:
        return sum(MATERIAL_SPECS.get(m, {"weight": 1.0})["weight"] for m in self.inventory)

    def current_volume(self) -> float:
        raw = sum(MATERIAL_SPECS.get(m, {"volume": 1.0})["volume"] for m in self.inventory)
        return raw * self.volume_factor

    def turn_left(self):
        dirs = ['N', 'E', 'S', 'W']
        self.direction = dirs[(dirs.index(self.direction) - 1) % 4]
        self.battery -= TURN_COST * self.motor_efficiency
        self.status = "TURNING"

    def turn_right(self):
        dirs = ['N', 'E', 'S', 'W']
        self.direction = dirs[(dirs.index(self.direction) + 1) % 4]
        self.battery -= TURN_COST * self.motor_efficiency
        self.status = "TURNING"

    def move_forward(self, env: Environment):
        offsets = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}
        dx, dy = offsets[self.direction]
        nx, ny = self.x + dx, self.y + dy

        if env.is_within_bounds(nx, ny) and env.get_terrain_type(nx, ny) != 2:
            terrain_type = env.get_terrain_type(nx, ny)
            self.x, self.y = nx, ny
            self.battery -= TERRAIN_COSTS.get(terrain_type, 1.0) * self.motor_efficiency

            if terrain_type == 1:
                self.status = "HEAVY_DRAIN"
            else:
                self.status = "MOVING"

        self._check_death()

    def _get_valid_target_upgrade(self) -> Optional[str]:
        """INTELIGENTNY wybór ulepszenia oparty na analizie bieżących słabości łazika (Expert System).
        Inteligentny wybór ulepszenia na podstawie bieżących słabości łazika.
        Интеллектуальный wybór улучшения na podstawie aktualnych słabości ровера.
        """
        # 1. Jeśli mamy już cel, sprawdzamy czy nadal fizycznie mieści się w plecaku.
        # 1. Jeśli mamy już cel, sprawdzamy, czy nadal fizycznie mieści się w plecaku.
        # 1. Если цель уже jest, sprawdzamy, czy nadal mieści się w рюкzaku.
        if self.current_upgrade_target:
            cost = shop.next_level_cost(self.current_upgrade_target, self)
            if cost is not None:
                req_w = sum(MATERIAL_SPECS.get(m, {"weight": 1.0})["weight"] * q for m, q in cost["materials"].items())
                req_v = sum(MATERIAL_SPECS.get(m, {"volume": 1.0})["volume"] * q * self.volume_factor for m, q in cost["materials"].items())
                if req_w <= self.capacity and req_v <= self.volume_capacity:
                    return self.current_upgrade_target

        # 2. Jeśli nie mamy celu, sprawdzamy na co możemy w ogóle zbierać.
        # 2. Jeśli nie mamy celu, sprawdzamy, co w ogóle zmieści się w plecaku.
        # 2. Если цели nie ma, sprawdzamy, co w ogóle zmieści się w рюкzaku.
        valid_targets = []
        for upgrade_id in shop.UPGRADE_ORDER:
            cost = shop.next_level_cost(upgrade_id, self)
            if cost is not None:
                req_w = sum(MATERIAL_SPECS.get(m, {"weight": 1.0})["weight"] * q for m, q in cost["materials"].items())
                req_v = sum(MATERIAL_SPECS.get(m, {"volume": 1.0})["volume"] * q * self.volume_factor for m, q in cost["materials"].items())
                if req_w <= self.capacity and req_v <= self.volume_capacity:
                    valid_targets.append(upgrade_id)
        
        # 3. Zastosowanie prostego scoringu heurystycznego do wyboru najlepszego ulepszenia.
        # 3. Zastosowanie prostego scoringu heurystycznego do wyboru najlepszego ulepszenia.
        # 3. Использование prostego heurystycznego scoringu для wyboru najlepszego улучшения.
        if valid_targets:
            scores = {}
            for uid in valid_targets:
                score = 0.0
                if uid == "battery":
                    # Im mniejsza bateria, tym bardziej jej potrzebuje (Priorytet najwyższy).
                    # Im mniejsza bateria, tym większy priorytet.
                    # Чем mniejsza bateria, tym wyższy priorytet.
                    score = (100.0 / self.max_battery) * 100.0
                elif uid == "motor":
                    # Im gorsza wydajność silnika, tym wyższy priorytet.
                    # Im słabszy napęd, tym większy priorytet.
                    # Чем gorsza wydajność silnika, tym wyższy priorytet.
                    score = self.motor_efficiency * 90.0
                elif uid == "cargo":
                    # Im mniejszy plecak w stosunku do bazy, tym większa potrzeba.
                    # Im mniejszy plecak, tym pilniejszy zakup.
                    # Чем mniejszy plecak względem bazy, tym większa potrzeba.
                    score = (20.0 / self.capacity) * 85.0
                elif uid == "compressor":
                    # Objętość: kompresor ma wysoki wynik, dopóki factor jest wysoki (1.0).
                    # Kompresor jest ważny, dopóki mnożnik objętości jest wysoki.
                    # Компрессор ważny, пока współczynnik объёmu jest wysoki.
                    score = self.volume_factor * 80.0
                elif uid == "solar":
                    # Panele słoneczne stają się mniej ważne po pierwszym ulepszeniu.
                    # Panele słoneczne z czasem dostają niższy priorytet.
                    # Солнечные панели z czasem dostają niższy priorytet.
                    score = (1.0 / self.solar_bonus) * 75.0
                elif uid == "drill":
                    # Wiertło przydaje się później, żeby szybciej zarabiać.
                    # Wiertło pomaga później zwiększać zysk.
                    # Бур przydaje się później, aby szybciej zarabiać.
                    score = 40.0 + (self.sell_bonus * 20.0)
                
                scores[uid] = score
                
            # Łazik samodzielnie decyduje się na cel z najwyższym wynikiem.
            # Rover sam wybiera cel z najwyższym wynikiem.
            # Ровер sam wybiera цель с najwyższym wynikiem.
            best_upgrade = max(scores, key=scores.get)
            self.current_upgrade_target = best_upgrade
            return self.current_upgrade_target
            
        self.current_upgrade_target = None
        return None

    # =================================================================
    # PROBLEM PLECAKOWY: planowanie zestawu minerałów do zebrania (GA)
    # ЗАДАЧA РЮКЗАКА: planowanie zestawu minerałów do zebrania (GA)
    # =================================================================
    def _plan_mining_manifest(self, env: Environment, method: str = "ga") -> None:
        active = [m for m in env.objects if m.is_active and m.type in MINERAL_TYPES]
        rem_w = self.capacity - self.current_weight()
        rem_v = self.volume_capacity - self.current_volume()

        if not active or rem_w < MIN_MINERAL_WEIGHT or rem_v < MIN_MINERAL_VOLUME * self.volume_factor:
            self.mining_manifest = []
            return

        items = items_from_minerals(active)
        for it in items:
            it.volume *= self.volume_factor

        target = self._get_valid_target_upgrade()
        cost = shop.next_level_cost(target, self) if target else None
        if cost and self.money >= cost["money"]:
            for it in items:
                if it.name in cost["materials"]:
                    it.value += 120.0

        if method == "dp":
            chosen, total_value, total_weight, total_volume = solve_knapsack_dp(items, rem_w, rem_v)
        else:
            chosen, total_value, total_weight, total_volume = solve_knapsack_ga(items, rem_w, rem_v)

        self.mining_manifest = [it.ref for it in chosen if it.ref is not None]
        self.last_knapsack = {
            "method": method.upper(),
            "value": round(total_value, 1),
            "weight": round(total_weight, 1),
            "volume": round(total_volume, 1),
            "count": len(chosen),
        }

    def _plan_to_manifest(self, env: Environment) -> Optional[List[str]]:
        rem_w = self.capacity - self.current_weight()
        rem_v = self.volume_capacity - self.current_volume()
        self.mining_manifest = [
            m for m in self.mining_manifest
            if getattr(m, "is_active", False)
            and getattr(m, "weight", 1.0) <= rem_w
            and getattr(m, "volume", 1.0) * self.volume_factor <= rem_v
        ]
        candidates = sorted(self.mining_manifest, key=lambda m: abs(self.x - m.x) + abs(self.y - m.y))
        for m in candidates:
            path = self._find_path(m.x, m.y, env)
            if path is not None:
                return path
            
            m.is_active = False
            self.mining_manifest.remove(m)
            
        return None

    def _plan_to_charge_or_base(self, env: Environment) -> Optional[List[str]]:
        chargers = [s for s in env.objects if s.is_active and s.type == "ChargingStation"]
        bases = [b for b in env.objects if b.is_active and b.type == "ScienceBase"]
        
        chargers.sort(key=lambda o: abs(self.x - o.x) + abs(self.y - o.y))
        bases.sort(key=lambda o: abs(self.x - o.x) + abs(self.y - o.y))

        rem_w = self.capacity - self.current_weight()
        rem_v = self.volume_capacity - self.current_volume()
        is_full = (rem_w < MIN_MINERAL_WEIGHT) or (rem_v < MIN_MINERAL_VOLUME * self.volume_factor)

        # Priorytet celu zależy od POTRZEBY:
        # Priorytet celu zależy od aktualnej potrzeby.
        # Priorytet zależy od aktualnej potrzeby.
        #  - pełny plecak -> najpierw BAZA (sprzedaż),
        #  - słaba bateria -> najpierw ŁADOWARKA (baza nie ładuje!),
        #  - w innym wypadku -> baza (sprzedaż / sklep).
        #  - pełny plecak -> najpierw BAZA (sprzedaż).
        #  - słaba bateria -> najpierw ŁADOWARKA (baza nie ładuje!).
        #  - w innym wypadku -> baza (sprzedaż / sklep).
        #  - full backpack -> first BASE (sale).
        #  - weak battery -> first CHARGER (base does not charge!).
        #  - otherwise -> base (sale / shop).
        if is_full:
            candidates = bases + chargers
        elif self.battery < 0.55 * self.max_battery:
            candidates = chargers + bases
        else:
            candidates = bases + chargers

        for o in candidates:
            path = self._find_path(o.x, o.y, env)
            if path is not None:
                return path
                
        return None

    def _plan_to_station(self, env: Environment) -> Optional[List[str]]:
        stations = [s for s in env.objects if s.is_active and s.type == "ChargingStation"]
        stations.sort(key=lambda s: abs(self.x - s.x) + abs(self.y - s.y))
        for s in stations:
            path = self._find_path(s.x, s.y, env)
            if path is not None:
                return path
        return None

    def _find_path(self, gx: int, gy: int, env: Environment) -> Optional[List[str]]:
        """Wybór algorytmu wg aktywnego zadania: Zadanie 3 -> BFS, pozostałe -> A*.
        Wybiera algorytm zgodnie z aktywnym zadaniem.
        Выбирает алгоритм zgodnie z aktywnym zadaniem.
        """
        if get_active_task().get("selected_task") == "project-3-uninformed-search":
            return bfs_find_path(self.x, self.y, self.direction, gx, gy, env)
        return astar_find_path(self.x, self.y, self.direction, gx, gy, env)

    def _needs_emergency_charge(self, env: Environment) -> bool:
        stations = [s for s in env.objects if s.is_active and s.type == "ChargingStation"]
        if not stations:
            return False
        dist = min(abs(self.x - s.x) + abs(self.y - s.y) for s in stations)
        energy_to_return = dist * 2.5 * self.motor_efficiency + 15.0
        return self.battery <= energy_to_return

    def follow_plan_or_search(self, env: Environment, trained_nn=None, scaler=None, reverse_mapping=None, tree_clf=None) -> None:
        if self.status == "DEAD":
            return

        if self.charging_mode and self.battery >= 0.8 * self.max_battery:
            self.charging_mode = False
        if self._needs_emergency_charge(env):
            self.charging_mode = True

        # Trasa do stacji liczona tylko w trybie ładowania.
        # Trasa do stacji liczona jest tylko przy ładowaniu.
        # Маршрут до станции liczymy tylko w trybie ładowania.
        station_plan = self._plan_to_station(env) if self.charging_mode else None
        if self.charging_mode and station_plan is None:
            # Brak osiągalnej/aktywnej ładowarki -> nie zamarzaj na polu, wróć do normalnej pracy.
            # Brak dostępnej ładowarki -> wróć do normalnej pracy.
            # Нет доступной зарядки -> wróć do normalnej pracy.
            self.charging_mode = False

        if self.charging_mode:
            self.mining_manifest = []
            self.current_plan = station_plan or []
        elif not self.current_plan:
            if trained_nn is not None and scaler is not None and reverse_mapping is not None:
                decision = self.decide_next_macro_action(env, trained_nn, scaler, reverse_mapping)
            elif tree_clf is not None:
                decision = self.decide_with_tree(env, tree_clf)
            else:
                self.decision_system = "HEURISTIC"
                decision = "CONTINUE_MINING"
            self.last_decision = decision

            rem_w = self.capacity - self.current_weight()
            rem_v = self.volume_capacity - self.current_volume()
            if rem_w < MIN_MINERAL_WEIGHT or rem_v < MIN_MINERAL_VOLUME * self.volume_factor:
                decision = "GO_TO_CHARGE"
                self.mining_manifest = []

            plan = None
            if decision == "CONTINUE_MINING":
                if not self.mining_manifest:
                    self._plan_mining_manifest(env)
                plan = self._plan_to_manifest(env)
                if plan is None and self.inventory:
                    decision = "GO_TO_CHARGE"

            if decision == "GO_TO_CHARGE":
                plan = self._plan_to_charge_or_base(env)

                rem_w = self.capacity - self.current_weight()
                rem_v = self.volume_capacity - self.current_volume()
                if not plan and self.battery > 50.0 and rem_w >= MIN_MINERAL_WEIGHT and rem_v >= (MIN_MINERAL_VOLUME * self.volume_factor):
                    self._plan_mining_manifest(env)
                    plan = self._plan_to_manifest(env)

            if plan:
                self.current_plan = plan
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

    # =================================================================
    # EKONOMIA W BAZIE: sprzedaż nadwyżek + zakup ulepszeń (pieniądze+materiały)
    # ЭКОНОМИКА В БАЗЕ: sprzedaż nadwyżek + zakup ulepszeń (pieniądze+materiały)
    # =================================================================
    def _do_base_economy(self) -> None:
        target = self._get_valid_target_upgrade()
        cost = shop.next_level_cost(target, self) if target else None

        reserve = bool(target and cost and self.money >= cost["money"])
        needed = dict(cost["materials"]) if reserve else {}

        kept_counts: Dict[str, int] = {}
        new_inventory: List[str] = []
        for mat in self.inventory:
            if kept_counts.get(mat, 0) < needed.get(mat, 0):
                kept_counts[mat] = kept_counts.get(mat, 0) + 1
                new_inventory.append(mat)
            else:
                base_val = MATERIAL_SPECS.get(mat, {"value": 10.0})["value"]
                self.money += base_val * (1.0 + self.sell_bonus)
        self.inventory = new_inventory
        self.status = "UNLOADING"

        for _ in range(10 if shop.SHOP_ENABLED else 0):
            tid = self._get_valid_target_upgrade()
            if tid and shop.can_afford(self, tid):
                result = shop.purchase_upgrade(self, tid)
                if not result.get("success"):
                    break
                self.last_purchase = result["message"]
                # Po zakupie resetujemy cel, żeby łazik policzył potrzeby od nowa.
                # После покупки сбрасываем цель, чтобы ровер пересчитал потребности заново.
                self.current_upgrade_target = None
            else:
                break

    def interact_and_recharge(self, env: Environment) -> None:
        if self.status == "DEAD":
            return

        is_charging_at_station = False

        for obj in env.objects:
            if obj.is_active and obj.x == self.x and obj.y == self.y:
                if obj.type == "ScienceBase":
                    if self.inventory or self._get_valid_target_upgrade():
                        self._do_base_economy()

                elif obj.type == "ChargingStation":
                    charge_needed = self.max_battery - self.battery
                    if charge_needed > 0 and obj.energy_pool > 0:
                        charge_amount = min(25.0, obj.energy_pool, charge_needed)
                        self.battery += charge_amount
                        obj.energy_pool -= charge_amount
                        self.status = "CHARGING"
                        is_charging_at_station = True
                        if obj.energy_pool <= 0:
                            obj.is_active = False

                elif obj.type in MINERAL_TYPES:
                    w = getattr(obj, "weight", 1.0)
                    v = getattr(obj, "volume", 1.0) * self.volume_factor
                    if (self.current_weight() + w <= self.capacity
                            and self.current_volume() + v <= self.volume_capacity):
                        self.inventory.append(obj.type)
                        obj.is_active = False

        solar_efficiency = self._calculate_solar_efficiency(env.time_of_day)
        weather_multiplier = self.WEATHER_MULTIPLIERS.get(env.weather, 1.0)
        solar_charge = 1.0 * solar_efficiency * weather_multiplier * self.solar_bonus
        self.battery = min(self.max_battery, self.battery + solar_charge)

        if not is_charging_at_station and self.status not in ["MOVING", "HEAVY_DRAIN", "TURNING", "UNLOADING"]:
            self.status = "IDLE"

    def _get_dist_to_mineral(self, env: Environment) -> float:
        active_minerals = [m for m in env.objects if getattr(m, 'is_active', False) and m.type in MINERAL_TYPES]
        if not active_minerals:
            return 100.0

        effective_distances = []
        for m in active_minerals:
            phys_dist = abs(self.x - m.x) + abs(self.y - m.y)
            price_factor = MATERIAL_SPECS.get(m.type, {"value": 10.0})["value"] / 100.0
            eff_dist = (phys_dist + 1) / price_factor
            effective_distances.append(eff_dist)

        return min(effective_distances)

    def _get_dist_to_station(self, env: Environment) -> float:
        active_stations = [s for s in env.objects if getattr(s, 'is_active', False) and s.type == "ChargingStation"]
        if not active_stations:
            return 100.0
        return min(abs(self.x - s.x) + abs(self.y - s.y) for s in active_stations)

    def terrain_to_pixels(self, terrain_type: int) -> list:
        if terrain_type == 0:
            base = [220, 220, 220, 210, 210, 210, 220, 220, 220]
        elif terrain_type == 1:
            base = [80, 180, 80, 180, 80, 180, 80, 180, 80]
        else:
            base = [50, 50, 50, 50, 10, 50, 50, 50, 50]

        noisy_pixels = []
        for val in base:
            noise = random.randint(-15, 15)
            noisy_val = max(0, min(255, val + noise))
            noisy_pixels.append(noisy_val)

        return noisy_pixels

    def get_camera_image_from_ue5(self, env: Environment) -> torch.Tensor:
        category = "sand"
        obj = next((o for o in env.objects if o.x == self.x and o.y == self.y and o.is_active), None)

        if obj is not None:
            if obj.type == "ChargingStation":
                category = "station"
            elif obj.type == "ScienceBase":
                category = "base"
        else:
            terrain = env.get_terrain_type(self.x, self.y)
            if terrain == 0:
                category = "sand"
            elif terrain == 1:
                category = "rock"
            elif terrain == 2:
                category = "crater"

        folder_path = os.path.join("ue5_photos", category)
        fallback = torch.zeros((1, 3, 32, 32))

        if not os.path.exists(folder_path) or not os.listdir(folder_path):
            return fallback

        files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not files:
            return fallback

        random_file = random.choice(files)
        img_path = os.path.join(folder_path, random_file)

        try:
            img = Image.open(img_path).convert('RGB')
            return agent_img_transform(img).unsqueeze(0)
        except Exception as e:
            print(f"[OSTRZEZENIE] Blad wczytywania kamery w locie: {e}")
            return fallback

    def decide_next_macro_action(self, env: Environment, trained_nn, scaler, reverse_mapping: dict) -> str:
        self.decision_system = "CNN + MLP"
        img_tensor = self.get_camera_image_from_ue5(env)

        battery_pct = (self.battery / self.max_battery * 100.0) if self.max_battery > 0 else 0.0
        w_fill = (self.current_weight() / self.capacity) if self.capacity > 0 else 1.0
        v_fill = (self.current_volume() / self.volume_capacity) if self.volume_capacity > 0 else 1.0
        fill_ratio = max(w_fill, v_fill)
        
        raw_features = np.array([[
            battery_pct,
            env.time_of_day,
            self._calculate_solar_efficiency(env.time_of_day),
            self.WEATHER_MULTIPLIERS.get(env.weather, 1.0),
            self._get_dist_to_mineral(env),
            self._get_dist_to_station(env),
            fill_ratio
        ]])

        scaled_features = scaler.transform(raw_features)
        tab_tensor = torch.tensor(scaled_features, dtype=torch.float32)

        with torch.no_grad():
            outputs = trained_nn(img_tensor, tab_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1).numpy()[0]
            self.nn_confidence["CHARGE"] = float(probabilities[0] * 100)
            self.nn_confidence["MINING"] = float(probabilities[1] * 100)
            class_idx = torch.argmax(outputs, dim=1).item()

        decision = reverse_mapping.get(class_idx, "CONTINUE_MINING")
        return decision

    def decide_with_tree(self, env: Environment, tree_clf) -> str:
        self.decision_system = "DECISION TREE"
        decision, confidence = predict_with_tree(tree_clf, self, env)
        self.nn_confidence = confidence
        return decision

    def _calculate_solar_efficiency(self, time_of_day: int) -> float:
        if 6 <= time_of_day <= 20:
            return math.sin((time_of_day - 6) / 14.0 * math.pi)
        return 0.0

    def _check_death(self) -> None:
        if self.battery <= 0:
            self.battery = 0.0
            self.status = "DEAD"

    def to_dict(self, env=None) -> Dict[str, Any]:
        pixels = [220, 220, 220, 210, 210, 210, 220, 220, 220]
        feed_type = "SAND"

        if env is not None:
            terrain = env.get_terrain_type(self.x, self.y)
            pixels = self.terrain_to_pixels(terrain)

            obj = next((o for o in env.objects if o.x == self.x and o.y == self.y and o.is_active), None)
            if obj is not None:
                if obj.type == "ChargingStation":
                    feed_type = "CHARGER"
                elif obj.type == "ScienceBase":
                    feed_type = "BASE"
                elif obj.type == "Titanium":
                    feed_type = "TITANIUM"
                elif obj.type == "Water Ice":
                    feed_type = "WATER_ICE"
                elif obj.type == "Hematite":
                    feed_type = "HEMATITE"
            else:
                if terrain == 0:
                    feed_type = "SAND"
                elif terrain == 1:
                    feed_type = "ROCK"
                else:
                    feed_type = "CRATER"

        nn_conf = getattr(self, "nn_confidence", {"MINING": 0.0, "CHARGE": 0.0})
        mining_p = nn_conf.get("MINING", 0.0)
        charge_p = nn_conf.get("CHARGE", 0.0)
        nn_thought_str = f"MINING {mining_p:.1f}% | CHARGE {charge_p:.1f}%"

        return {
            "x": self.x,
            "y": self.y,
            "direction": self.direction,
            "battery": round(self.battery, 2),
            "max_battery": round(self.max_battery, 2),
            "inventory": self.inventory,
            "capacity": round(self.capacity, 2),
            "current_weight": round(self.current_weight(), 2),
            "volume_capacity": round(self.volume_capacity, 2),
            "current_volume": round(self.current_volume(), 2),
            "money": round(self.money, 2),
            "upgrade_levels": self.upgrade_levels,
            "nn_thought": nn_thought_str,
            "decision_system": self.decision_system,
            "camera_matrix": pixels,
            "camera_feed_type": feed_type,
            "status": self.status,
            "current_plan": self.current_plan
        }
