"""
PROBLEM PLECAKOWY (0/1 Knapsack) dla łazika marsjańskiego.

Łazik napotyka zbiór minerałów, każdy o pewnej WADZE (kg) i WARTOŚCI ($).
Plecak ma ograniczoną POJEMNOŚĆ (kg) -- nie zmieści wszystkiego. Trzeba więc
wybrać taki podzbiór minerałów, który maksymalizuje sumaryczną wartość ($)
nie przekraczając pojemności plecaka. To klasyczny problem plecakowy 0/1.

Dwa rozwiązania:
  * solve_knapsack_dp  -- DOKŁADNE, programowanie dynamiczne  O(n * W)
  * solve_knapsack_ga  -- ALGORYTM GENETYCZNY (krzyżowanie + mutacja + ruletka)

Zadanie projektowe "Algorytmy genetyczne" realizuje GA. DP służy jako wzorzec
do walidacji: pozwala udowodnić w raporcie, że GA znajduje wynik optymalny
(albo zbliżony do optymalnego).
"""

import random
import copy
import time
from typing import List, Tuple, Any, Optional


class KnapsackItem:
    """Pojedynczy przedmiot (minerał) kandydujący do włożenia do plecaka."""
    def __init__(self, name: str, weight: float, value: float, ref: Any = None):
        self.name = name
        self.weight = weight
        self.value = value
        self.ref = ref  # opcjonalne odniesienie do obiektu Mineral (współrzędne itd.)

    def __repr__(self) -> str:
        return f"{self.name}(w={self.weight:g}kg, v=${self.value:g})"


def items_from_minerals(minerals: List[Any]) -> List[KnapsackItem]:
    """Konwertuje aktywne obiekty Mineral na listę przedmiotów plecakowych."""
    items = []
    for m in minerals:
        w = getattr(m, "weight", 1.0)
        v = getattr(m, "value", 10.0)
        items.append(KnapsackItem(m.type, w, v, ref=m))
    return items


# =====================================================================
# 1. ROZWIĄZANIE DOKŁADNE -- PROGRAMOWANIE DYNAMICZNE (wzorzec optymalności)
# =====================================================================
def solve_knapsack_dp(items: List[KnapsackItem], capacity: float
                      ) -> Tuple[List[KnapsackItem], float, float]:
    """
    Dokładne rozwiązanie problemu plecakowego 0/1 metodą programowania
    dynamicznego. Zwraca (wybrane_przedmioty, suma_wartości, suma_wag).
    Wagi są zaokrąglane do liczb całkowitych na potrzeby tabeli DP.
    """
    n = len(items)
    W = int(round(capacity))
    if n == 0 or W <= 0:
        return [], 0.0, 0.0

    weights = [max(0, int(round(it.weight))) for it in items]
    values = [it.value for it in items]

    # dp[i][w] = maksymalna wartość przy użyciu pierwszych i przedmiotów i limicie w
    dp = [[0.0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        wi, vi = weights[i - 1], values[i - 1]
        for w in range(W + 1):
            best = dp[i - 1][w]                       # nie bierzemy przedmiotu i
            if wi <= w:
                take = dp[i - 1][w - wi] + vi         # bierzemy przedmiot i
                if take > best:
                    best = take
            dp[i][w] = best

    # Odtworzenie wybranego podzbioru (backtracking po tabeli)
    chosen: List[KnapsackItem] = []
    w = W
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            chosen.append(items[i - 1])
            w -= weights[i - 1]
    chosen.reverse()

    total_value = dp[n][W]
    total_weight = sum(it.weight for it in chosen)
    return chosen, total_value, total_weight


# =====================================================================
# 2. ALGORYTM GENETYCZNY (selekcja ruletkowa + krzyżowanie + mutacja)
#    Struktura analogiczna do genetic_map.py (spójność z resztą projektu).
# =====================================================================
class KnapsackChromosome:
    """
    Osobnik populacji = wektor bitów. genes[i] == 1 oznacza, że i-ty
    przedmiot jest spakowany do plecaka.
    """
    def __init__(self, n: int, randomize: bool = True):
        self.n = n
        if randomize:
            self.genes = [random.randint(0, 1) for _ in range(n)]
        else:
            self.genes = [0] * n
        self.fitness = 0.0


class KnapsackGA:
    """Ewolucja rozwiązań problemu plecakowego."""
    def __init__(self, items: List[KnapsackItem], capacity: float,
                 pop_size: int = 50, mutation_rate: float = 0.05,
                 generations: int = 80):
        self.items = items
        self.n = len(items)
        self.capacity = capacity
        self.pop_size = pop_size
        self.mutation_rate = mutation_rate
        self.generations = generations
        self.population: List[KnapsackChromosome] = []
        # Kara za przekroczenie pojemności (na 1 kg nadwagi). Dobrana tak, by
        # każde rozwiązanie dopuszczalne było lepsze od niedopuszczalnego.
        self.penalty_factor = max((it.value for it in items), default=1.0)

    def init_population(self) -> None:
        self.population = [KnapsackChromosome(self.n, randomize=True)
                           for _ in range(self.pop_size)]

    def evaluate_fitness(self, chromo: KnapsackChromosome) -> float:
        """
        Funkcja przystosowania: suma wartości spakowanych przedmiotów.
        Przekroczenie pojemności plecaka jest karane (rozwiązanie
        niedopuszczalne), ale fitness zawsze > 0, by selekcja ruletkowa
        mogła działać poprawnie.
        """
        total_w = 0.0
        total_v = 0.0
        for gene, item in zip(chromo.genes, self.items):
            if gene:
                total_w += item.weight
                total_v += item.value

        if total_w <= self.capacity:
            chromo.fitness = max(0.1, total_v)
        else:
            overweight = total_w - self.capacity
            chromo.fitness = max(0.1, total_v - self.penalty_factor * overweight)
        return chromo.fitness

    def roulette_wheel_selection(self) -> KnapsackChromosome:
        """Wybór rodzica zgodnie z regułą ruletki (proporcjonalnie do fitness)."""
        total_fitness = sum(ind.fitness for ind in self.population)
        if total_fitness <= 0:
            return random.choice(self.population)

        pick = random.uniform(0, total_fitness)
        current = 0.0
        for individual in self.population:
            current += individual.fitness
            if current >= pick:
                return individual
        return self.population[-1]

    def crossover(self, parent1: KnapsackChromosome,
                  parent2: KnapsackChromosome) -> KnapsackChromosome:
        """Krzyżowanie jednopunktowe wektorów genów."""
        child = KnapsackChromosome(self.n, randomize=False)
        if self.n < 2:
            child.genes = list(parent1.genes)
            return child
        split = random.randint(1, self.n - 1)
        child.genes = parent1.genes[:split] + parent2.genes[split:]
        return child

    def mutate(self, child: KnapsackChromosome) -> None:
        """Mutacja: z prawdopodobieństwem mutation_rate odwracamy bit (0<->1)."""
        for i in range(self.n):
            if random.random() < self.mutation_rate:
                child.genes[i] = 1 - child.genes[i]

    def run(self, verbose: bool = False) -> KnapsackChromosome:
        if self.n == 0:
            return KnapsackChromosome(0, randomize=False)

        self.init_population()
        best_overall: Optional[KnapsackChromosome] = None

        for gen in range(self.generations):
            for ind in self.population:
                self.evaluate_fitness(ind)

            self.population.sort(key=lambda c: c.fitness, reverse=True)

            if best_overall is None or self.population[0].fitness > best_overall.fitness:
                best_overall = copy.deepcopy(self.population[0])

            if verbose and (gen % 20 == 0 or gen == self.generations - 1):
                avg = sum(c.fitness for c in self.population) / self.pop_size
                print(f"[GA-KNAPSACK] Gen {gen:3d} | Best fit: "
                      f"{self.population[0].fitness:7.1f} | Avg: {avg:7.1f}")

            new_population: List[KnapsackChromosome] = []
            # Elityzm -- najlepsze osobniki przechodzą bez zmian
            new_population.append(copy.deepcopy(self.population[0]))
            if self.pop_size > 1:
                new_population.append(copy.deepcopy(self.population[1]))

            while len(new_population) < self.pop_size:
                parent1 = self.roulette_wheel_selection()
                parent2 = self.roulette_wheel_selection()
                child = self.crossover(parent1, parent2)
                self.mutate(child)
                new_population.append(child)

            self.population = new_population

        return best_overall


def solve_knapsack_ga(items: List[KnapsackItem], capacity: float,
                      pop_size: int = 50, mutation_rate: float = 0.05,
                      generations: int = 80, verbose: bool = False
                      ) -> Tuple[List[KnapsackItem], float, float]:
    """
    Rozwiązuje problem plecakowy algorytmem genetycznym.
    Zwraca (wybrane_przedmioty, suma_wartości, suma_wag).
    Jeśli najlepszy osobnik okaże się niedopuszczalny (nadwaga), naprawiamy go
    zachłannie -- usuwamy przedmioty o najniższym stosunku wartość/waga.
    """
    if not items:
        return [], 0.0, 0.0

    ga = KnapsackGA(items, capacity, pop_size, mutation_rate, generations)
    best = ga.run(verbose=verbose)

    chosen = [items[i] for i, g in enumerate(best.genes) if g]

    # Naprawa ewentualnej nadwagi (gwarancja dopuszczalności wyniku)
    total_w = sum(it.weight for it in chosen)
    if total_w > capacity:
        chosen.sort(key=lambda it: it.value / it.weight if it.weight else 1e9)
        while chosen and sum(it.weight for it in chosen) > capacity:
            chosen.pop(0)

    total_value = sum(it.value for it in chosen)
    total_weight = sum(it.weight for it in chosen)
    return chosen, total_value, total_weight


# =====================================================================
# 3. PORÓWNANIE GA vs DP (do raportu / endpointu diagnostycznego)
# =====================================================================
def compare_knapsack(items: List[KnapsackItem], capacity: float,
                     ga_params: Optional[dict] = None) -> dict:
    """Uruchamia oba algorytmy na tej samej instancji i zwraca metryki."""
    ga_params = ga_params or {}

    t0 = time.perf_counter()
    dp_items, dp_value, dp_weight = solve_knapsack_dp(items, capacity)
    dp_time = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    ga_items, ga_value, ga_weight = solve_knapsack_ga(items, capacity, **ga_params)
    ga_time = (time.perf_counter() - t0) * 1000.0

    gap = (dp_value - ga_value)
    gap_pct = (gap / dp_value * 100.0) if dp_value > 0 else 0.0

    return {
        "capacity": capacity,
        "num_items": len(items),
        "dp": {"value": round(dp_value, 2), "weight": round(dp_weight, 2),
               "items": [it.name for it in dp_items], "time_ms": round(dp_time, 3)},
        "ga": {"value": round(ga_value, 2), "weight": round(ga_weight, 2),
               "items": [it.name for it in ga_items], "time_ms": round(ga_time, 3)},
        "gap_value": round(gap, 2),
        "gap_pct": round(gap_pct, 2),
        "ga_optimal": abs(gap) < 1e-6,
    }


def run_knapsack_experiment(num_items: int = 12, capacity: float = 20.0,
                            trials: int = 20) -> None:
    """
    Eksperyment porównawczy: GA vs DP na wielu losowych instancjach problemu
    plecakowego. Liczy, jak często GA trafia w optimum oraz średnią lukę (gap).
    Wyniki zapisywane do 'knapsack_report.txt'.
    """
    from .environment import MATERIAL_SPECS, MINERAL_TYPES

    lines: List[str] = []
    lines.append("=" * 78)
    lines.append("  RAPORT: ALGORYTM GENETYCZNY vs PROGRAMOWANIE DYNAMICZNE")
    lines.append("  Problem plecakowy 0/1 -- pakowanie minerałów do łazika")
    lines.append("=" * 78)
    lines.append(f"\nParametry: {trials} losowych instancji, {num_items} minerałów, "
                 f"pojemność plecaka = {capacity:g} kg")
    lines.append("GA: populacja=50, pokolenia=80, mutacja=0.05, selekcja=ruletka\n")
    lines.append("-" * 78)

    optimal_hits = 0
    total_gap_pct = 0.0
    ga_time_sum = 0.0
    dp_time_sum = 0.0

    for t in range(1, trials + 1):
        items = []
        for _ in range(num_items):
            name = random.choice(MINERAL_TYPES)
            spec = MATERIAL_SPECS[name]
            items.append(KnapsackItem(name, spec["weight"], spec["value"]))

        res = compare_knapsack(items, capacity)
        if res["ga_optimal"]:
            optimal_hits += 1
        total_gap_pct += res["gap_pct"]
        ga_time_sum += res["ga"]["time_ms"]
        dp_time_sum += res["dp"]["time_ms"]

        flag = "OPTIMUM" if res["ga_optimal"] else f"gap {res['gap_pct']:.1f}%"
        lines.append(f"Instancja {t:2d}: DP=${res['dp']['value']:>7.1f}  "
                     f"GA=${res['ga']['value']:>7.1f}  [{flag}]")

    lines.append("-" * 78)
    lines.append("\n[PODSUMOWANIE]")
    lines.append(f"  GA trafił w optimum: {optimal_hits}/{trials} "
                 f"({optimal_hits / trials * 100:.1f}%)")
    lines.append(f"  Średnia luka do optimum (gap): {total_gap_pct / trials:.2f}%")
    lines.append(f"  Średni czas GA: {ga_time_sum / trials:.3f} ms")
    lines.append(f"  Średni czas DP: {dp_time_sum / trials:.3f} ms")
    lines.append("\n[KONIEC RAPORTU]")

    report = "\n".join(lines)
    with open("knapsack_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print(report)


if __name__ == "__main__":
    run_knapsack_experiment()
