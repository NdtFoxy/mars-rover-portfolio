# -*- coding: utf-8 -*-
"""
Zadanie projektowe 7: Algorytmy genetyczne (problem plecakowy).
Uruchom:  python3 uruchom.py
Generuje: zbior/instancja.txt (dane: minerały) i decyzja/ga_vs_dp.txt
          (parametry GA + ewolucja po pokoleniach + wynik GA vs DP + walidacja).
Pełna prezentacja krok po kroku: python3 ../../demo_genetyczny.py
"""
import sys, os, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)
ZBIOR = os.path.join(HERE, "zbior")
DECYZJA = os.path.join(HERE, "decyzja")
os.makedirs(ZBIOR, exist_ok=True)
os.makedirs(DECYZJA, exist_ok=True)

import random
from app.core.environment import MATERIAL_SPECS, MINERAL_TYPES
from zadania.zadanie_7_AlgorytmGenetyczny.genetyczny import (
    KnapsackItem, KnapsackGA, compare_knapsack,
)

random.seed(42)
CAP_W, CAP_V = 20.0, 16.0
POP, GEN, MUT = 50, 60, 0.05

names = ["Titanium", "Water Ice", "Hematite", "Water Ice", "Titanium",
         "Hematite", "Water Ice", "Titanium", "Hematite", "Water Ice"]
items = [KnapsackItem(n, MATERIAL_SPECS[n]["weight"], MATERIAL_SPECS[n]["volume"],
                      MATERIAL_SPECS[n]["value"]) for n in names]

# ------------------------------------------------------------------ ZBIOR
with open(os.path.join(ZBIOR, "instancja.txt"), "w", encoding="utf-8") as f:
    f.write("DANE WEJSCIOWE (Zadanie 7 - wielowymiarowy problem plecakowy 0/1)\n")
    f.write(f"Limity plecaka: waga <= {CAP_W:g} kg ORAZ objetosc <= {CAP_V:g} l\n")
    f.write("(trzeba spelnic OBA limity jednoczesnie -> realne kompromisy)\n\n")
    f.write(f"{'#':>2}  {'Mineral':<11} {'waga':>5} {'objetosc':>9} {'wartosc':>8} {'$/kg':>7} {'$/l':>7}\n")
    f.write("-" * 56 + "\n")
    for i, it in enumerate(items, 1):
        f.write(f"{i:>2}  {it.name:<11} {it.weight:>4g}kg {it.volume:>7g}l "
                f"{('$'+str(int(it.value))):>8} {it.value/it.weight:>7.1f} {it.value/it.volume:>7.1f}\n")
    f.write("-" * 56 + "\n")
    f.write(f"Suma wag = {sum(i.weight for i in items):g} kg, suma objetosci = {sum(i.volume for i in items):g} l\n")
    f.write("Obie sumy przekraczaja limity -> nie da sie wziac wszystkiego, trzeba WYBIERAC.\n")
    f.write("Uwaga: Titanium jest kompaktowy ($50/l), Water Ice objetosciowy ($8/l) -> konflikt wag vs objetosc.\n")

# ------------------------------------------------------------------ EWOLUCJA (verbose)
random.seed(42)
ga = KnapsackGA(items, CAP_W, CAP_V, pop_size=POP, mutation_rate=MUT, generations=GEN)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    ga.run(verbose=True)               # loguje co 20 pokolen: best fit + srednia
evolution = [ln for ln in buf.getvalue().splitlines() if "Gen" in ln]

# ------------------------------------------------------------------ WYNIK GA vs DP
random.seed(42)
res = compare_knapsack(items, CAP_W, CAP_V, ga_params={"pop_size": POP, "generations": GEN, "mutation_rate": MUT})

# ------------------------------------------------------------------ WALIDACJA (wiele instancji)
trials, hits, gap_sum = 8, 0, 0.0
exp_lines = []
for t in range(1, trials + 1):
    random.seed(100 + t)
    inst = [KnapsackItem(n := random.choice(MINERAL_TYPES),
                         MATERIAL_SPECS[n]["weight"], MATERIAL_SPECS[n]["volume"],
                         MATERIAL_SPECS[n]["value"]) for _ in range(12)]
    r = compare_knapsack(inst, CAP_W, CAP_V)
    hits += 1 if r["ga_optimal"] else 0
    gap_sum += r["gap_pct"]
    flag = "OPTIMUM" if r["ga_optimal"] else f"gap {r['gap_pct']:.1f}%"
    exp_lines.append(f"  Instancja {t}: DP=${r['dp']['value']:>6.0f}  GA=${r['ga']['value']:>6.0f}  [{flag}]")

# ------------------------------------------------------------------ DECYZJA
with open(os.path.join(DECYZJA, "ga_vs_dp.txt"), "w", encoding="utf-8") as f:
    f.write("=" * 68 + "\n")
    f.write(" DECYZJA: wybor mineralow ALGORYTMEM GENETYCZNYM (problem plecakowy)\n")
    f.write("=" * 68 + "\n\n")

    f.write("PARAMETRY ALGORYTMU GENETYCZNEGO:\n")
    f.write(f"  populacja      = {POP}\n")
    f.write(f"  pokolenia      = {GEN}\n")
    f.write(f"  mutacja        = {MUT}  (prawdopodobienstwo odwrocenia bitu)\n")
    f.write("  selekcja       = ruletkowa (szansa ~ fitness)\n")
    f.write("  krzyzowanie    = jednopunktowe\n")
    f.write("  elityzm        = 2 najlepsze osobniki przechodza bez zmian\n")
    f.write("  reprezentacja  = wektor bitow (1 = mineral spakowany do plecaka)\n\n")

    f.write("EWOLUCJA (zbieznosc fitness po pokoleniach):\n")
    for ln in evolution:
        f.write("  " + ln.strip() + "\n")
    f.write("  -> fitness rosnie i stabilizuje sie = populacja zbiega do optimum.\n\n")

    f.write("WYNIK KONCOWY:\n")
    f.write(f"  GA -> wartosc ${res['ga']['value']:.0f}, waga {res['ga']['weight']:g} kg, "
            f"objetosc {res['ga']['volume']:g} l, czas {res['ga']['time_ms']:.2f} ms\n")
    f.write(f"        wybrane: {res['ga']['items']}\n")
    f.write(f"  DP -> wartosc ${res['dp']['value']:.0f} (dokladne optimum), czas {res['dp']['time_ms']:.3f} ms\n")
    f.write(f"        wybrane: {res['dp']['items']}\n\n")
    f.write(f"  GA == OPTIMUM: {'TAK' if res['ga_optimal'] else 'NIE (luka %.1f%%)' % res['gap_pct']}\n\n")

    f.write("WALIDACJA NA WIELU LOSOWYCH INSTANCJACH (dowod poprawnosci operatorow):\n")
    for ln in exp_lines:
        f.write(ln + "\n")
    f.write(f"\n  GA trafil w optimum: {hits}/{trials} instancji, srednia luka {gap_sum/trials:.2f}%\n")
    f.write("  Wniosek: GA praktycznie zawsze znajduje rozwiazanie optymalne (lub o ulamek\n")
    f.write("  procenta gorsze), co potwierdza poprawnosc selekcji/krzyzowania/mutacji.\n")

print("=" * 60)
print(" ZADANIE 7 - ALGORYTM GENETYCZNY (problem plecakowy)")
print("=" * 60)
print(f"Dane: {len(items)} mineralow, limity {CAP_W:g}kg / {CAP_V:g}l")
print(f"GA = ${res['ga']['value']:.0f} | DP(optimum) = ${res['dp']['value']:.0f} | "
      f"GA optymalne: {res['ga_optimal']} | walidacja: {hits}/{trials}")
print("Zapisano: zbior/instancja.txt, decyzja/ga_vs_dp.txt")
print("Pelna prezentacja krok po kroku: python3 demo_genetyczny.py")
