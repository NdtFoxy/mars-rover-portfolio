"""
Wielowymiarowy problem plecakowy 0/1.
Многомерная задача рюкзака 0/1.

Łazik napotyka zbiór minerałów, z których każdy ma wagę (kg), objętość (l)
i wartość ($). Plecak ma dwa limity naraz: wagę i objętość. Trzeba wybrać
podzbiór minerałów maksymalizujący wartość i mieszczący się w obu limitach.
Ровер встречает набор минералов, у каждого есть вес (кг), объём (л)
и ценность ($). Рюкзак имеет два ограничения сразу: вес и объём. Нужно выбрать
поднабор минералов с максимальной ценностью и в пределах обоих лимитов.

Dwa rozwiązania:
  * `solve_knapsack_dp` - dokładne programowanie dynamiczne O(n * W * V)
  * `solve_knapsack_ga` - algorytm genetyczny (krzyżowanie, mutacja, ruletka)
Два решения:
  * `solve_knapsack_dp` - точное динамическое программирование O(n * W * V)
  * `solve_knapsack_ga` - генетический алгоритм (скрещивание, мутация, рулетка)

Zadanie z algorytmów genetycznych realizuje GA, a DP służy do walidacji
optymalności i przygotowania raportu porównawczego.
Задание из области генетических алгоритмов реализует GA, а DP служит для проверки
оптимальности и подготовки сравнительного отчёта.
"""

import random
import copy
import time
from typing import List, Tuple, Any, Optional


class KnapsackItem:
    """Przedmiot (minerał) kandydujący do plecaka: waga, objętość, wartość.
    Предмет (минерал)-кандидат в рюкзак: вес, объём, ценность.
    """
    def __init__(self, name: str, weight: float, volume: float, value: float, ref: Any = None):
        self.name = name
        self.weight = weight
        self.volume = volume
        self.value = value
        self.ref = ref  # opcjonalne odniesienie do obiektu Mineral (współrzędne itd.)

    def __repr__(self) -> str:
        return f"{self.name}(w={self.weight:g}kg, v={self.volume:g}l, ${self.value:g})"


def items_from_minerals(minerals: List[Any]) -> List[KnapsackItem]:
    """Konwertuje aktywne obiekty Mineral na listę przedmiotów plecakowych.
    Преобразует активные объекты Mineral в список предметов для рюкзака.
    """
    items = []
    for m in minerals:
        w = getattr(m, "weight", 1.0)
        vol = getattr(m, "volume", 1.0)
        val = getattr(m, "value", 10.0)
        items.append(KnapsackItem(m.type, w, vol, val, ref=m))
    return items


# =====================================================================
# 1. ROZWIĄZANIE DOKŁADNE -- PROGRAMOWANIE DYNAMICZNE 2D (wzorzec optymalności)
# 1. ТОЧНОЕ РЕШЕНИЕ -- ДВУМЕРНОЕ ДИНАМИЧЕСКОЕ ПРОГРАММИРОВАНИЕ (эталон оптимальности)
# =====================================================================
def solve_knapsack_dp(items: List[KnapsackItem], cap_w: float, cap_v: float
                      ) -> Tuple[List[KnapsackItem], float, float, float]:
    """
    Dokładne rozwiązanie wielowymiarowego problemu plecakowego 0/1 metodą
    programowania dynamicznego po DWÓCH wymiarach (waga i objętość).
    Zwraca (wybrane_przedmioty, suma_wartości, suma_wag, suma_objętości).
    Точное решение многомерной задачи рюкзака 0/1 методом динамического
    программирования по ДВУМ измерениям (вес и объём).
    Возвращает (wybrane_przedmioty, suma_wartości, suma_wag, suma_objętości).
    """
    n = len(items)
    W = int(round(cap_w))
    V = int(round(cap_v))
    if n == 0 or W <= 0 or V <= 0:
        return [], 0.0, 0.0, 0.0

    weights = [max(0, int(round(it.weight))) for it in items]
    vols = [max(0, int(round(it.volume))) for it in items]
    values = [it.value for it in items]

    # dp[i][w][v] = maksymalna wartość przy pierwszych i przedmiotach,
    #               limicie wagi w oraz limicie objętości v
    # dp[i][w][v] = максимальная ценность для первых i предметов,
    #               при лимите веса w и лимите объёма v
    dp = [[[0.0] * (V + 1) for _ in range(W + 1)] for _ in range(n + 1)]
    for i in range(1, n + 1):
        wi, vi, val = weights[i - 1], vols[i - 1], values[i - 1]
        prev, cur = dp[i - 1], dp[i]
        for w in range(W + 1):
            for v in range(V + 1):
                best = prev[w][v]                       # nie bierzemy przedmiotu i
                # Nie bierzemy tego przedmiotu.
                # Этот предмет не берем.
                if wi <= w and vi <= v:
                    take = prev[w - wi][v - vi] + val   # bierzemy przedmiot i
                    # Bierzemy ten przedmiot.
                    # Берем этот предмет.
                    if take > best:
                        best = take
                cur[w][v] = best

    # Odtworzenie wybranego podzbioru (backtracking)
    # Восстановление выбранного подмножества (backtracking)
    chosen: List[KnapsackItem] = []
    w, v = W, V
    for i in range(n, 0, -1):
        if dp[i][w][v] != dp[i - 1][w][v]:
            chosen.append(items[i - 1])
            w -= weights[i - 1]
            v -= vols[i - 1]
    chosen.reverse()

    total_value = dp[n][W][V]
    total_weight = sum(it.weight for it in chosen)
    total_volume = sum(it.volume for it in chosen)
    return chosen, total_value, total_weight, total_volume


# =====================================================================
# 2. ALGORYTM GENETYCZNY (selekcja ruletkowa + krzyżowanie + mutacja)
# 2. ГЕНЕТИЧЕСКИЙ АЛГОРИТМ (рулеточный отбор + скрещивание + мутация)
# =====================================================================
class KnapsackChromosome:
    """Osobnik = wektor bitów. genes[i] == 1 => i-ty przedmiot jest w plecaku.
    Особь = вектор битов. genes[i] == 1 => i-й предмет лежит в рюкзаке.
    """
    def __init__(self, n: int, randomize: bool = True):
        self.n = n
        if randomize:
            self.genes = [random.randint(0, 1) for _ in range(n)]
        else:
            self.genes = [0] * n
        self.fitness = 0.0


class KnapsackGA:
    """Ewolucja rozwiązań wielowymiarowego problemu plecakowego.
    Эволюция решений многомерной задачи рюкзака.
    """
    def __init__(self, items: List[KnapsackItem], cap_w: float, cap_v: float,
                 pop_size: int = 50, mutation_rate: float = 0.05,
                 generations: int = 80):
        self.items = items
        self.n = len(items)
        self.cap_w = cap_w
        self.cap_v = cap_v
        self.pop_size = pop_size
        self.mutation_rate = mutation_rate
        self.generations = generations
        self.population: List[KnapsackChromosome] = []
        # Kara za przekroczenie KTÓREGOKOLWIEK limitu (na jednostkę nadmiaru).
        # Штраф за превышение ЛЮБОГО лимита (за единицу превышения).
        self.penalty_factor = max((it.value for it in items), default=1.0)

    def init_population(self) -> None:
        self.population = [KnapsackChromosome(self.n, randomize=True)
                           for _ in range(self.pop_size)]

    def evaluate_fitness(self, chromo: KnapsackChromosome) -> float:
        """
        Funkcja przystosowania: suma wartości. Przekroczenie limitu wagi LUB
        objętości jest karane (rozwiązanie niedopuszczalne), ale fitness > 0,
        aby selekcja ruletkowa działała.
        Функция приспособленности: сумма ценности. Превышение лимита веса ИЛИ
        объёма штрафуется (решение недопустимо), но fitness > 0,
        чтобы работал рулеточный отбор.
        """
        total_w = total_v = total_val = 0.0
        for gene, item in zip(chromo.genes, self.items):
            if gene:
                total_w += item.weight
                total_v += item.volume
                total_val += item.value

        if total_w <= self.cap_w and total_v <= self.cap_v:
            chromo.fitness = max(0.1, total_val)
        else:
            overflow = max(0.0, total_w - self.cap_w) + max(0.0, total_v - self.cap_v)
            chromo.fitness = max(0.1, total_val - self.penalty_factor * overflow)
        return chromo.fitness

    def roulette_wheel_selection(self) -> KnapsackChromosome:
        """Wybór rodzica zgodnie z regułą ruletki (proporcjonalnie do fitness).
        Выбор родителя по правилу рулетки (пропорционально fitness).
        """
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
        """Krzyżowanie jednopunktowe wektorów genów.
        Одноточечное скрещивание векторов генов.
        """
        child = KnapsackChromosome(self.n, randomize=False)
        if self.n < 2:
            child.genes = list(parent1.genes)
            return child
        split = random.randint(1, self.n - 1)
        child.genes = parent1.genes[:split] + parent2.genes[split:]
        return child

    def mutate(self, child: KnapsackChromosome) -> None:
        """Mutacja: z prawdopodobieństwem mutation_rate odwracamy bit (0<->1).
        Мутация: с вероятностью mutation_rate инвертируем бит (0<->1).
        """
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
            # Элитизм -- лучшие особи переходят без изменений
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


def solve_knapsack_ga(items: List[KnapsackItem], cap_w: float, cap_v: float,
                      pop_size: int = 50, mutation_rate: float = 0.05,
                      generations: int = 80, verbose: bool = False
                      ) -> Tuple[List[KnapsackItem], float, float, float]:
    """
    Rozwiązuje wielowymiarowy problem plecakowy algorytmem genetycznym.
    Решает многомерную задачу рюкзака генетическим алгоритмом.

    Zwraca (wybrane_przedmioty, suma_wartości, suma_wag, suma_objętości).
    Возвращает (wybrane_przedmioty, suma_wartości, suma_wag, suma_objętości).

    Ewentualna nadwaga/nadobjętość jest naprawiana zachłannie -- usuwamy
    przedmioty o najgorszym stosunku wartość/(waga+objętość).
    Лишний вес/объём исправляется жадно -- удаляем предметы с худшим
    stosunku wartość/(waga+objętość).
    """
    if not items:
        return [], 0.0, 0.0, 0.0

    ga = KnapsackGA(items, cap_w, cap_v, pop_size, mutation_rate, generations)
    best = ga.run(verbose=verbose)

    chosen = [items[i] for i, g in enumerate(best.genes) if g]

    # Naprawa: usuwaj najmniej opłacalne, aż zmieścimy się w OBU limitach
    # Исправление: удаляем наименее выгодные, пока не уложимся в ОБА лимита
    def over(sel):
        return sum(it.weight for it in sel) > cap_w or sum(it.volume for it in sel) > cap_v
    if over(chosen):
        chosen.sort(key=lambda it: it.value / (it.weight + it.volume + 1e-9))
        while chosen and over(chosen):
            chosen.pop(0)

    total_value = sum(it.value for it in chosen)
    total_weight = sum(it.weight for it in chosen)
    total_volume = sum(it.volume for it in chosen)
    return chosen, total_value, total_weight, total_volume


# =====================================================================
# 3. PORÓWNANIE GA vs DP (do raportu / endpointu diagnostycznego)
# 3. СРАВНЕНИЕ GA vs DP (для отчёта / диагностического endpoint)
# =====================================================================
def compare_knapsack(items: List[KnapsackItem], cap_w: float, cap_v: float,
                     ga_params: Optional[dict] = None) -> dict:
    """Uruchamia oba algorytmy na tej samej instancji i zwraca metryki.
    Запускает оба алгоритма на одной и той же задаче и возвращает метрики.
    """
    ga_params = ga_params or {}

    t0 = time.perf_counter()
    dp_items, dp_value, dp_w, dp_v = solve_knapsack_dp(items, cap_w, cap_v)
    dp_time = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    ga_items, ga_value, ga_w, ga_v = solve_knapsack_ga(items, cap_w, cap_v, **ga_params)
    ga_time = (time.perf_counter() - t0) * 1000.0

    gap = dp_value - ga_value
    gap_pct = (gap / dp_value * 100.0) if dp_value > 0 else 0.0

    return {
        "cap_weight": cap_w,
        "cap_volume": cap_v,
        "num_items": len(items),
        "dp": {"value": round(dp_value, 2), "weight": round(dp_w, 2), "volume": round(dp_v, 2),
               "items": [it.name for it in dp_items], "time_ms": round(dp_time, 3)},
        "ga": {"value": round(ga_value, 2), "weight": round(ga_w, 2), "volume": round(ga_v, 2),
               "items": [it.name for it in ga_items], "time_ms": round(ga_time, 3)},
        "gap_value": round(gap, 2),
        "gap_pct": round(gap_pct, 2),
        "ga_optimal": abs(gap) < 1e-6,
    }


def run_knapsack_experiment(num_items: int = 12, cap_w: float = 20.0,
                            cap_v: float = 16.0, trials: int = 20) -> None:
    """
    Eksperyment porównawczy GA vs DP na wielu losowych instancjach
    wielowymiarowego problemu plecakowego. Wyniki -> 'knapsack_report.txt'.
    Сравнительный эксперимент GA vs DP на многих случайных экземплярах
    многомерной задачи рюкзака. Результаты -> 'knapsack_report.txt'.
    """
    from app.core.environment import MATERIAL_SPECS, MINERAL_TYPES

    lines: List[str] = []
    lines.append("=" * 78)
    lines.append("  RAPORT: ALGORYTM GENETYCZNY vs PROGRAMOWANIE DYNAMICZNE")
    lines.append("  Wielowymiarowy problem plecakowy 0/1 (waga + objętość)")
    lines.append("=" * 78)
    lines.append(f"\nParametry: {trials} losowych instancji, {num_items} minerałów, "
                 f"limity plecaka = {cap_w:g} kg ORAZ {cap_v:g} l")
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
            items.append(KnapsackItem(name, spec["weight"], spec["volume"], spec["value"]))

        res = compare_knapsack(items, cap_w, cap_v)
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
