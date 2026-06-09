# -*- coding: utf-8 -*-
"""
=====================================================================
 SKRYPT PREZENTACYJNY DLA PROWADZĄCEGO
 Zadanie projektowe: ALGORYTMY GENETYCZNE
 Wielowymiarowy problem plecakowy (waga + objętość)
=====================================================================

Pokazuje krok po kroku:
  CZĘŚĆ 1 — ZBIÓR DANYCH (minerały: waga, objętość, wartość; 2 limity plecaka)
  CZĘŚĆ 2 — ALGORYTM GENETYCZNY: selekcja RULETKOWA, KRZYŻOWANIE, MUTACJA
  CZĘŚĆ 3 — DECYZJA GA (co spakować) + weryfikacja optymalności (GA vs DP)
  CZĘŚĆ 4 — ZBIÓR UCZĄCY sieci neuronowej + jakie DECYZJE podejmuje

Uruchomienie (z katalogu backend/):
    python3 demo_genetyczny.py
"""

import random
from app.core.environment import MATERIAL_SPECS
from zadania.zadanie_7_AlgorytmGenetyczny.genetyczny import (
    KnapsackItem, KnapsackGA, solve_knapsack_dp,
)

LINE = "=" * 70
random.seed(42)  # powtarzalność prezentacji


def chromo_summary(genes, items):
    """Opis osobnika: spakowane przedmioty, waga, objętość, wartość."""
    packed = [items[i].name for i, g in enumerate(genes) if g]
    weight = sum(items[i].weight for i, g in enumerate(genes) if g)
    volume = sum(items[i].volume for i, g in enumerate(genes) if g)
    value = sum(items[i].value for i, g in enumerate(genes) if g)
    return packed, weight, volume, value


def bits(genes):
    return "[" + " ".join(str(g) for g in genes) + "]"


# =====================================================================
def part1_dataset(items, cap_w, cap_v):
    print(LINE)
    print(" CZĘŚĆ 1.  ZBIÓR DANYCH  —  wielowymiarowy problem plecakowy")
    print(LINE)
    print(f" Limity plecaka łazika:  WAGA <= {cap_w:g} kg   ORAZ   OBJĘTOŚĆ <= {cap_v:g} l\n")
    print(f" {'#':>2}  {'Minerał':<11} {'Waga':>6} {'Objęt.':>7} {'Wartość':>9}")
    print(" " + "-" * 42)
    total_w = total_v = 0.0
    for i, it in enumerate(items, 1):
        total_w += it.weight
        total_v += it.volume
        print(f" {i:>2}  {it.name:<11} {it.weight:>4g}kg {it.volume:>5g}l "
              f"{('$'+str(int(it.value))):>9}")
    print(" " + "-" * 42)
    print(f" Suma wszystkich: {total_w:g} kg  oraz  {total_v:g} l")
    print(f" >> {total_w:g} kg > {cap_w:g} kg  I  {total_v:g} l > {cap_v:g} l")
    print("    Nie zmieści się wszystko ani wagowo, ani objętościowo!")
    print("    Trzeba wybrać NAJLEPSZY podzbiór mieszczący się w OBU limitach.\n")


# =====================================================================
def part2_operators(items, cap_w, cap_v):
    print(LINE)
    print(" CZĘŚĆ 2.  ALGORYTM GENETYCZNY  —  operatory ewolucyjne")
    print(LINE)
    print(" Reprezentacja: osobnik = wektor bitów; gen 1 = minerał w plecaku.\n")

    ga = KnapsackGA(items, cap_w, cap_v, pop_size=6, mutation_rate=0.2, generations=40)
    ga.init_population()
    for ind in ga.population:
        ga.evaluate_fitness(ind)

    # --- Populacja początkowa ---
    print(" Populacja początkowa (losowa) i jej przystosowanie (fitness):")
    for k, ind in enumerate(ga.population, 1):
        _, w, v, val = chromo_summary(ind.genes, items)
        flag = "  (nie mieści się!)" if (w > cap_w or v > cap_v) else ""
        print(f"   Osobnik {k}: {bits(ind.genes)}  {w:>4g}kg/{v:>4g}l  ${int(val):<4} "
              f"fit={ind.fitness:>6.1f}{flag}")

    # --- SELEKCJA RULETKOWA ---
    print("\n [A] SELEKCJA RULETKOWA (reguła ruletki)")
    total_fit = sum(i.fitness for i in ga.population)
    print("     Prawdopodobieństwo wyboru rodzica ∝ jego fitness:")
    for k, ind in enumerate(ga.population, 1):
        p = ind.fitness / total_fit * 100 if total_fit else 0
        bar = "█" * int(p / 3)
        print(f"       Osobnik {k}: {p:>5.1f}%  {bar}")
    p1 = ga.roulette_wheel_selection()
    p2 = ga.roulette_wheel_selection()
    # Dla czytelności krzyżowania chcemy DWÓCH RÓŻNYCH rodziców
    tries = 0
    while p2.genes == p1.genes and tries < 30:
        p2 = ga.roulette_wheel_selection()
        tries += 1
    if p2.genes == p1.genes:
        others = [i for i in ga.population if i.genes != p1.genes]
        if others:
            p2 = random.choice(others)
    print(f"     Wylosowano rodziców: {bits(p1.genes)}  oraz  {bits(p2.genes)}")

    # --- KRZYŻOWANIE ---
    print("\n [B] KRZYŻOWANIE jednopunktowe (krzyżowanie)")
    n = len(items)
    split = random.randint(1, n - 1)
    # Punkt cięcia dający dziecko RÓŻNE od obojga rodziców (czytelność prezentacji)
    for s in range(1, n):
        cand = p1.genes[:s] + p2.genes[s:]
        if cand != p1.genes and cand != p2.genes:
            split = s
            break
    child_genes = p1.genes[:split] + p2.genes[split:]
    print(f"     Rodzic 1:  {bits(p1.genes)}")
    print(f"     Rodzic 2:  {bits(p2.genes)}")
    print(f"     Punkt cięcia po pozycji {split} ─┐")
    print(f"     Dziecko :  {bits(child_genes)}   (geny 1..{split} od R1, reszta od R2)")

    # --- MUTACJA ---
    print("\n [C] MUTACJA (mutacja — odwracanie bitów)")
    before = list(child_genes)
    after = list(child_genes)
    for i in range(n):
        if random.random() < 0.25:
            after[i] = 1 - after[i]
    if before == after:           # gwarantujemy widoczną mutację w prezentacji
        j = random.randrange(n)
        after[j] = 1 - after[j]
    changed = [i + 1 for i in range(n) if before[i] != after[i]]
    print(f"     Przed mutacją: {bits(before)}")
    print(f"     Po mutacji   : {bits(after)}")
    print(f"     Odwrócone geny na pozycjach: {changed if changed else 'brak (los)'}\n")


# =====================================================================
def part3_decision(items, cap_w, cap_v):
    print(LINE)
    print(" CZĘŚĆ 3.  DECYZJA ALGORYTMU + weryfikacja (GA vs DP)")
    print(LINE)

    ga = KnapsackGA(items, cap_w, cap_v, pop_size=50, mutation_rate=0.05, generations=80)
    best = None
    print(" Ewolucja (najlepszy fitness w kolejnych pokoleniach):")
    ga.init_population()
    import copy
    for gen in range(ga.generations):
        for ind in ga.population:
            ga.evaluate_fitness(ind)
        ga.population.sort(key=lambda c: c.fitness, reverse=True)
        if best is None or ga.population[0].fitness > best.fitness:
            best = copy.deepcopy(ga.population[0])
        if gen % 20 == 0 or gen == ga.generations - 1:
            avg = sum(c.fitness for c in ga.population) / ga.pop_size
            print(f"     Pokolenie {gen:>3}: best=${best.fitness:>6.0f}   avg=${avg:>6.0f}")
        # nowe pokolenie (elityzm + ruletka + krzyżowanie + mutacja)
        newp = [copy.deepcopy(ga.population[0]), copy.deepcopy(ga.population[1])]
        while len(newp) < ga.pop_size:
            c = ga.crossover(ga.roulette_wheel_selection(), ga.roulette_wheel_selection())
            ga.mutate(c)
            newp.append(c)
        ga.population = newp

    packed, w, v, val = chromo_summary(best.genes, items)
    print(f"\n >> DECYZJA GA: spakować {packed}")
    print(f"    Łącznie: wartość = ${int(val)},  waga = {w:g}/{cap_w:g} kg,  objętość = {v:g}/{cap_v:g} l\n")

    dp_items, dp_val, dp_w, dp_v = solve_knapsack_dp(items, cap_w, cap_v)
    print(" Weryfikacja rozwiązaniem DOKŁADNYM (programowanie dynamiczne 2D):")
    print(f"    DP (optimum): wartość = ${int(dp_val)},  przedmioty = {[it.name for it in dp_items]}")
    print(f"    GA          : wartość = ${int(val)}")
    if abs(dp_val - val) < 1e-6:
        print("    WYNIK: ✔ GA znalazł rozwiązanie OPTYMALNE.\n")
    else:
        print(f"    WYNIK: GA o ${int(dp_val - val)} od optimum (luka {(dp_val-val)/dp_val*100:.1f}%).\n")


# =====================================================================
def part4_training_set():
    print(LINE)
    print(" CZĘŚĆ 4.  ZBIÓR UCZĄCY sieci neuronowej  +  jej DECYZJE")
    print(LINE)
    try:
        from zadania.zadanie_5_DrzewoDecyzyjne.drzewo import generate_dataset
    except Exception as e:
        print(f" (pominięto — brak zależności ML: {e})")
        return

    df = generate_dataset(400)
    cols = ["battery_level", "weather_multiplier", "dist_to_station",
            "inventory_fill_ratio", "target_decision"]
    print(" Cechy wejściowe (atrybuty), na podstawie których podejmowana jest DECYZJA:")
    print("   battery_level, time_of_day, solar_efficiency, weather_multiplier,")
    print("   terrain_type, dist_to_mineral, dist_to_station, inventory_fill_ratio\n")
    print(" Próbka zbioru uczącego (wybrane kolumny):")
    sample = df[cols].head(8).to_string(index=False,
             formatters={"battery_level": lambda x: f"{x:.1f}",
                         "weather_multiplier": lambda x: f"{x:.1f}",
                         "inventory_fill_ratio": lambda x: f"{x:.2f}"})
    for ln in sample.split("\n"):
        print("   " + ln)

    counts = df["target_decision"].value_counts().to_dict()
    print(f"\n Możliwe DECYZJE (klasy wyjściowe) i ich liczność w zbiorze:")
    for k, v in counts.items():
        print(f"     {k:<18} : {v} próbek")
    print("\n Pełny raport decyzji wytrenowanej sieci na scenariuszach testowych")
    print(" generuje się przy starcie serwera do pliku 'nn_model_report.txt'.\n")


# =====================================================================
def main():
    # Stała, czytelna instancja problemu do prezentacji (waga + objętość)
    cap_w = 20.0
    cap_v = 16.0
    demo_names = ["Titanium", "Water Ice", "Hematite", "Water Ice",
                  "Titanium", "Hematite", "Water Ice", "Titanium"]
    items = [KnapsackItem(n, MATERIAL_SPECS[n]["weight"], MATERIAL_SPECS[n]["volume"],
                          MATERIAL_SPECS[n]["value"])
             for n in demo_names]

    print("\n" + LINE)
    print(" PREZENTACJA: ALGORYTM GENETYCZNY DLA PROBLEMU PLECAKOWEGO")
    print(" Projekt: Autonomiczny Łazik Marsjański")
    print(LINE + "\n")

    part1_dataset(items, cap_w, cap_v)
    part2_operators(items, cap_w, cap_v)
    part3_decision(items, cap_w, cap_v)
    part4_training_set()

    print(LINE)
    print(" KONIEC PREZENTACJI")
    print(LINE)


if __name__ == "__main__":
    main()
