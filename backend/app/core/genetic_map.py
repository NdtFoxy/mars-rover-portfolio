import random
import copy
import heapq
from typing import List, Tuple

class MapChromosome:
    """
    Один представитель популяции — хранит в себе карту Марса (сетку grid).
    """
    def __init__(self, width: int = 20, height: int = 15, randomize: bool = True):
        self.width = width
        self.height = height
        self.grid = []
        self.fitness = 0.0
        
        if randomize:
            for _ in range(height):
                row = [random.choices([0, 1, 2], weights=[70, 20, 10], k=1)[0] for _ in range(width)]
                self.grid.append(row)

    def _find_shortest_path_cost(self) -> float:
        """
        Симуляция прохождения пути ровером из верхнего левого угла в правый нижний.
        Возвращает суммарную стоимость пути или -1.0, если прохода нет.
        """
        # Создаем копию сетки и гарантируем, что старт и финиш свободны для симуляции
        temp_grid = [list(row) for row in self.grid]
        temp_grid[0][0] = 0
        temp_grid[self.height - 1][self.width - 1] = 0

        start = (0, 0)
        end = (self.width - 1, self.height - 1)
        
        # Очередь с приоритетами для Дейкстры: (cost, x, y)
        queue = [(0.0, start[0], start[1])]
        visited = set()
        costs = {start: 0.0}
        
        while queue:
            cost, x, y = heapq.heappop(queue)
            
            if (x, y) == end:
                return cost
                
            if (x, y) in visited:
                continue
            visited.add((x, y))
            
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    terrain = temp_grid[ny][nx]
                    if terrain == 2:  # Кратер непроходим
                        continue
                    
                    # Скала (1) преодолевается дольше и дороже, песок (0) — быстрее
                    step_cost = 1.0 if terrain == 0 else 2.0
                    new_cost = cost + step_cost
                    
                    if (nx, ny) not in costs or new_cost < costs[(nx, ny)]:
                        costs[(nx, ny)] = new_cost
                        heapq.heappush(queue, (new_cost, nx, ny))
                        
        return -1.0  # Путь заблокирован

    def evaluate_fitness(self) -> float:
        """
        Динамическая функция приспособленности (Fitness Function).
        Оценивает карту на основе реальной проходимости и сложности лабиринта.
        """
        score = 100.0
        
        # 1. Поиск пути через карту (Дейкстра)
        path_cost = self._find_shortest_path_cost()
        
        if path_cost == -1.0:
            # Пути нет — жесткий штраф. Карта почти гарантированно не выживет.
            return 0.1
            
        # Идеальная целевая сложность пути для карты 20x15 составляет примерно 42-45 единиц энергии
        # (это заставляет карту быть не пустой, но и не перегруженной скалами)
        target_complexity = 44.0
        complexity_error = abs(target_complexity - path_cost)
        
        # Штрафуем за отклонение от целевой сложности пути
        score -= complexity_error * 3.0

        # 2. Оценка пропорций плиток на всей карте
        counts = {0: 0, 1: 0, 2: 0}
        for y in range(self.height):
            for x in range(self.width):
                counts[self.grid[y][x]] += 1
                
        total_cells = self.width * self.height
        sand_ratio = counts[0] / total_cells
        rock_ratio = counts[1] / total_cells
        crater_ratio = counts[2] / total_cells
        
        # Небольшие штрафы за сильные отклонения по общей площади объектов
        score -= abs(0.70 - sand_ratio) * 20
        score -= abs(0.20 - rock_ratio) * 20
        score -= abs(0.10 - crater_ratio) * 40
        
        # 3. Бонус за кластеризацию скал (чтобы они выглядели как гряды гор, а не белый шум)
        for y in range(self.height - 1):
            for x in range(self.width - 1):
                current = self.grid[y][x]
                if current in [1, 2]:
                    if self.grid[y+1][x] == current: score += 0.5
                    if self.grid[y][x+1] == current: score += 0.5

        self.fitness = max(0.1, score)
        return self.fitness

class MapEvolution:
    """
    Класс управления эволюцией карт.
    """
    def __init__(self, width=20, height=15, pop_size=40, mutation_rate=0.04, generations=40):
        self.width = width
        self.height = height
        self.pop_size = pop_size
        self.mutation_rate = mutation_rate
        self.generations = generations
        self.population: List[MapChromosome] = []

    def init_population(self):
        self.population = [MapChromosome(self.width, self.height, randomize=True) for _ in range(self.pop_size)]

    def roulette_wheel_selection(self) -> MapChromosome:
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

    def crossover(self, parent1: MapChromosome, parent2: MapChromosome) -> MapChromosome:
        child = MapChromosome(self.width, self.height, randomize=False)
        split_point = random.randint(1, self.height - 2)
        
        for y in range(self.height):
            if y < split_point:
                child.grid.append(list(parent1.grid[y]))
            else:
                child.grid.append(list(parent2.grid[y]))
                
        return child

    def mutate(self, child: MapChromosome):
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < self.mutation_rate:
                    child.grid[y][x] = random.choices([0, 1, 2], weights=[70, 20, 10], k=1)[0]

    def run(self, verbose: bool = False) -> List[List[int]]:
        self.init_population()
        best_overall = None
        
        for gen in range(self.generations):
            for ind in self.population:
                ind.evaluate_fitness()
                
            self.population.sort(key=lambda x: x.fitness, reverse=True)
            
            if best_overall is None or self.population[0].fitness > best_overall.fitness:
                best_overall = copy.deepcopy(self.population[0])
            
            if verbose and (gen % 10 == 0 or gen == self.generations - 1):
                avg_fit = sum(ind.fitness for ind in self.population) / self.pop_size
                print(f"[GA] Gen {gen} | Best path cost: {self.population[0]._find_shortest_path_cost():.1f} | Best Fit: {self.population[0].fitness:.1f} | Avg: {avg_fit:.1f}")

            new_population = []
            
            # Элитизм (лучшие выживают)
            new_population.append(copy.deepcopy(self.population[0]))
            new_population.append(copy.deepcopy(self.population[1]))
            
            while len(new_population) < self.pop_size:
                parent1 = self.roulette_wheel_selection()
                parent2 = self.roulette_wheel_selection()
                
                child = self.crossover(parent1, parent2)
                self.mutate(child)
                new_population.append(child)
                
            self.population = new_population
            
        return best_overall.grid

def generate_optimal_map(width: int, height: int) -> List[List[int]]:
    # Запускаем эволюцию. Параметры сбалансированы для быстрой работы (около 0.2 - 0.5 секунд на запуск)
    ga = MapEvolution(width=width, height=height, pop_size=40, mutation_rate=0.04, generations=40)
    return ga.run(verbose=True)