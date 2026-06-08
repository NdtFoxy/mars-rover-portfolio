import random
import math
import torch
import numpy as np
from typing import List, Dict, Any, Optional
from .environment import Environment, ChargingStation, Mineral, MATERIAL_SPECS, MINERAL_TYPES
from .search import astar_find_path, TERRAIN_COSTS, TURN_COST
from .knapsack import items_from_minerals, solve_knapsack_ga, solve_knapsack_dp
from . import shop

# Najlżejszy/najmniejszy minerał -- jeśli wolnego miejsca jest mniej, plecak jest "pełny".
MIN_MINERAL_WEIGHT = min(spec["weight"] for spec in MATERIAL_SPECS.values())
MIN_MINERAL_VOLUME = min(spec["volume"] for spec in MATERIAL_SPECS.values())
BASE_CAPACITY = 20.0       # bazowy limit WAGI plecaka (kg)
BASE_VOLUME = 16.0         # bazowy limit OBJĘTOŚCI plecaka (l)
BASE_MAX_BATTERY = 100.0   # bazowa pojemność baterii


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

        # --- Stan związany z problemem plecakowym ---
        self.mining_manifest: List[Mineral] = []    # zestaw minerałów wybrany przez GA
        self.last_knapsack: Optional[Dict[str, Any]] = None
        self.last_purchase: str = ""
        self.charging_mode: bool = False            # histereza ładowania (ładuj do pełna)

    # ---- Aktualna waga / objętość ładunku w plecaku ----
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

    # =================================================================
    # PROBLEM PLECAKOWY: planowanie zestawu minerałów do zebrania (GA)
    # =================================================================
    def _plan_mining_manifest(self, env: Environment, method: str = "ga") -> None:
        """
        Rozwiązuje problem plecakowy: spośród wszystkich aktywnych minerałów
        wybiera podzbiór maksymalizujący wartość, mieszczący się w wolnej
        przestrzeni plecaka. Domyślnie algorytm genetyczny (GA).
        """
        active = [m for m in env.objects if m.is_active and m.type in MINERAL_TYPES]
        rem_w = self.capacity - self.current_weight()
        rem_v = self.volume_capacity - self.current_volume()

        if not active or rem_w < MIN_MINERAL_WEIGHT or rem_v < MIN_MINERAL_VOLUME * self.volume_factor:
            self.mining_manifest = []
            return

        items = items_from_minerals(active)
        # Kompresor zmniejsza efektywną objętość przenoszonych minerałów
        for it in items:
            it.volume *= self.volume_factor

        # POŁĄCZENIE PLECAKA ZE SKLEPEM: jeśli zbieramy na konkretne ulepszenie i
        # stać nas już na jego koszt pieniężny, podbijamy wartość potrzebnych
        # surowców w funkcji celu, aby algorytm genetyczny włożył je do plecaka.
        target = shop.next_target_upgrade(self)
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
        """
        Wyznacza trasę (A*) do najbliższego OSIĄGALNEGO minerału z manifestu,
        który WCIĄŻ MIEŚCI SIĘ w plecaku (waga). Z manifestu usuwane są minerały
        nieaktywne, za ciężkie (po zebraniu innych) oraz nieosiągalne (za
        kraterami) -- dzięki temu łazik nigdy nie blokuje się na celu, którego
        nie da się ani osiągnąć, ani podnieść.
        Zwraca plan ruchów ([] = już na miejscu) lub None, gdy nic nie zostało.
        """
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
            path = astar_find_path(self.x, self.y, self.direction, m.x, m.y, env)
            if path is not None:
                return path
            self.mining_manifest.remove(m)  # nieosiągalny -> wyrzuć z planu
        return None

    def _plan_to_charge_or_base(self, env: Environment) -> Optional[List[str]]:
        """Trasa do stacji ładującej (słaba bateria) lub do bazy (sprzedaż)."""
        if self.battery < 45.0:
            candidates = [s for s in env.objects if s.is_active and s.type == "ChargingStation"]
        else:
            candidates = [b for b in env.objects if b.is_active and b.type == "ScienceBase"]
        candidates.sort(key=lambda o: abs(self.x - o.x) + abs(self.y - o.y))
        for o in candidates:
            path = astar_find_path(self.x, self.y, self.direction, o.x, o.y, env)
            if path is not None:
                return path
        return None

    def _plan_to_station(self, env: Environment) -> Optional[List[str]]:
        """Trasa do najbliższej osiągalnej stacji ładującej."""
        stations = [s for s in env.objects if s.is_active and s.type == "ChargingStation"]
        stations.sort(key=lambda s: abs(self.x - s.x) + abs(self.y - s.y))
        for s in stations:
            path = astar_find_path(self.x, self.y, self.direction, s.x, s.y, env)
            if path is not None:
                return path
        return None

    def _needs_emergency_charge(self, env: Environment) -> bool:
        """
        Twardy limit bezpieczeństwa (niezależny od sieci neuronowej): czy baterii
        wystarczy jeszcze na dojazd do najbliższej stacji? Szacujemy koszt powrotu
        jako ~2.5 energii na pole (skały + obroty) z rezerwą, aby łazik nie padł
        w trasie między minerałami.
        """
        stations = [s for s in env.objects if s.is_active and s.type == "ChargingStation"]
        if not stations:
            return False
        dist = min(abs(self.x - s.x) + abs(self.y - s.y) for s in stations)
        energy_to_return = dist * 2.5 * self.motor_efficiency + 15.0
        return self.battery <= energy_to_return

    def follow_plan_or_search(self, env: Environment, trained_nn=None, scaler=None, reverse_mapping=None) -> None:
        if self.status == "DEAD":
            return

        # Tryb ładowania z histerezą: po wejściu ładujemy aż do ~90% pojemności,
        # aby wyruszać z pełnym bakiem (inaczej łazik kręci się przy stacji).
        if self.charging_mode and self.battery >= 0.9 * self.max_battery:
            self.charging_mode = False
        if self._needs_emergency_charge(env):
            self.charging_mode = True

        if self.charging_mode:
            # PRIORYTET BEZPIECZEŃSTWA: jedź do stacji i ładuj do pełna
            self.mining_manifest = []
            self.current_plan = self._plan_to_station(env) or []
        elif not self.current_plan:
            if trained_nn is not None and scaler is not None and reverse_mapping is not None:
                decision = self.decide_next_macro_action(env, trained_nn, scaler, reverse_mapping)
            else:
                decision = "CONTINUE_MINING"

            # Plecak praktycznie pełny (waga LUB objętość) -> wracamy rozładować/sprzedać
            rem_w = self.capacity - self.current_weight()
            rem_v = self.volume_capacity - self.current_volume()
            if rem_w < MIN_MINERAL_WEIGHT or rem_v < MIN_MINERAL_VOLUME * self.volume_factor:
                decision = "GO_TO_CHARGE"
                self.mining_manifest = []

            plan = None
            if decision == "CONTINUE_MINING":
                # Problem plecakowy: zaplanuj optymalny zestaw, potem zbieraj po kolei
                if not self.mining_manifest:
                    self._plan_mining_manifest(env)
                plan = self._plan_to_manifest(env)
                # Nic osiągalnego się już nie mieści, a mamy ładunek -> jedź sprzedać
                if plan is None and self.inventory:
                    decision = "GO_TO_CHARGE"

            if decision == "GO_TO_CHARGE":
                plan = self._plan_to_charge_or_base(env)

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
    # =================================================================
    def _do_base_economy(self) -> None:
        target = shop.next_target_upgrade(self)
        cost = shop.next_level_cost(target, self) if target else None

        # Materiały rezerwujemy dopiero gdy stać nas już na koszt pieniężny celu
        # (inaczej najpierw uzbierajmy pieniądze, sprzedając wszystko).
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
                self.money += base_val * (1.0 + self.sell_bonus)   # premia wiertła
        self.inventory = new_inventory
        self.status = "UNLOADING"

        # Auto-zakup wszystkich ulepszeń, na które agenta teraz stać
        for _ in range(10):
            tid = shop.next_target_upgrade(self)
            if tid and shop.can_afford(self, tid):
                result = shop.purchase_upgrade(self, tid)
                if not result.get("success"):
                    break
                self.last_purchase = result["message"]
            else:
                break

    def interact_and_recharge(self, env: Environment) -> None:
        if self.status == "DEAD":
            return

        is_charging_at_station = False

        for obj in env.objects:
            if obj.is_active and obj.x == self.x and obj.y == self.y:
                if obj.type == "ScienceBase":
                    if self.inventory or shop.next_target_upgrade(self):
                        self._do_base_economy()

                elif obj.type == "ChargingStation":
                    charge_needed = self.max_battery - self.battery
                    if charge_needed > 0 and obj.energy_pool > 0:
                        charge_amount = min(10.0, obj.energy_pool, charge_needed)
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

    # ---- MAPOWANIE TERENU NA WIZUALNY MATRYCĘ 3x3 Z SZUMEM LOSOWYM ----
    def terrain_to_pixels(self, terrain_type: int) -> list:
        """
        Konwertuje kod terenu na płaską macierz pikseli 3x3 (9 pikseli)
        z dodanym szumem losowym w zakresie ±15. Zapobiega to przeuczeniu (overfitting).
        """
        if terrain_type == 0:   # Piasek (Sand)
            base = [220, 220, 220, 210, 210, 210, 220, 220, 220]
        elif terrain_type == 1: # Skała (Rock)
            base = [80, 180, 80, 180, 80, 180, 80, 180, 80]
        else:                   # Krater (Crater)
            base = [50, 50, 50, 50, 10, 50, 50, 50, 50]

        # Generowanie losowego szumu sensora kamery
        noisy_pixels = []
        for val in base:
            noise = random.randint(-15, 15)
            # Normalizacja do dopuszczalnych granic pikseli [0, 255]
            noisy_val = max(0, min(255, val + noise))
            noisy_pixels.append(noisy_val)

        return noisy_pixels

    def decide_next_macro_action(self, env: Environment, trained_nn, scaler, reverse_mapping: dict) -> str:
        # Sieć decyzyjna używa WYŁĄCZNIE 7 cech telemetrycznych (bez "kamery").
        # Cechy znormalizowane, by były niezależne od ulepszeń sklepowych:
        # bateria jako % pojemności, plecak jako stopień zapełnienia (0..1).
        battery_pct = (self.battery / self.max_battery * 100.0) if self.max_battery > 0 else 0.0
        # Zapełnienie = bardziej wypełniony z dwóch wymiarów (waga / objętość)
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


        scaled_features = scaler.transform(raw_features) # Skalowanie cech (StandardScaler) [1]
        input_tensor = torch.tensor(scaled_features, dtype=torch.float32) # Konwersja na tensor PyTorch [1]

        with torch.no_grad():# Wyłączenie obliczania gradientów (Oszczędność zasobów) [1]
            outputs = trained_nn(input_tensor)# Przejście w przód przez sieć (Forward Pass) [1]

            probabilities = torch.nn.functional.softmax(outputs, dim=1).numpy()[0]# Softmax dla procentów [1]
            self.nn_confidence["CHARGE"] = float(probabilities[0] * 100)
            self.nn_confidence["MINING"] = float(probabilities[1] * 100)

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

    def to_dict(self, env=None) -> Dict[str, Any]:
        # Wartości domyślne (np. na wypadek braku przekazania środowiska)
        pixels = [220, 220, 220, 210, 210, 210, 220, 220, 220] # Domyślny piasek
        feed_type = "SAND"

        if env is not None:
            # Odczytujemy typ podłoża pod łazikiem i generujemy piksele z szumem
            terrain = env.get_terrain_type(self.x, self.y)
            pixels = self.terrain_to_pixels(terrain)

            # Sprawdzamy czy na polu stoi aktywny obiekt
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

        # Pobieranie aktualnych procentów pewności sieci
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
            "camera_matrix": pixels,             # Przekazanie 3x3 matrycy pikseli do JSON [2]
            "camera_feed_type": feed_type,       # Przekazanie typu widoku (np. BASE, ROCK) do JSON [2]
            "status": self.status,
            "current_plan": self.current_plan
        }
