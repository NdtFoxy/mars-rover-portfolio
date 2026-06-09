# -*- coding: utf-8 -*-
"""
Zadanie projektowe 7: Algorytmy genetyczne (problem plecakowy).
Uruchom:  python3 uruchom.py
Generuje: zbior/instancja.txt (dane: minerały) i decyzja/ga_vs_dp.txt (wynik GA + weryfikacja DP).
Pełna prezentacja krok po kroku: python3 ../../demo_genetyczny.py
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)
ZBIOR = os.path.join(HERE, "zbior")
DECYZJA = os.path.join(HERE, "decyzja")
os.makedirs(ZBIOR, exist_ok=True)
os.makedirs(DECYZJA, exist_ok=True)

import random
from app.core.environment import MATERIAL_SPECS
from zadania.zadanie_7_AlgorytmGenetyczny.genetyczny import KnapsackItem, compare_knapsack

random.seed(42)
CAP_W, CAP_V = 20.0, 16.0

names = ["Titanium", "Water Ice", "Hematite", "Water Ice", "Titanium",
         "Hematite", "Water Ice", "Titanium", "Hematite", "Water Ice"]
items = [KnapsackItem(n, MATERIAL_SPECS[n]["weight"], MATERIAL_SPECS[n]["volume"],
                      MATERIAL_SPECS[n]["value"]) for n in names]

with open(os.path.join(ZBIOR, "instancja.txt"), "w", encoding="utf-8") as f:
    f.write("DANE WEJSCIOWE (Zadanie 7 - problem plecakowy)\n")
    f.write(f"Limity plecaka: waga <= {CAP_W:g} kg ORAZ objetosc <= {CAP_V:g} l\n\n")
    f.write(f"{'#':>2}  {'Mineral':<11} {'waga':>5} {'objetosc':>9} {'wartosc':>8}\n")
    for i, it in enumerate(items, 1):
        f.write(f"{i:>2}  {it.name:<11} {it.weight:>4g}kg {it.volume:>7g}l {('$'+str(int(it.value))):>8}\n")
    f.write(f"\nSuma wag = {sum(i.weight for i in items):g} kg, suma objetosci = {sum(i.volume for i in items):g} l "
            f"(wiecej niz limity -> trzeba wybierac).\n")

res = compare_knapsack(items, CAP_W, CAP_V)
with open(os.path.join(DECYZJA, "ga_vs_dp.txt"), "w", encoding="utf-8") as f:
    f.write("DECYZJA: wybor minerlow przez algorytm genetyczny (ruletka + krzyzowanie + mutacja)\n\n")
    f.write(f"GA  -> wartosc ${res['ga']['value']:.0f}, waga {res['ga']['weight']:g} kg, "
            f"objetosc {res['ga']['volume']:g} l, przedmioty: {res['ga']['items']}\n")
    f.write(f"DP  -> wartosc ${res['dp']['value']:.0f} (rozwiazanie dokladne, wzorzec optymalnosci)\n\n")
    f.write(f"GA == OPTIMUM: {'TAK' if res['ga_optimal'] else 'NIE (luka %.1f%%)' % res['gap_pct']}\n")

print("=" * 60)
print(" ZADANIE 7 - ALGORYTM GENETYCZNY (problem plecakowy)")
print("=" * 60)
print(f"Dane: {len(items)} mineralow, limity {CAP_W:g}kg / {CAP_V:g}l")
print(f"GA = ${res['ga']['value']:.0f} | DP(optimum) = ${res['dp']['value']:.0f} | "
      f"GA optymalne: {res['ga_optimal']}")
print("Zapisano: zbior/instancja.txt, decyzja/ga_vs_dp.txt")
print("Pelna prezentacja krok po kroku: python3 demo_genetyczny.py")
